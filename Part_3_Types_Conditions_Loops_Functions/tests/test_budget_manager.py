
from Part_3_Types_Conditions_Loops_Functions.hw3 import OP_SUCCESS_MSG, income_handler
from Part_3_Types_Conditions_Loops_Functions.tests.conftest import IncomeFactory


def test_income_success(income_factory: type[IncomeFactory]) -> None:
    income_instance = income_factory.build()
    assert income_handler(income_instance.amount, income_instance.date) == OP_SUCCESS_MSG
