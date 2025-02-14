from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import starkbank

load_dotenv()


def construct_private_key(ec_parameters: str, ec_private_key: str) -> str:
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


class Settings(BaseSettings):
    STARK_ENVIRONMENT: str
    STARK_PROJECT_ID: str
    STARKBANK_EC_PARAMETERS: str
    STARKBANK_EC_PRIVATE_KEY: str

    @property
    def starkbank_project(self) -> starkbank.Project:
        return starkbank.Project(
            environment=self.STARK_ENVIRONMENT,
            id=self.STARK_PROJECT_ID,
            private_key=construct_private_key(
                self.STARKBANK_EC_PARAMETERS,
                self.STARKBANK_EC_PRIVATE_KEY,
            ),
        )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
