import pika
import json
import time
import random
from ..models.schemas import Invoice, InvalidRequestType, InvalidRequestData
from ..config.settings import RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASS
from .starkbank_service import send_invoice


class QueueWithRetry:
    def __init__(self, queue_name: str):
        self.queue_name = queue_name
        self.wait_queue_name = f"{queue_name}_wait"
        self.connection = None
        self.channel = None

    def callback(self, ch, method, properties, body):
        print("BBBBBBBBBBBBBBBBBBBBBBBBBBBBBB", flush=True)
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
                        host=RABBITMQ_HOST,
                        port=RABBITMQ_PORT,
                        credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS),
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
