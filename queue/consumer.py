import pika
import json
import os
import time
from typing import Callable
from dotenv import load_dotenv

load_dotenv()


class SimpleQueueConsumer:
    def __init__(self, queue_name: str = "simple_queue"):
        self.queue_name = queue_name
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
                print(f"Attempting to connect to RabbitMQ (attempt {attempt + 1}/{max_retries})...")
                
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
                        retry_delay=5
                    )
                )
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.queue_name, durable=True)
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
        """Default callback function to process messages"""
        try:
            message = json.loads(body)
            print(f"Received message: {message}", flush=True)

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError:
            print(f"Error decoding message: {body}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self, callback: Callable = None):
        """Start consuming messages from the queue"""
        while True:
            try:
                if not self.connection or self.connection.is_closed:
                    self.connect()

                self.channel.basic_qos(prefetch_count=1)

                self.channel.basic_consume(
                    queue=self.queue_name,
                    on_message_callback=callback if callback else self.callback,
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
                time.sleep(5)  # Wait before reconnecting
            finally:
                if self.connection and not self.connection.is_closed:
                    self.connection.close()


if __name__ == "__main__":
    consumer = SimpleQueueConsumer()
    consumer.start_consuming()
