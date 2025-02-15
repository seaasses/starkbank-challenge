from typing import Literal
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import starkbank
from app.models.types import Account, AccountType

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
    ENVIRONMENT: Literal["development", "production"]
    STARK_ENVIRONMENT: Literal["sandbox", "production"]
    STARK_PROJECT_ID: str
    STARKBANK_EC_PARAMETERS: str
    STARKBANK_EC_PRIVATE_KEY: str
    API_EXTERNAL_URL: str
    DEFAULT_BANK_CODE: str = Field(default="20018183")
    DEFAULT_BRANCH: str = Field(default="0001")
    DEFAULT_ACCOUNT: str = Field(default="6341320293482496")
    DEFAULT_NAME: str = Field(default="Stark Bank S.A.")
    DEFAULT_TAX_ID: str = Field(default="20.018.183/0001-80")
    DEFAULT_ACCOUNT_TYPE: AccountType = Field(default="payment")

    @model_validator(mode="after")
    def validate_default_account(self):
        self.default_account
        return self

    @property
    def default_account(self) -> Account:
        return Account(
            bank_code=self.DEFAULT_BANK_CODE,
            branch=self.DEFAULT_BRANCH,
            account=self.DEFAULT_ACCOUNT,
            name=self.DEFAULT_NAME,
            tax_id=self.DEFAULT_TAX_ID,
            account_type=self.DEFAULT_ACCOUNT_TYPE,
        )

    @property
    def starkbank_invoices_webhook_url(self) -> str:
        return f"{self.API_EXTERNAL_URL}/api/v1/webhooks/starkbank"

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
