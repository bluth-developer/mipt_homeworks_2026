#!/usr/bin/env python

import sys
from typing import Any, Final

type DateTuple = tuple[int, int, int]

INCORRECT_DATE_MSG: Final = "Invalid date!"
NOT_EXISTS_CATEGORY: Final = "Category not exists!"
OP_SUCCESS_MSG: Final = "Added"
NONPOSITIVE_VALUE_MSG: Final = "Value must be positive!"
UNKNOWN_COMMAND_MSG: Final = "Unknown command!"

ATTR_AMOUNT: Final = "amount"
ATTR_DATE: Final = "date"
ATTR_CATEGORY: Final = "category"

EXPENSE_CATEGORIES: Final = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}

financial_transactions_storage: list[dict[str, Any]] = []

DATE_PARTS_COUNT: Final = 3
MONTHS_COUNT: Final = 12
FEB_LEAP_COUNT: Final = 29
FEB_COUNT: Final = 28
FEB_IDX: Final = 2

DAYS_IN_MONTH: Final = [
    31, 28, 31, 30, 31, 30,
    31, 31, 30, 31, 30, 31,
]

CATEGORY_PARTS_COUNT: Final = 2
INCOME_CMD_PARTS: Final = 3
COST_CATEGORIES_CMD_PARTS: Final = 2
COST_CMD_PARTS: Final = 4
STATS_CMD_PARTS: Final = 2


def is_leap_year(year: int) -> bool:
    small_condition = not (year % 4)
    blocking_condition = not (year % 100)
    big_condition = not (year % 400)
    return small_condition and (not blocking_condition or big_condition)


def extract_date(maybe_dt: str) -> DateTuple | None:
    parts = maybe_dt.split("-")

    if len(parts) != DATE_PARTS_COUNT:
        return None
    if not all(i.isnumeric() for i in parts):
        return None

    day, month, year = (int(i) for i in parts)

    if month < 1 or month > MONTHS_COUNT or year < 1:
        return None

    days_limit = DAYS_IN_MONTH[month - 1]
    if month == FEB_IDX:
        days_limit = FEB_LEAP_COUNT if is_leap_year(year) else FEB_COUNT

    if day < 1 or day > days_limit:
        return None

    return day, month, year


def _is_before_or_equal(checking: DateTuple, checker: DateTuple) -> bool:
    left = (checking[2], checking[1], checking[0])
    right = (checker[2], checker[1], checker[0])
    return left <= right


def _is_before(checking: DateTuple, checker: DateTuple) -> bool:
    left = (checking[2], checking[1], checking[0])
    right = (checker[2], checker[1], checker[0])
    return left < right


def _is_after_or_equal(checking: DateTuple, checker: DateTuple) -> bool:
    return not _is_before(checking, checker)


def _timed_sum_incomes(start: DateTuple, end: DateTuple) -> float:
    total = 0
    for item in financial_transactions_storage:
        if not item or ATTR_CATEGORY in item:
            continue
        valid_start = _is_after_or_equal(item[ATTR_DATE], start)
        valid_end = _is_before_or_equal(item[ATTR_DATE], end)
        if valid_start and valid_end:
            total += item[ATTR_AMOUNT]
    return float(total)


def _timed_sum_costs(start: DateTuple, end: DateTuple) -> float:
    total = 0
    for item in financial_transactions_storage:
        if not item or ATTR_CATEGORY not in item:
            continue
        valid_start = _is_after_or_equal(item[ATTR_DATE], start)
        valid_end = _is_before_or_equal(item[ATTR_DATE], end)
        if valid_start and valid_end:
            total += item[ATTR_AMOUNT]
    return float(total)


def _calculate_details(start: DateTuple, end: DateTuple) -> dict[str, float]:
    details: dict[str, float] = {}
    for item in financial_transactions_storage:
        if not item or ATTR_CATEGORY not in item:
            continue
        valid_start = _is_after_or_equal(item[ATTR_DATE], start)
        valid_end = _is_before_or_equal(item[ATTR_DATE], end)
        if valid_start and valid_end:
            cat = item[ATTR_CATEGORY]
            details[cat] = details.get(cat, 0) + item[ATTR_AMOUNT]
    return details


def income_handler(amount: float, income_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG
    parsed = extract_date(income_date)
    if parsed is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG
    financial_transactions_storage.append({ATTR_AMOUNT: amount, ATTR_DATE: parsed})
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG
    parsed = extract_date(income_date)
    if parsed is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG
    parts = category_name.split("::")
    if (
        len(parts) != CATEGORY_PARTS_COUNT
        or parts[0] not in EXPENSE_CATEGORIES
        or parts[1] not in EXPENSE_CATEGORIES[parts[0]]
    ):
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY
    financial_transactions_storage.append({
        ATTR_CATEGORY: category_name,
        ATTR_AMOUNT: amount,
        ATTR_DATE: parsed,
    })
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    lines: list[str] = []
    for category, subcategories in EXPENSE_CATEGORIES.items():
        lines.extend(f"{category}::{sub}" for sub in subcategories)
    return "\n".join(lines)


def _get_cash_info(income: float, expenses: float) -> tuple[str, float]:
    if income >= expenses:
        return "profit", income - expenses
    return "loss", expenses - income


def _get_monthly_stats(start: DateTuple, end: DateTuple) -> dict[str, Any]:
    inc = _timed_sum_incomes(start, end)
    exp = _timed_sum_costs(start, end)
    ctype, camt = _get_cash_info(inc, exp)
    return {
        "income": inc,
        "expenses": exp,
        "cash_type": ctype,
        "cash_amount": camt,
    }


def _format_details(start: DateTuple, end: DateTuple) -> list[str]:
    details = sorted(_calculate_details(start, end).items())
    return [
        f"{idx}. {k}: {v:.2f}"
        for idx, (k, v) in enumerate(details, 1)
    ]


def stats_handler(report_date: str) -> str:
    parsed = extract_date(report_date)
    if parsed is None:
        return INCORRECT_DATE_MSG

    m_start: DateTuple = (0, parsed[1], parsed[2])
    m_stats = _get_monthly_stats(m_start, parsed)
    total_cap = (
        _timed_sum_incomes((0, 0, 0), parsed)
        - _timed_sum_costs((0, 0, 0), parsed)
    )

    rep_lines = [
        f"Your statistics as of {report_date}:",
        f"Total capital: {total_cap:.2f} rubles",
        f"This month, the {m_stats['cash_type']} amounted to {m_stats['cash_amount']:.2f} rubles.",
        f"Income: {m_stats['income']:.2f} rubles",
        f"Expenses: {m_stats['expenses']:.2f} rubles",
        "",
        "Details (category: amount):",
    ]

    rep_lines.extend(_format_details(m_start, parsed))
    return "\n".join(rep_lines)


def _parse_amount(raw: str) -> float:
    return float(raw.replace(",", "."))


def _handle_command(parts: list[str]) -> str:
    cmd = parts[0]
    count = len(parts)
    if cmd == "income" and count == INCOME_CMD_PARTS:
        return income_handler(_parse_amount(parts[1]), parts[2])
    if cmd == "cost" and count == COST_CATEGORIES_CMD_PARTS and parts[1] == "categories":
        return cost_categories_handler()
    if cmd == "cost" and count == COST_CMD_PARTS:
        return cost_handler(parts[1], _parse_amount(parts[2]), parts[3])
    if cmd == "stats" and count == STATS_CMD_PARTS:
        return stats_handler(parts[1])
    return UNKNOWN_COMMAND_MSG


def main() -> None:
    for line in sys.stdin:
        parts = line.split()
        if not parts:
            print(UNKNOWN_COMMAND_MSG)
            continue
        print(_handle_command(parts))


if __name__ == "__main__":
    main()
