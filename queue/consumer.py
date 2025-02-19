import pika
import json
import os
import time
import random
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from datetime import date
from typing import Optional
import starkbank
import re
import threading

load_dotenv()


class Person(BaseModel):
    name: str = Field(min_length=1)
    cpf: str

    @field_validator("cpf")
    def validate_cpf(cls, v: str) -> str:
        numbers = "".join(filter(str.isdigit, v))

        if len(numbers) != 11:
            raise ValueError("CPF must have 11 digits")

        if len(set(numbers)) == 1:
            raise ValueError("Invalid CPF")

        sum_of_products = sum(
            int(a) * b for a, b in zip(numbers[0:9], range(10, 1, -1))
        )
        expected_digit = (sum_of_products * 10 % 11) % 10
        if int(numbers[9]) != expected_digit:
            raise ValueError("Invalid CPF")

        sum_of_products = sum(
            int(a) * b for a, b in zip(numbers[0:10], range(11, 1, -1))
        )
        expected_digit = (sum_of_products * 10 % 11) % 10
        if int(numbers[10]) != expected_digit:
            raise ValueError("Invalid CPF")

        return v


class Invoice(BaseModel):
    amount: int = Field(gt=0, lt=10000000000)
    person: Person
    due_date: Optional[date] = None


class AccountType(str, Enum):
    CHECKING = "checking"
    PAYMENT = "payment"
    SALARY = "salary"
    SAVINGS = "savings"


class Account(BaseModel):
    bank_code: str
    branch: str
    account: str
    name: str = Field(min_length=1)
    tax_id: str
    account_type: AccountType

    @field_validator("account", mode="before")
    def account_checker(cls, value: str) -> str:
        if not re.match(r"^\d{1,20}$|^\d{1,19}-\d{1,20}$", value):
            raise ValueError(
                "Invalid account number. Should be 1 to 20 digits or 1 to 19 digits with an hyphen and more 1 digit."
            )
        return value


class Transfer(BaseModel):
    account: Account
    amount: int = Field(gt=0, lt=10000000000)


class InvalidRequestType(Exception):
    def __init__(self, request_type: str):
        super().__init__(f"Invalid request type: {request_type}")


class InvalidRequestData(Exception):
    def __init__(self, data):
        super().__init__(f"Invalid request data: {data}")


###############################################################


def get_private_key():
    return f"""-----BEGIN EC PARAMETERS-----
{os.getenv("STARKBANK_EC_PARAMETERS")}
-----END EC PARAMETERS-----
-----BEGIN EC PRIVATE KEY-----
{os.getenv("STARKBANK_EC_PRIVATE_KEY")}
-----END EC PRIVATE KEY-----"""


def send_invoice(invoice: Invoice):
    starkbank.user = starkbank.Project(
        environment="sandbox",
        id="5340871184613376",
        private_key=get_private_key(),
    )

    starkbank_invoice = starkbank.Invoice(
        amount=invoice.amount,
        due=invoice.due_date,
        name=invoice.person.name,
        tax_id=invoice.person.cpf,
    )

    starkbank.invoice.create([starkbank_invoice])


###############################################################


class QueueWithRetry:
    def __init__(self, queue_name: str):
        self.queue_name = queue_name
        self.wait_queue_name = f"{queue_name}_wait"
        self.connection = None
        self.channel = None

        self.rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        self.rabbitmq_port = int(os.getenv("RABBITMQ_PORT", "5672"))
        self.rabbitmq_user = os.getenv("RABBITMQ_USER", "guest")
        self.rabbitmq_pass = os.getenv("RABBITMQ_PASS", "guest")

    def callback(self, ch, method, properties, body):
        try:
            message = json.loads(body)
            request_type = str(message.get("type"))

            # test type
            if request_type not in ["invoice"]:
                raise InvalidRequestType(request_type)

            headers = properties.headers or {}
            retry_count = headers.get("retry_count", 0)

            if retry_count >= 3:
                print(f"Message exceeded maximum retries. Discarding: {body}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # ACTUAL CODE

            try:
                invoice = Invoice(**message.get("data"))
            except:
                raise InvalidRequestData(message.get("data"))

            print(
                f"Processing message (attempt {retry_count + 1}/3): {body}", flush=True
            )
            print(invoice, flush=True)

            if retry_count == 0:
                time.sleep(random.randint(0, 2000) / 1000)

            send_invoice(invoice)

            print(f"Successfully processed message: {body}", flush=True)

            # ack
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError:
            print(f"Error decoding message: {body}", flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except InvalidRequestType as e:
            print(f"Invalid request type: {str(e)}", flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except InvalidRequestData as e:
            print(f"Invalid request data: {str(e)}", flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"Error processing message: {str(e)}", flush=True)

            retry_count += 1
            print(f"Retry count: {retry_count}", flush=True)

            if retry_count == 1:
                delay = random.randint(15000, 30000)
            elif retry_count == 2:
                delay = random.randint(120000, 180000)
            else:
                delay = random.randint(300000, 420000)

            self.channel.basic_publish(
                exchange="",
                routing_key=self.wait_queue_name,
                body=body,
                properties=pika.BasicProperties(
                    headers={"retry_count": retry_count},
                    expiration=str(delay),
                ),
            )

            print(
                f"Message sent to wait queue. Will retry in {delay/1000} seconds (attempt {retry_count}/3)",
                flush=True,
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def connect(self):
        """Establish connection to RabbitMQ with retry logic"""
        max_retries = 10
        retry_delay = 6

        for attempt in range(max_retries):
            try:
                print(
                    f"Attempting to connect to RabbitMQ (attempt {attempt + 1}/{max_retries})..."
                )

                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=self.rabbitmq_host,
                        port=self.rabbitmq_port,
                        credentials=pika.PlainCredentials(
                            self.rabbitmq_user, self.rabbitmq_pass
                        ),
                        heartbeat=600,
                        blocked_connection_timeout=300,
                        connection_attempts=3,
                        retry_delay=5,
                    )
                )
                self.channel = self.connection.channel()

                self.channel.exchange_declare(
                    exchange=f"{self.queue_name}_dlx", exchange_type="direct"
                )

                self.channel.queue_declare(queue=self.queue_name, durable=True)

                self.channel.queue_declare(
                    queue=self.wait_queue_name,
                    durable=True,
                    arguments={
                        "x-dead-letter-exchange": f"{self.queue_name}_dlx",
                        "x-dead-letter-routing-key": self.queue_name,
                    },
                )

                self.channel.queue_bind(
                    exchange=f"{self.queue_name}_dlx", queue=self.queue_name
                )

                print("Successfully connected to RabbitMQ!")
                return

            except Exception as e:
                print(f"Failed to connect to RabbitMQ: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("Max retries reached. Unable to connect to RabbitMQ.")
                    raise

    def start_consuming(self):
        """Start consuming messages from the queue"""
        while True:
            try:
                if not self.connection or self.connection.is_closed:
                    self.connect()

                self.channel.basic_qos(prefetch_count=1)
                self.channel.basic_consume(
                    queue=self.queue_name, on_message_callback=self.callback
                )

                print(f"Started consuming from queue: {self.queue_name}")
                self.channel.start_consuming()

            except KeyboardInterrupt:
                print("Stopping consumer...")
                if self.channel:
                    self.channel.stop_consuming()
                break
            except Exception as e:
                print(f"Error in consumer: {str(e)}")
                print("Attempting to reconnect...")
                time.sleep(5)
            finally:
                if self.connection and not self.connection.is_closed:
                    self.connection.close()


def start_consumer(queue_name: str):
    consumer = QueueWithRetry(queue_name)
    consumer.connect()
    consumer.channel.basic_qos(prefetch_count=1)
    consumer.channel.basic_consume(
        queue=queue_name, on_message_callback=consumer.callback
    )
    try:
        print(f"Started consumer for queue: {queue_name}", flush=True)
        consumer.channel.start_consuming()
    except Exception as e:
        print(f"Consumer error: {str(e)}", flush=True)
        if consumer.connection and not consumer.connection.is_closed:
            consumer.connection.close()


if __name__ == "__main__":
    num_consumers = int(os.getenv("NUM_CONSUMERS_PER_INSTANCE", "3"))
    queue_name = os.getenv("QUEUE_NAME")

    print(f"Starting {num_consumers} consumers...", flush=True)

    # Create consumer threads
    threads = []
    for i in range(num_consumers):
        thread = threading.Thread(target=start_consumer, args=(queue_name,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
        print(f"Started consumer thread {i+1}", flush=True)

    # Wait for all threads
    for thread in threads:
        thread.join()
