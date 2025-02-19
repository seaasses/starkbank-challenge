from pydantic import BaseModel, Field, field_validator
from enum import Enum
from datetime import date
from typing import Optional
import re


class Person(BaseModel):
    name: str = Field(min_length=1)
    cpf: str

    @field_validator("cpf")
    def validate_cpf(cls, v: str) -> str:
        numbers = "".join(filter(str.isdigit, v))

        if len(numbers) != 11:
            raise ValueError("CPF must have 11 digits")

        if len(set(numbers)) == 1:
            raise ValueError("Invalid CPF")

        sum_of_products = sum(
            int(a) * b for a, b in zip(numbers[0:9], range(10, 1, -1))
        )
        expected_digit = (sum_of_products * 10 % 11) % 10
        if int(numbers[9]) != expected_digit:
            raise ValueError("Invalid CPF")

        sum_of_products = sum(
            int(a) * b for a, b in zip(numbers[0:10], range(11, 1, -1))
        )
        expected_digit = (sum_of_products * 10 % 11) % 10
        if int(numbers[10]) != expected_digit:
            raise ValueError("Invalid CPF")

        return v


class Invoice(BaseModel):
    amount: int = Field(gt=0, lt=10000000000)
    person: Person
    due_date: Optional[date] = None


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


class InvalidRequestType(Exception):
    def __init__(self, request_type: str):
        super().__init__(f"Invalid request type: {request_type}")


class InvalidRequestData(Exception):
    def __init__(self, data):
        super().__init__(f"Invalid request data: {data}") 