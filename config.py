import os
from dotenv import load_dotenv
import starkbank

load_dotenv()


def construct_private_key(ec_parameters: str, ec_private_key: str):
    if not ec_parameters or not ec_private_key:
        raise ValueError(
            "EC Parameters or Private Key not found in environment variables"
        )

    return f"""-----BEGIN EC PARAMETERS-----
{ec_parameters}
-----END EC PARAMETERS-----
-----BEGIN EC PRIVATE KEY-----
{ec_private_key}
-----END EC PRIVATE KEY-----"""


class Config:
    def __init__(self):

        self.starkbank_project = starkbank.Project(
            environment=os.getenv("STARK_ENVIRONMENT"),
            id=os.getenv("STARK_PROJECT_ID"),
            private_key=construct_private_key(
                os.getenv("STARKBANK_EC_PARAMETERS"),
                os.getenv("STARKBANK_EC_PRIVATE_KEY"),
            ),
        )


config = Config()
