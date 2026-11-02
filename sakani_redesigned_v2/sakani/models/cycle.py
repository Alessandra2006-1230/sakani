"""Production cycle status helpers and validators for Sakani."""

from models import validators

CYCLE_STATUSES = ("planned", "active", "harvested", "archived")
VALID_STATUS_TRANSITIONS = {
    "planned": ("active",),
    "active": ("harvested",),
    "harvested": ("archived",),
    "archived": (),
}


def is_valid_cycle_status(status):
    """Return True when the status is one of the known cycle states."""
    return status in CYCLE_STATUSES


def is_valid_transition(current_status, next_status):
    """Return True when the status change follows the safe lifecycle.

    planned -> active -> harvested -> archived. No transitions out of
    'archived' are allowed.
    """
    if current_status not in CYCLE_STATUSES or next_status not in CYCLE_STATUSES:
        return False
    allowed = VALID_STATUS_TRANSITIONS.get(current_status, ())
    return next_status in allowed


def validate_cycle_fields(data):
    """Validate production-cycle form values.

    ``data`` is a dict with optional keys: crop_name, variety, plot_name,
    start_date, expected_harvest_date, actual_harvest_date, status, notes.

    Returns (ok, message, values). ``message`` is an error string when ok is
    False, otherwise ``values`` holds the cleaned values.
    """
    ok, crop_name = validators.validate_description(data.get("crop_name") or "")
    if not ok:
        return False, crop_name, {}
    if not crop_name:
        return False, "Please enter a crop name.", {}

    ok, start_date = validators.validate_transaction_date(data.get("start_date") or "")
    if not ok:
        return False, start_date, {}

    expected_harvest_date = None
    if data.get("expected_harvest_date"):
        ok, expected_harvest_date = validators.validate_transaction_date(
            data["expected_harvest_date"])
        if not ok:
            return False, expected_harvest_date, {}

    actual_harvest_date = None
    if data.get("actual_harvest_date"):
        ok, actual_harvest_date = validators.validate_transaction_date(
            data["actual_harvest_date"])
        if not ok:
            return False, actual_harvest_date, {}

    status = data.get("status") or "planned"
    if not is_valid_cycle_status(status):
        return False, "Please choose a valid status.", {}

    notes = data.get("notes") or ""
    if len(notes) > 500:
        return False, "Notes are too long (maximum 500 characters).", {}

    values = {
        "crop_name": crop_name,
        "variety": (data.get("variety") or "").strip(),
        "plot_name": (data.get("plot_name") or "").strip(),
        "start_date": start_date,
        "expected_harvest_date": expected_harvest_date,
        "actual_harvest_date": actual_harvest_date,
        "status": status,
        "notes": notes,
    }
    return True, "", values
