from person_generator import PersonGenerator
from person_generator import Person
import pytest


@pytest.fixture
def person_generator():
    return PersonGenerator()


def test_generate_person_returns_a_person(person_generator):
    person = person_generator.generate_person()
    assert isinstance(person, Person)


def test_return_non_none_person(person_generator):
    person = person_generator.generate_person()
    assert person.name is not None
    assert person.cpf is not None


def test_return_non_empty_person(person_generator):
    person = person_generator.generate_person()
    assert person.name != ""
    assert person.cpf != ""


def test_cpf_is_valid(person_generator):
    # TODO create a class for this and add tests for it
    def check_cpf_checksum(cpf: str) -> bool:
        cpf = cpf.replace(".", "").replace("-", "")
        if len(cpf) != 11:
            return False
        total = 0
        for i in range(9):
            total += int(cpf[i]) * (10 - i)
        if total % 11 < 2:
            return int(cpf[9]) == 0
        return int(cpf[9]) == 11 - total % 11

    person = person_generator.generate_person()
    assert check_cpf_checksum(person.cpf)
