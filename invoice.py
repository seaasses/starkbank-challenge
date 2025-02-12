from dataclasses import dataclass
from person_generator import Person
from datetime import date
from typing import Optional


@dataclass
class Invoice:
    amount: int
    person: Person
    due_date: Optional[date] = None
