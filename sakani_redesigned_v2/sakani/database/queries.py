"""All SQL operations for Sakani. UI pages call these functions.

Every query uses %s placeholders. Connections and cursors are always closed.
"""

from decimal import Decimal

from database.connection import get_connection


def _run(sql, params=(), fetch=None, commit=False):
    """Run one query and return one row, all rows, or lastrowid."""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        if commit:
            connection.commit()
        if fetch == "one":
            return cursor.fetchone()
        if fetch == "all":
            return cursor.fetchall()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def create_user(full_name, email, password_hash, salt):
    """Insert a new user and return the new user id."""
    return _run(
        "INSERT INTO users (full_name, email, password_hash, salt) "
        "VALUES (%s, %s, %s, %s)",
        (full_name.strip(), email.strip().lower(), password_hash, salt),
        commit=True,
    )


def get_user_by_email(email):
    """Return the user row for an email address, or None."""
    return _run(
        "SELECT * FROM users WHERE email = %s",
        (email.strip().lower(),),
        fetch="one",
    )


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

def get_categories(transaction_type):
    """Return categories for 'income' or 'expense' (None returns all)."""
    if transaction_type:
        return _run(
            "SELECT id, name, type FROM categories WHERE type = %s ORDER BY name",
            (transaction_type,),
            fetch="all",
        )
    return _run(
        "SELECT id, name, type FROM categories ORDER BY type, name",
        fetch="all",
    )


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

def add_transaction(user_id, category_id, transaction_type, amount,
                    description, transaction_date):
    """Insert a transaction and return its id."""
    return _run(
        "INSERT INTO transactions "
        "(user_id, category_id, type, amount, description, transaction_date) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, category_id, transaction_type, amount,
         description.strip(), transaction_date),
        commit=True,
    )


def update_transaction(transaction_id, category_id, transaction_type, amount,
                       description, transaction_date, user_id=None):
    """Update an existing transaction. Optionally restrict it to one user."""
    if user_id is None:
        return _run(
            "UPDATE transactions SET category_id = %s, type = %s, amount = %s, "
            "description = %s, transaction_date = %s WHERE id = %s",
            (category_id, transaction_type, amount, description.strip(),
             transaction_date, transaction_id),
            commit=True,
        )
    return _run(
        "UPDATE transactions SET category_id = %s, type = %s, amount = %s, "
        "description = %s, transaction_date = %s "
        "WHERE id = %s AND user_id = %s",
        (category_id, transaction_type, amount, description.strip(),
         transaction_date, transaction_id, user_id),
        commit=True,
    )


def delete_transaction(transaction_id, user_id=None):
    """Delete a transaction. Optionally restrict it to one user."""
    if user_id is None:
        return _run(
            "DELETE FROM transactions WHERE id = %s",
            (transaction_id,),
            commit=True,
        )
    return _run(
        "DELETE FROM transactions WHERE id = %s AND user_id = %s",
        (transaction_id, user_id),
        commit=True,
    )


def get_transactions(user_id, transaction_type=None, search=None,
                     start=None, end=None):
    """Return filtered transactions for one user, newest first."""
    sql = (
        "SELECT t.id, t.transaction_date, t.type, c.name AS category, "
        "t.description, t.amount, t.category_id "
        "FROM transactions t "
        "JOIN categories c ON c.id = t.category_id "
        "WHERE t.user_id = %s"
    )
    params = [user_id]
    if transaction_type:
        sql += " AND t.type = %s"
        params.append(transaction_type)
    if search:
        sql += " AND (c.name LIKE %s OR t.description LIKE %s)"
        pattern = "%" + search.strip() + "%"
        params.extend([pattern, pattern])
    if start:
        sql += " AND t.transaction_date >= %s"
        params.append(start)
    if end:
        sql += " AND t.transaction_date <= %s"
        params.append(end)
    sql += " ORDER BY t.transaction_date DESC, t.id DESC"
    return _run(sql, tuple(params), fetch="all")


# ---------------------------------------------------------------------------
# Summary numbers
# ---------------------------------------------------------------------------

def get_totals(user_id, start=None, end=None):
    """Return (total_income, total_expense, net_income, transaction_count).

    Amounts are Decimal values to keep financial math exact. Optional
    ``start``/``end`` date bounds (inclusive) scope the totals.
    """
    sql = (
        "SELECT "
        "COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) "
        "AS income, "
        "COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) "
        "AS expense, "
        "COUNT(*) AS total_count "
        "FROM transactions WHERE user_id = %s"
    )
    params = [user_id]
    if start:
        sql += " AND transaction_date >= %s"
        params.append(start)
    if end:
        sql += " AND transaction_date <= %s"
        params.append(end)
    row = _run(sql, tuple(params), fetch="one")
    income = Decimal(row["income"]) if row and row["income"] is not None else Decimal("0")
    expense = Decimal(row["expense"]) if row and row["expense"] is not None else Decimal("0")
    net = income - expense
    count = int(row["total_count"]) if row and row["total_count"] is not None else 0
    return income, expense, net, count


def get_monthly_summary(user_id, year):
    """Return 12 monthly rows (month, income, expense, net) for a year."""
    rows = _run(
        "SELECT MONTH(transaction_date) AS month, "
        "SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS income, "
        "SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS expense "
        "FROM transactions "
        "WHERE user_id = %s AND YEAR(transaction_date) = %s "
        "GROUP BY MONTH(transaction_date)",
        (user_id, int(year)),
        fetch="all",
    )
    found = {int(row["month"]): row for row in rows}
    summary = []
    for month in range(1, 13):
        row = found.get(month)
        income = Decimal(row["income"]) if row and row["income"] is not None else Decimal("0")
        expense = Decimal(row["expense"]) if row and row["expense"] is not None else Decimal("0")
        summary.append({
            "month": month,
            "income": income,
            "expense": expense,
            "net": income - expense,
        })
    return summary


def get_monthly_summary_range(user_id, start=None, end=None):
    """Return monthly rows (month, income, expense, net) within a date range.

    ``start``/``end`` are inclusive transaction dates. If either is None the
    corresponding bound is omitted (useful for "all time").
    """
    sql = (
        "SELECT YEAR(transaction_date) AS yr, MONTH(transaction_date) AS month, "
        "SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS income, "
        "SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS expense "
        "FROM transactions "
        "WHERE user_id = %s"
    )
    params = [user_id]
    if start:
        sql += " AND transaction_date >= %s"
        params.append(start)
    if end:
        sql += " AND transaction_date <= %s"
        params.append(end)
    sql += " GROUP BY YEAR(transaction_date), MONTH(transaction_date) ORDER BY yr, month"
    rows = _run(sql, tuple(params), fetch="all")
    summary = []
    for row in rows:
        income = Decimal(row["income"]) if row["income"] is not None else Decimal("0")
        expense = Decimal(row["expense"]) if row["expense"] is not None else Decimal("0")
        summary.append({
            "month": int(row["month"]),
            "year": int(row["yr"]) if row.get("yr") is not None else None,
            "income": income,
            "expense": expense,
            "net": income - expense,
        })
    # Zero-fill months between start and end if bounded and sparse
    if summary and start and end:
        try:
            import calendar
            from datetime import date
            # determine range
            s_m = date(start.year, start.month, 1)
            e_m = date(end.year, end.month, 1)
            filled = []
            cur = s_m
            by_key = {(r.get('year') or start.year, r['month']): r for r in summary}
            while cur <= e_m:
                key = (cur.year, cur.month)
                if key in by_key:
                    filled.append({**by_key[key], 'year': cur.year, 'month': cur.month})
                else:
                    filled.append({'year': cur.year, 'month': cur.month, 'income': Decimal('0'), 'expense': Decimal('0'), 'net': Decimal('0')})
                if cur.month == 12:
                    cur = date(cur.year + 1, 1, 1)
                else:
                    cur = date(cur.year, cur.month + 1, 1)
            summary = filled
        except Exception:
            pass
    return summary


def get_daily_summary_range(user_id, start=None, end=None):
    """Return daily rows (date, income, expense, net) within a date range."""
    sql = (
        "SELECT transaction_date AS d, "
        "SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS income, "
        "SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS expense "
        "FROM transactions "
        "WHERE user_id = %s"
    )
    params = [user_id]
    if start:
        sql += " AND transaction_date >= %s"
        params.append(start)
    if end:
        sql += " AND transaction_date <= %s"
        params.append(end)
    sql += " GROUP BY transaction_date ORDER BY transaction_date"
    rows = _run(sql, tuple(params), fetch="all")
    summary = []
    for row in rows:
        income = Decimal(row["income"]) if row["income"] is not None else Decimal("0")
        expense = Decimal(row["expense"]) if row["expense"] is not None else Decimal("0")
        d = row["d"]
        summary.append({
            "date": d,
            "income": income,
            "expense": expense,
            "net": income - expense,
        })
    # Zero-fill between first and last if range is bounded
    if summary and start and end:
        try:
            from datetime import timedelta
            filled = []
            by_date = {r["date"]: r for r in summary}
            cur = start
            while cur <= end:
                if cur in by_date:
                    filled.append(by_date[cur])
                else:
                    filled.append({"date": cur, "income": Decimal("0"), "expense": Decimal("0"), "net": Decimal("0")})
                cur = cur + timedelta(days=1)
            summary = filled
        except Exception:
            pass
    return summary


def get_category_breakdown_range(user_id, transaction_type, start=None, end=None):
    """Return category totals for income or expense within a date range."""
    sql = (
        "SELECT c.name AS category, SUM(t.amount) AS total "
        "FROM transactions t "
        "JOIN categories c ON c.id = t.category_id "
        "WHERE t.user_id = %s AND t.type = %s"
    )
    params = [user_id, transaction_type]
    if start:
        sql += " AND t.transaction_date >= %s"
        params.append(start)
    if end:
        sql += " AND t.transaction_date <= %s"
        params.append(end)
    sql += " GROUP BY c.name ORDER BY total DESC"
    rows = _run(sql, tuple(params), fetch="all")
    return [
        {"category": row["category"], "total": Decimal(row["total"]) if row["total"] is not None else Decimal("0")}
        for row in rows
    ]


def get_category_breakdown(user_id, transaction_type, year=None):
    """Return category totals for income or expense, largest first."""
    sql = (
        "SELECT c.name AS category, SUM(t.amount) AS total "
        "FROM transactions t "
        "JOIN categories c ON c.id = t.category_id "
        "WHERE t.user_id = %s AND t.type = %s"
    )
    params = [user_id, transaction_type]
    if year:
        sql += " AND YEAR(t.transaction_date) = %s"
        params.append(int(year))
    sql += " GROUP BY c.name ORDER BY total DESC"
    rows = _run(sql, tuple(params), fetch="all")
    return [
        {"category": row["category"], "total": Decimal(row["total"]) if row["total"] is not None else Decimal("0")}
        for row in rows
    ]


def get_available_years(user_id):
    """Return the years that contain transactions, newest first."""
    rows = _run(
        "SELECT DISTINCT YEAR(transaction_date) AS year FROM transactions "
        "WHERE user_id = %s ORDER BY year DESC",
        (user_id,),
        fetch="all",
    )
    return [int(row["year"]) for row in rows]


def get_recent_transactions(user_id, limit=5):
    """Return the latest few transactions for the dashboard."""
    limit = max(1, min(int(limit), 50))
    return _run(
        "SELECT t.id, t.transaction_date, t.type, c.name AS category, "
        "t.description, t.amount, t.category_id, t.production_cycle_id "
        "FROM transactions t "
        "JOIN categories c ON c.id = t.category_id "
        "WHERE t.user_id = %s "
        "ORDER BY t.transaction_date DESC, t.id DESC LIMIT %s",
        (user_id, limit),
        fetch="all",
    )


# ---------------------------------------------------------------------------
# Production cycles
# ---------------------------------------------------------------------------

CYCLE_COLUMNS = (
    "id, user_id, crop_name, variety, plot_name, start_date, "
    "expected_harvest_date, actual_harvest_date, status, notes"
)


def get_cycles(user_id, status=None):
    """Return production cycles for one user, newest first."""
    sql = "SELECT " + CYCLE_COLUMNS + " FROM production_cycles WHERE user_id = %s"
    params = [user_id]
    if status:
        sql += " AND status = %s"
        params.append(status)
    sql += " ORDER BY start_date DESC, id DESC"
    return _run(sql, tuple(params), fetch="all")


def get_cycle_by_id(cycle_id, user_id):
    """Return one production cycle owned by the user, or None."""
    return _run(
        "SELECT " + CYCLE_COLUMNS + " FROM production_cycles "
        "WHERE id = %s AND user_id = %s",
        (cycle_id, user_id),
        fetch="one",
    )


def add_cycle(user_id, crop_name, variety, plot_name, start_date,
              expected_harvest_date, actual_harvest_date, status, notes):
    """Insert a new production cycle and return its id."""
    return _run(
        "INSERT INTO production_cycles "
        "(user_id, crop_name, variety, plot_name, start_date, "
        " expected_harvest_date, actual_harvest_date, status, notes) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (user_id, crop_name.strip(), variety, plot_name, start_date,
         expected_harvest_date, actual_harvest_date, status, notes),
        commit=True,
    )


def update_cycle(cycle_id, user_id, crop_name, variety, plot_name, start_date,
                 expected_harvest_date, actual_harvest_date, status, notes):
    """Update one production cycle owned by the user."""
    return _run(
        "UPDATE production_cycles SET crop_name = %s, variety = %s, "
        "plot_name = %s, start_date = %s, expected_harvest_date = %s, "
        "actual_harvest_date = %s, status = %s, notes = %s "
        "WHERE id = %s AND user_id = %s",
        (crop_name.strip(), variety, plot_name, start_date,
         expected_harvest_date, actual_harvest_date, status, notes,
         cycle_id, user_id),
        commit=True,
    )


def delete_cycle(cycle_id, user_id):
    """Delete one production cycle owned by the user (linked transactions "
    "keep their production_cycle_id cleared via ON DELETE SET NULL)."""
    return _run(
        "DELETE FROM production_cycles WHERE id = %s AND user_id = %s",
        (cycle_id, user_id),
        commit=True,
    )


def link_transaction_to_cycle(transaction_id, cycle_id, user_id):
    """Assign a transaction to a production cycle owned by the user."""
    return _run(
        "UPDATE transactions SET production_cycle_id = %s "
        "WHERE id = %s AND user_id = %s",
        (cycle_id, transaction_id, user_id),
        commit=True,
    )


def unlink_transaction_from_cycle(transaction_id, user_id):
    """Clear the production cycle link of a transaction owned by the user."""
    return _run(
        "UPDATE transactions SET production_cycle_id = NULL "
        "WHERE id = %s AND user_id = %s",
        (transaction_id, user_id),
        commit=True,
    )


def get_cycle_transactions(user_id, cycle_id):
    """Return the transactions assigned to one of the user's cycles."""
    return _run(
        "SELECT t.id, t.transaction_date, t.type, c.name AS category, "
        "t.description, t.amount, t.category_id, t.production_cycle_id "
        "FROM transactions t "
        "JOIN categories c ON c.id = t.category_id "
        "WHERE t.user_id = %s AND t.production_cycle_id = %s "
        "ORDER BY t.transaction_date DESC, t.id DESC",
        (user_id, cycle_id),
        fetch="all",
    )


def get_cycle_totals(cycle_id, user_id):
    """Return (income, expense, net, count) for one of the user's cycles."""
    rows = get_cycle_transactions(user_id, cycle_id)
    income = Decimal("0")
    expense = Decimal("0")
    for row in rows:
        if str(row["type"]).lower() == "income":
            income += Decimal(str(row["amount"]))
        else:
            expense += Decimal(str(row["amount"]))
    return income, expense, income - expense, len(rows)


# ---------------------------------------------------------------------------
# Budgets
# ---------------------------------------------------------------------------

BUDGET_COLUMNS = (
    "id, user_id, name, category_id, amount, period_type, "
    "start_date, end_date, notes, created_at, updated_at"
)


def get_budgets(user_id):
    """Return all budgets for one user, newest first."""
    return _run(
        "SELECT " + BUDGET_COLUMNS + " FROM budgets WHERE user_id = %s "
        "ORDER BY created_at DESC, id DESC",
        (user_id,),
        fetch="all",
    )


def get_budget_by_id(budget_id, user_id):
    """Return one budget owned by the user, or None."""
    return _run(
        "SELECT " + BUDGET_COLUMNS + " FROM budgets WHERE id = %s AND user_id = %s",
        (budget_id, user_id),
        fetch="one",
    )


def add_budget(user_id, name, category_id, amount, period_type, start_date, end_date, notes):
    """Insert a new budget and return its id."""
    return _run(
        "INSERT INTO budgets "
        "(user_id, name, category_id, amount, period_type, start_date, end_date, notes) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (user_id, name.strip(), category_id, amount, period_type, start_date, end_date, notes),
        commit=True,
    )


def update_budget(budget_id, user_id, name, category_id, amount, period_type, start_date, end_date, notes):
    """Update one budget owned by the user."""
    return _run(
        "UPDATE budgets SET name = %s, category_id = %s, amount = %s, period_type = %s, "
        "start_date = %s, end_date = %s, notes = %s "
        "WHERE id = %s AND user_id = %s",
        (name.strip(), category_id, amount, period_type, start_date, end_date, notes,
         budget_id, user_id),
        commit=True,
    )


def delete_budget(budget_id, user_id):
    """Delete one budget owned by the user."""
    return _run(
        "DELETE FROM budgets WHERE id = %s AND user_id = %s",
        (budget_id, user_id),
        commit=True,
    )


def get_budget_actual(budget_id, user_id):
    """Return actual expense for a budget based on its category and date range."""
    budget = get_budget_by_id(budget_id, user_id)
    if not budget:
        return Decimal("0")
    if budget["category_id"] is None:
        # Category-specific budgets only; return 0 for unassigned
        return Decimal("0")
    rows = _run(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM transactions "
        "WHERE user_id = %s AND type = 'expense' AND category_id = %s "
        "AND transaction_date BETWEEN %s AND %s",
        (user_id, budget["category_id"], budget["start_date"], budget["end_date"]),
        fetch="one",
    )
    return Decimal(rows["total"]) if rows and rows["total"] is not None else Decimal("0")


def get_budget_report(user_id):
    """Return a list of budgets with actual spending and variance for the user."""
    budgets = get_budgets(user_id)
    report = []
    for b in budgets:
        actual = get_budget_actual(b["id"], user_id)
        budgeted = Decimal(str(b["amount"]))
        remaining = budgeted - actual
        pct = (actual / budgeted * Decimal("100")) if budgeted > 0 else Decimal("0")
        is_over = actual > budgeted
        category_name = None
        if b["category_id"] is not None:
            cat = _run(
                "SELECT name FROM categories WHERE id = %s",
                (b["category_id"],),
                fetch="one",
            )
            category_name = cat["name"] if cat else "Unknown"
        report.append({
            "budget_id": b["id"],
            "name": b["name"],
            "category": category_name,
            "budgeted": budgeted,
            "actual": actual,
            "remaining": remaining,
            "pct_used": pct,
            "is_over": is_over,
            "period_type": b["period_type"],
            "start_date": b["start_date"],
            "end_date": b["end_date"],
        })
    return report
