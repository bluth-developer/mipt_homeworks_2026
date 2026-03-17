#!/usr/bin/env python
from typing import Any  # извинте но не хочется вкостыливать None в список парсеров

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
OP_SUCCESS_MSG = "Added"

def parse_amount(amount: str) -> float:
    return float(amount.replace(",", "."))

def check_amount(amount: float) -> bool:
    return amount > 0

def is_leap_year(year: int) -> bool:
    """
    Для заданного года определяет: високосный (True) или невисокосный (False).

    :param int year: Проверяемый год
    :return: Значение високосности.
    :rtype: bool
    """

    default_condition = not (year % 4)
    blocking_condition = not (year % 100)
    unblocking_condition = not (year % 400)

    return default_condition and (not blocking_condition or unblocking_condition)

DATE_PARTS_COUNT = 3
MONTHS_COUNT = 12
FEB_LEAP_COUNT = 29
FEB_COUNT = 28
FEB_IDX = 2

days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    """
    Парсит дату формата DD-MM-YYYY из строки.

    :param str maybe_dt: Проверяемая строка
    :return: typle формата (день, месяц, год) или None, если дата неправильная.
    :rtype: tuple[int, int, int] | None
    """
    parts = maybe_dt.split("-")

    if len(parts) != DATE_PARTS_COUNT:
        return None
    if not all(i.isnumeric() for i in parts):
        return None
    day, month, year = [int(i) for i in parts]

    if month < 1 or month > MONTHS_COUNT:
        return None

    days_count = days[month - 1]

    if month == FEB_IDX:
        days_count = FEB_LEAP_COUNT if is_leap_year(year) else FEB_COUNT

    if (day < 1 or day > days_count) or (month < 1 or month > MONTHS_COUNT) or year < 1:
        return None

    return day, month, year

incomes: list[tuple[float, tuple[int, int, int]]] = []
costs: list[tuple[str, float, tuple[int, int, int]]] = []

def income_handler(amount: float, income_date: str) -> str:
    parsed_date = extract_date(income_date)

    if not check_amount(amount):
        return NONPOSITIVE_VALUE_MSG

    if parsed_date is None:
        return INCORRECT_DATE_MSG

    incomes.append((amount, parsed_date))
    return OP_SUCCESS_MSG

def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    parsed_date = extract_date(income_date)
    if not check_amount(amount):
        return NONPOSITIVE_VALUE_MSG

    if parsed_date is None:
        return INCORRECT_DATE_MSG

    costs.append((category_name, amount, parsed_date))
    return OP_SUCCESS_MSG

def is_before_or_equal(checking: tuple[int, int, int], checker: tuple[int, int, int]) -> bool:
    return ((checking[2] < checker[2]) or
            (checking[2] == checker[2] and checking[1] < checker[1]) or
            (checking[2] == checker[2] and checking[1] == checker[1] and checking[0] <= checker[0]))

def is_before(checking: tuple[int, int, int], checker: tuple[int, int, int]) -> bool:
    return ((checking[2] < checker[2]) or
            (checking[2] == checker[2] and checking[1] < checker[1]) or
            (checking[2] == checker[2] and checking[1] == checker[1] and checking[0] < checker[0]))

def is_after(checking: tuple[int, int, int], checker: tuple[int, int, int]) -> bool:
    return not is_before_or_equal(checking, checker)

def is_after_or_equal(checking: tuple[int, int, int], checker: tuple[int, int, int]) -> bool:
    return not is_before(checking, checker)

def timed_sum(timed: list[Any], start: tuple[int, int, int], end: tuple[int, int, int]) -> float:
    total = 0
    for item in timed:
        if is_after_or_equal(item[1], start) and is_before_or_equal(item[1], end):
            total += item[0]
    return total

def calculate_capital(date: tuple[int, int, int]) -> float:
    return timed_sum(incomes, (00, 00, 0000), date) - timed_sum([(x[1], x[2]) for x in costs], (00, 00, 0000), date)

def sum_monthly(timed: list[Any], date: tuple[int, int, int]) -> float:
    month_start = 0, date[1], date[2]

    return timed_sum(timed, month_start, date)

def calculate_details(date: tuple[int, int, int]) -> dict[str, float]:
    month_start = 0, date[1], date[2]

    details: dict[str, float] = {}
    for item in costs:
        if is_after_or_equal(item[2], month_start) and is_before_or_equal(item[2], date):
            amount = details.get(item[0], 0)
            details[item[0]] = amount + item[1]

    return details


def stats_handler(report_date: str) -> str:
    parsed_date = extract_date(report_date)
    if parsed_date is None:
        return INCORRECT_DATE_MSG
    capital = calculate_capital(parsed_date)
    monthly_income = sum_monthly(incomes, parsed_date)
    monthly_expenses = sum_monthly([(x[1], x[2]) for x in costs], parsed_date)

    cash_type = None
    cash_amount: float = 0.0

    if monthly_income >= monthly_expenses:
        cash_type = "profit"
        cash_amount = monthly_income - monthly_expenses
    else:
        cash_type = "loss"
        cash_amount = monthly_expenses - monthly_income

    details = "\n".join(f"{idx}. {key}: {val:.2f}" for idx, (key, val) in
                        enumerate(sorted(calculate_details(parsed_date).items()), 1))


    return f"""Your statistics as of {report_date}:
Total capital: {capital:.2f} rubles
This month, the {cash_type} amounted to {cash_amount:.2f} rubles.
Income: {monthly_income:.2f} rubles
Expenses: {monthly_expenses:.2f} rubles

Details (category: amount):
""" + details


def nop(arg: Any) -> Any:
    return arg

caller: dict[str, list[Any]] = {
    "income": [income_handler, 2, (parse_amount, nop)],
    "cost": [cost_handler, 3, (nop, parse_amount, nop)],
    "stats": [stats_handler, 1, (nop, )]
}

def parse_args(arguments: list[Any], parsers: list[Any]) -> list[Any]:
    return [parser(arg) for arg, parser in zip(arguments, parsers, strict=True)]

def assert_command(command: str, arguments: list[Any]) -> bool:
    return bool(caller[command][1] == len(arguments))

def main() -> None:
    while True:
        command = input()
        arguments = command.split()
        if caller.get(arguments[0]) is None or not assert_command(arguments[0], arguments[1:]):
            print(UNKNOWN_COMMAND_MSG)
            continue
        result = caller[arguments[0]][0](*parse_args(arguments[1:], caller[arguments[0]][2]))
        print(result)


if __name__ == "__main__":
    main()
