from pydantic import BaseModel
from enum import Enum
from pydantic import Field, field_validator
import re
from datetime import date, datetime
from typing import Optional, Literal


class Person(BaseModel):
    name: str = Field(min_length=1)
    cpf: str  # TODO add validator


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


class Invoice(BaseModel):
    amount: int = Field(gt=0, lt=10000000000)
    person: Person
    due_date: Optional[date] = None


class StarkBankEvent(BaseModel):
    created: datetime
    id: str
    log: dict  # TODO: create log models
    subscription: str
    workspaceId: str
