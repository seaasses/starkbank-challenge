from account import Account
from pydantic import BaseModel


class Transfer(BaseModel):
    account: Account
    amount: int  # TODO maybe create the Amount class that have a decimal value? This is RRRRCC. R - real, C - cents
