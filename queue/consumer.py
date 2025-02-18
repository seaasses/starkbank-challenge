import pika
import json
import os
import time
import random
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import re

load_dotenv()


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
    def __init__(self, data: dict):
        super().__init__(f"Invalid request data: {data}")


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

            if request_type not in ["transfer"]:
                raise InvalidRequestType(request_type)

            headers = properties.headers or {}
            retry_count = headers.get("retry_count", 0)

            if retry_count >= 3:
                print(f"Message exceeded maximum retries. Discarding: {body}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # ACTUAL CODE

            try:
                transfer = Transfer(**message["data"])
                print(transfer)
            except:
                raise InvalidRequestData(message["data"])

            print(f"Processing message (attempt {retry_count + 1}/3): {body}")

            from datetime import datetime

            print(datetime.now(), flush=True)
            print(body, flush=True)
            message_data = json.loads(body)
            if "fail" in message_data:
                raise Exception("Message failed")

            print(f"Successfully processed message: {body}")
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
        max_retries = 5
        retry_delay = 5

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


if __name__ == "__main__":
    consumer = QueueWithRetry(
        queue_name="task_queue",
    )
    consumer.start_consuming()
