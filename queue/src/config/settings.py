import os
from dotenv import load_dotenv

load_dotenv()


# RabbitMQ Settings
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS")

# Starkbank Settings
STARK_PROJECT_ID = os.getenv("STARK_PROJECT_ID")
STARK_ENVIRONMENT = os.getenv("STARK_ENVIRONMENT")


def get_private_key():
    return f"""-----BEGIN EC PARAMETERS-----
{os.getenv("STARKBANK_EC_PARAMETERS")}
-----END EC PARAMETERS-----
-----BEGIN EC PRIVATE KEY-----
{os.getenv("STARKBANK_EC_PRIVATE_KEY")}
-----END EC PRIVATE KEY-----"""


# Consumer Settings
NUM_CONSUMERS_PER_INSTANCE = int(os.getenv("NUM_CONSUMERS_PER_INSTANCE", "30"))
