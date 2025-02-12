import random
import faker
from dataclasses import dataclass


@dataclass
class Person:
    name: str
    cpf: str


class PersonGenerator:
    def __init__(self):
        self.faker = faker.Faker()

    def generate_person(self) -> Person:
        print(self.__generate_name())
        return Person(name=self.__generate_name(), cpf=self.__generate_cpf())

    def __generate_name(self) -> str:
        return self.faker.name()

    def __generate_cpf(self) -> str:
        # open source implementation of cpf generator (https://gist.github.com/lucascnr/24c70409908a31ad253f97f9dd4c6b7c)
        cpf = [random.randint(0, 9) for x in range(9)]

        for _ in range(2):
            val = sum([(len(cpf) + 1 - i) * v for i, v in enumerate(cpf)]) % 11

            cpf.append(11 - val if val > 1 else 0)

        return "%s%s%s.%s%s%s.%s%s%s-%s%s" % tuple(cpf)


if __name__ == "__main__":
    person_generator = PersonGenerator()
    print(person_generator.generate_person())
