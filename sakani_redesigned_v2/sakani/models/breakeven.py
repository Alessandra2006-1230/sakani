"""Break-even analysis helpers for Sakani."""

from decimal import Decimal, ROUND_HALF_UP


def calculate_break_even_quantity(fixed_costs, price_per_unit):
    """Calculate break-even quantity.

    break_even_quantity = fixed_costs / price_per_unit

    Returns (ok, message, quantity_decimal).
    """
    if price_per_unit <= 0:
        return False, "Selling price per unit must be greater than zero.", None
    if fixed_costs < 0:
        return False, "Fixed costs cannot be negative.", None

    try:
        qty = (Decimal(str(fixed_costs)) / Decimal(str(price_per_unit))).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    except Exception:
        return False, "Invalid input for break-even calculation.", None

    return True, "", qty


def calculate_break_even_revenue(fixed_costs):
    """Break-even revenue equals the costs to be covered."""
    if fixed_costs < 0:
        return False, "Fixed costs cannot be negative.", None
    return True, "", Decimal(str(fixed_costs))


def calculate_expected_revenue(quantity, price_per_unit):
    """Calculate expected revenue = quantity * price_per_unit."""
    if quantity < 0 or price_per_unit <= 0:
        return False, "Quantity must be non-negative and price must be positive.", None
    try:
        revenue = (Decimal(str(quantity)) * Decimal(str(price_per_unit))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    except Exception:
        return False, "Invalid input for revenue calculation.", None
    return True, "", revenue


def calculate_estimated_net(expected_revenue, fixed_costs):
    """Calculate estimated net = expected_revenue - fixed_costs."""
    try:
        net = (Decimal(str(expected_revenue)) - Decimal(str(fixed_costs))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    except Exception:
        return False, "Invalid input for net calculation.", None
    return True, "", net


def analyze_cycle_break_even(cycle_id, user_id, price_per_unit, expected_quantity=None):
    """Analyze break-even for a production cycle.

    Returns a dict with:
    - cycle_costs: total expenses for the cycle
    - break_even_qty: quantity needed to cover costs at given price
    - break_even_rev: revenue needed to cover costs
    - expected_rev: if expected_quantity provided
    - estimated_net: if expected_quantity provided
    """
    from database import queries

    income, expense, net, count = queries.get_cycle_totals(cycle_id, user_id)
    fixed_costs = expense  # Use recorded expenses as costs to cover

    ok, msg, be_qty = calculate_break_even_quantity(fixed_costs, price_per_unit)
    if not ok:
        return {"error": msg}

    ok, msg, be_rev = calculate_break_even_revenue(fixed_costs)
    if not ok:
        return {"error": msg}

    result = {
        "cycle_costs": fixed_costs,
        "cycle_income": income,
        "cycle_net": net,
        "cycle_count": count,
        "price_per_unit": Decimal(str(price_per_unit)),
        "break_even_quantity": be_qty,
        "break_even_revenue": be_rev,
    }

    if expected_quantity is not None and expected_quantity > 0:
        ok, msg, exp_rev = calculate_expected_revenue(expected_quantity, price_per_unit)
        if ok:
            result["expected_quantity"] = expected_quantity
            result["expected_revenue"] = exp_rev
            ok, msg, est_net = calculate_estimated_net(exp_rev, fixed_costs)
            if ok:
                result["estimated_net"] = est_net

    return result