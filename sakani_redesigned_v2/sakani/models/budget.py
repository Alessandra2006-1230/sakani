"""Budget management helpers and validators for Sakani."""

from database import queries
from models import validators

BUDGET_PERIODS = ("monthly", "quarterly", "yearly", "custom")


def is_valid_budget_period(period_type):
    """Return True when the period type is known."""
    return period_type in BUDGET_PERIODS


def check_budget_overlap(user_id, category_id, start_date, end_date, exclude_id=None):
    """Check if a budget would overlap with existing budgets.

    Returns (ok, message). ok=True means no overlap.
    """
    try:
        existing = queries.get_budgets(user_id)
    except Exception:
        # If we can't check (e.g., DB not available), allow and let DB trigger handle it
        return True, ""

    for b in existing:
        if b["category_id"] != category_id:
            continue
        if exclude_id is not None and b["id"] == exclude_id:
            continue
        # Check date overlap: not (b.end < new.start OR b.start > new.end)
        if not (b["end_date"] < start_date or b["start_date"] > end_date):
            return False, (
                "A budget already exists for this category and overlapping date range. "
                "Each category can have only one budget per date range."
            )
    return True, ""


def validate_budget(data, user_id=None, exclude_id=None):
    """Validate budget form values.

    Returns (ok, message, values). values contains cleaned data when ok is True.
    """
    name = (data.get("name") or "").strip()
    if not name:
        return False, "Please enter a budget name.", {}
    if len(name) > 100:
        return False, "Budget name is too long (maximum 100 characters).", {}

    ok, message, amount_float, amount_decimal = validate_budget_amount(data.get("amount"))
    if not ok:
        return False, message, {}

    period_type = data.get("period_type") or "monthly"
    if not is_valid_budget_period(period_type):
        return False, "Please choose a valid budget period.", {}

    ok, start_date = validators.validate_transaction_date(data.get("start_date") or "")
    if not ok:
        return False, start_date, {}

    ok, end_date = validators.validate_transaction_date(data.get("end_date") or "")
    if not ok:
        return False, end_date, {}

    if start_date > end_date:
        return False, "Start date must not be after end date.", {}

    # Check for overlapping budgets at application level
    if user_id is not None:
        category_id = data.get("category_id")
        if isinstance(category_id, str) and category_id.strip() == "":
            category_id = None
        ok, message = check_budget_overlap(user_id, category_id, start_date, end_date, exclude_id)
        if not ok:
            return False, message, {}

    notes = (data.get("notes") or "").strip()
    if len(notes) > 500:
        return False, "Notes are too long (maximum 500 characters).", {}

    values = {
        "name": name,
        "amount": amount_decimal,
        "period_type": period_type,
        "start_date": start_date,
        "end_date": end_date,
        "notes": notes,
    }
    return True, "", values


def validate_budget_amount(raw_amount):
    """Return (ok, message, float_value, decimal_value)."""
    ok, message, amount_decimal = validators.validate_amount(raw_amount)
    if not ok:
        return False, message, None, None
    try:
        amount_float = float(amount_decimal)
    except Exception:
        amount_float = None
    return True, "", amount_float, amount_decimal


def is_valid_budget_period(period_type):
    """Return True when the period type is known."""
    return period_type in BUDGET_PERIODS


BUDGET_PERIODS = ("monthly", "quarterly", "yearly", "custom")
