"""CSV export for transaction history and financial summaries. Works fully offline."""

import csv

HEADERS = ["Date", "Type", "Category", "Description", "Amount"]
SUMMARY_HEADERS = ["Period", "Income", "Expense", "Net"]
CATEGORY_HEADERS = ["Category", "Total"]


def export_transactions_csv(rows, filepath):
    """Write transaction rows (list of dicts) to a CSV file.

    Returns the number of rows written. Uses utf-8-sig so Excel opens it
    with the correct characters.
    """
    with open(filepath, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADERS)
        for row in rows:
            writer.writerow([
                row["transaction_date"],
                str(row["type"]).title(),
                row["category"],
                row.get("description") or "",
                "%.2f" % float(row["amount"]),
            ])
    return len(rows)


def export_summary_csv(monthly_rows, expense_breakdown, income_breakdown,
                       total_income, total_expense, net, filepath):
    """Write a financial summary CSV with monthly totals and category breakdowns.

    Args:
        monthly_rows: list of dicts with keys month, income, expense, net
        expense_breakdown: list of dicts with keys category, total
        income_breakdown: list of dicts with keys category, total
        total_income, total_expense, net: Decimal or float totals
        filepath: output file path

    Returns the number of data rows written (excluding header/total rows).
    """
    import calendar
    with open(filepath, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)

        # Monthly totals section
        writer.writerow(["Monthly Totals"])
        writer.writerow(SUMMARY_HEADERS)
        count = 0
        for row in monthly_rows:
            writer.writerow([
                calendar.month_name[row["month"]],
                "%.2f" % float(row["income"]),
                "%.2f" % float(row["expense"]),
                "%.2f" % float(row["net"]),
            ])
            count += 1

        # Totals row
        writer.writerow([
            "TOTAL",
            "%.2f" % float(total_income),
            "%.2f" % float(total_expense),
            "%.2f" % float(net),
        ])

        writer.writerow([])  # blank row

        # Expense by category
        writer.writerow(["Expenses by Category"])
        writer.writerow(CATEGORY_HEADERS)
        for row in expense_breakdown:
            writer.writerow([row["category"], "%.2f" % float(row["total"])])
            count += 1

        writer.writerow([])  # blank row

        # Income by category
        writer.writerow(["Income by Category"])
        writer.writerow(CATEGORY_HEADERS)
        for row in income_breakdown:
            writer.writerow([row["category"], "%.2f" % float(row["total"])])
            count += 1

    return count
