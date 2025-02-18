import pika
import json
import os
import time
import random
from typing import Callable
from dotenv import load_dotenv

load_dotenv()


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

    def connect(self):
        """Establish connection to RabbitMQ with retry logic"""
        max_retries = 5
        retry_delay = 5  # seconds

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

                # Declarar a exchange de dead letter
                self.channel.exchange_declare(
                    exchange=f"{self.queue_name}_dlx", exchange_type="direct"
                )

                # Declarar a fila principal que receberá as mensagens após o delay
                self.channel.queue_declare(queue=self.queue_name, durable=True)

                # Declarar a fila de espera (wait queue) que terá as mensagens em delay
                self.channel.queue_declare(
                    queue=self.wait_queue_name,
                    durable=True,
                    arguments={
                        "x-dead-letter-exchange": f"{self.queue_name}_dlx",
                        "x-dead-letter-routing-key": self.queue_name,
                    },
                )

                # Bind da dead letter exchange com a fila principal
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

    def callback(self, ch, method, properties, body):
        """Callback function to process messages with retry logic"""
        try:
            # Get retry count from message headers
            headers = properties.headers or {}
            retry_count = headers.get("retry_count", 0)

            if retry_count >= 3:
                print(f"Message exceeded maximum retries. Discarding: {body}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            print(f"Processing message (attempt {retry_count + 1}/3): {body}")

            # Aqui você coloca sua lógica de processamento
            from datetime import datetime

            print(datetime.now(), flush=True)
            print(body, flush=True)
            message_data = json.loads(body)
            if "fail" in message_data:
                raise Exception("Message failed")

            # Se chegou aqui, o processamento foi bem sucedido
            print(f"Successfully processed message: {body}")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError:
            print(f"Error decoding message: {body}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"Error processing message: {str(e)}")

            retry_count += 1

            delay = 10

            self.channel.basic_publish(
                exchange="",
                routing_key=self.wait_queue_name,
                body=body,
                properties=pika.BasicProperties(
                    headers={"retry_count": retry_count},
                    expiration=str(delay * 1000),  # TTL em milissegundos
                ),
            )

            print(
                f"Message sent to wait queue. Will retry in {delay} seconds (attempt {retry_count}/3)"
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)

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
