import pika
import json
from app.services.queue_service.interface import QueueService
import socket


class RabbitMQService(QueueService):
    def __init__(
        self,
        queue_name: str,
        rabbitmq_host: str,
        rabbitmq_port: int,
        rabbitmq_user: str,
        rabbitmq_pass: str,
    ):
        self.queue_name = queue_name
        self.connection = None
        self.channel = None

        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_port = rabbitmq_port
        self.rabbitmq_user = rabbitmq_user
        self.rabbitmq_pass = rabbitmq_pass

    def __connect(self):
        try:

            # Try to resolve hostname
            try:
                socket.gethostbyname(self.rabbitmq_host)
            except socket.gaierror as e:
                raise

            credentials = pika.PlainCredentials(self.rabbitmq_user, self.rabbitmq_pass)

            parameters = pika.ConnectionParameters(
                host=self.rabbitmq_host,
                port=self.rabbitmq_port,
                credentials=credentials,
                connection_attempts=3,
                retry_delay=5,
                socket_timeout=5,
            )

            self.connection = pika.BlockingConnection(parameters)

            self.channel = self.connection.channel()

            self.channel.queue_declare(queue=self.queue_name, durable=True)

        except Exception as e:
            raise

    def publish_message(self, message: dict[str, str]) -> bool:
        try:
            if not self.connection or self.connection.is_closed:
                self.__connect()

            message_body = json.dumps(message)

            self.channel.basic_publish(
                exchange="",
                routing_key=self.queue_name,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                ),
            )

            return True

        except Exception as e:
            return False
        finally:
            if self.connection and not self.connection.is_closed:
                self.connection.close()

    def publish_messages(self, messages: list[dict[str, str]]) -> list[bool]:
        return [self.publish_message(message) for message in messages]

    def test_connection(self) -> bool:
        try:
            self.__connect()
            return True
        except Exception as e:
            return False
        finally:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
