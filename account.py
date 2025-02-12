from pydantic import BaseModel


class Account(BaseModel):
    bank_code: str
    branch: str
    account: str
    name: str
    tax_id: str
    account_type: str
