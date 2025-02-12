from pydantic import BaseModel
from person_generator import Person
from datetime import date
from typing import Optional


class Invoice(BaseModel):
    amount: int
    person: Person
    due_date: Optional[date] = None
