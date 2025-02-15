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
    amount: int  # TODO maybe create the Amount class that have a decimal value? This is RRRRCC. R - real, C - cents


class Invoice(BaseModel):
    amount: int = Field(gt=0)
    person: Person
    due_date: Optional[date] = None


class StarkBankInvoice(BaseModel):
    amount: int
    brcode: str
    created: str
    descriptions: list[str]
    discountAmount: int
    discounts: list[str]
    displayDescription: str
    due: str
    expiration: int
    fee: int
    fine: float
    fineAmount: float
    id: str
    interest: float
    interestAmount: float
    link: str
    name: str
    nominalAmount: int
    pdf: str
    rules: list[str]
    splits: list[str]
    status: str
    tags: list[str]
    taxId: str
    transactionIds: list[str]
    updated: str


class StarkBankInvoiceEventLog(BaseModel):
    authentication: str
    created: str
    errors: list[str]
    id: str
    invoice: StarkBankInvoice
    type: Literal["created", "credited", "paid"]  # TODO see in the docs all the types


class _StarkBankInvoiceEvent(BaseModel):
    created: datetime
    id: str
    log: StarkBankInvoiceEventLog
    subscription: Literal["invoice"]
    workspaceId: str


class StarkBankInvoiceEvent(BaseModel):
    event: _StarkBankInvoiceEvent
