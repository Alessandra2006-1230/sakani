"""Input validators for money, dates and text fields used by Sakani."""

import math
import re
from datetime import datetime
from decimal import Decimal

MAX_AMOUNT = 9_999_999_999.99  # DECIMAL(12,2) maximum
MAX_DESCRIPTION_LENGTH = 255
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_amount(raw_amount):
    """Return (ok, amount_or_message, Decimal).

    Amounts must be positive, finite numbers within the DECIMAL(12,2) range.
    Returns a Decimal so financial math never uses binary floating point.
    """
    cleaned = str(raw_amount).strip().replace(",", "").replace("₱", "")
    if not cleaned:
        return False, "Please enter an amount.", None
    try:
        value = float(cleaned)
    except ValueError:
        return False, "Please enter a valid amount.", None
    if not math.isfinite(value):
        return False, "Amount must be a finite number.", None
    if value <= 0:
        return False, "Amount must be greater than zero.", None
    if value > MAX_AMOUNT:
        return False, "Amount is too large (maximum 9,999,999,999.99).", None
    return True, value, Decimal(str(cleaned))


def validate_transaction_date(raw_date):
    """Return (ok, date_or_message). Accepts YYYY-MM-DD only."""
    text = str(raw_date).strip()
    if not DATE_PATTERN.match(text):
        return False, "Please use a valid date in YYYY-MM-DD format."
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return False, "Please use a valid date in YYYY-MM-DD format."
    return True, parsed


def validate_description(raw_description):
    """Return (ok, cleaned_description_or_message)."""
    cleaned = str(raw_description).strip()
    if len(cleaned) > MAX_DESCRIPTION_LENGTH:
        return False, "Description is too long (maximum 255 characters)."
    return True, cleaned
