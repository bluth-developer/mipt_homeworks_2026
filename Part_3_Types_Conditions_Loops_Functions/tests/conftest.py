from dataclasses import dataclass
from datetime import UTC, datetime
from typing import NotRequired, TypedDict

from faker import Faker
from polyfactory.factories import DataclassFactory
from polyfactory.pytest_plugin import register_fixture


@dataclass
class Income:
    amount: float
    date: str


class IncomeKwargs(TypedDict):
    amount: NotRequired[float]
    date: NotRequired[str]


@register_fixture
class IncomeFactory(DataclassFactory[Income]):
    __faker__ = Faker("en_US")

    @classmethod
    def amount(cls) -> float:
        return float(cls.__faker__.pydecimal(5, 2, positive=True))

    @classmethod
    def date(cls) -> str:
        return str(datetime.now(tz=UTC).date())
