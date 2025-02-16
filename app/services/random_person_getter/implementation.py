from app.models.types import Person
import faker


class RandomPersonGetter:
    def __init__(self):
        self.faker = faker.Faker("pt_BR")

    def get_random_person(self) -> Person:
        return Person(
            name=self.faker.name(),
            cpf=self.faker.cpf(),
        )
