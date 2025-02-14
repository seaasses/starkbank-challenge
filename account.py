from pydantic import BaseModel, field_validator, Field
from enum import Enum
import re


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
