import pytest
from unittest.mock import Mock, patch
from app.services.random_person_getter.implementation import RandomPersonGetter
from app.models.types import Person


def test_get_random_person_returns_valid_person():
    getter = RandomPersonGetter()

    person = getter.get_random_person()

    assert isinstance(person, Person)
    assert isinstance(person.name, str)
    assert len(person.name) > 0
    assert isinstance(person.cpf, str)


def test_get_random_person_generates_different_people():
    getter = RandomPersonGetter()

    person1 = getter.get_random_person()
    person2 = getter.get_random_person()
    person3 = getter.get_random_person()

    assert person1 != person2
    assert person2 != person3
    assert person1 != person3


def test_get_random_person_uses_faker_correctly():
    with patch("faker.Faker") as mock_faker_class:
        mock_faker = Mock()
        mock_faker.name.return_value = "Test Name"
        mock_faker.cpf.return_value = "803.778.410-05"
        mock_faker_class.return_value = mock_faker

        getter = RandomPersonGetter()
        person = getter.get_random_person()

        mock_faker_class.assert_called_once_with("pt_BR")

        mock_faker.name.assert_called_once()
        mock_faker.cpf.assert_called_once()

        assert person.name == "Test Name"
        assert person.cpf == "803.778.410-05"


def test_get_random_person_handles_invalid_data():
    with patch("faker.Faker") as mock_faker_class:
        mock_faker = Mock()
        mock_faker.name.return_value = "Test Name"
        mock_faker.cpf.return_value = "invalid-cpf"
        mock_faker_class.return_value = mock_faker

        getter = RandomPersonGetter()
        with pytest.raises(ValueError) as exc_info:
            getter.get_random_person()
        assert "CPF must have 11 digits" in str(exc_info.value)

        mock_faker.name.return_value = ""
        mock_faker.cpf.return_value = "803.778.410-05"
        
        with pytest.raises(ValueError) as exc_info:
            getter.get_random_person()
        assert "String should have at least 1 character" in str(exc_info.value)


def test_faker_instance_is_reused():
    with patch("faker.Faker") as mock_faker_class:
        mock_faker = Mock()
        mock_faker.name.return_value = "Test Name"
        mock_faker.cpf.return_value = "803.778.410-05"
        mock_faker_class.return_value = mock_faker

        getter = RandomPersonGetter()

        getter.get_random_person()
        getter.get_random_person()
        getter.get_random_person()

        mock_faker_class.assert_called_once_with("pt_BR")

        assert mock_faker.name.call_count == 3
        assert mock_faker.cpf.call_count == 3 