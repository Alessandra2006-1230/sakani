"""Budget management page with budget vs actual comparison and CSV export."""

import csv
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox

import mysql.connector

from config import COLORS, CURRENCY, SPACING
from database import queries
from ui import theme
from ui.budget_dialog import BudgetDialog


def _date_text(value):
    if hasattr(value, "strftime"):
        return value.strftime("%b %d, %Y")
    return str(value)


class BudgetPage(tk.Frame):
    """User-scoped budget list with actual spending comparison."""

    def __init__(self, master, app):
        super().__init__(master, bg=COLORS["background"])
        self.app = app
        self.budgets = {}
        self._build()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _build(self):
        """Create header, action bar and a scrollable list of budget rows."""
        theme.PageHero(
            self, "Budgets",
            "Set spending limits and compare them with real expenses.",
            badge="Sakani \u00b7 Budgets", crumb="Budgets",
            on_home=lambda: self.app.open_page("dashboard")).pack(fill="x")

        scroll = theme.ScrollFrame(self, bg=COLORS["background"])
        scroll.pack(fill="both", expand=True)
        self.scroll = scroll

        self.content = tk.Frame(scroll.body, bg=COLORS["background"])
        self.content.pack(fill="both", expand=True, padx=SPACING["6"],
                          pady=SPACING["5"])

        header = tk.Frame(self.content, bg=COLORS["background"])
        header.pack(fill="x", pady=(0, SPACING["4"]))

        actions = tk.Frame(header, bg=COLORS["background"])
        actions.pack(side="right", anchor="e")
        theme.RoundedButton(actions, "Export Report",
                            command=self._export_report, width=132, height=38,
                            style="secondary",
                            parent_bg=COLORS["background"]).pack(
                                side="right", padx=(SPACING["2"], 0))
        theme.RoundedButton(actions, "Add Budget", command=self._add,
                            width=124, height=38,
                            parent_bg=COLORS["background"]).pack(side="right")

        self.list_frame = tk.Frame(self.content, bg=COLORS["background"])
        self.list_frame.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _add(self):
        """Open the create-budget dialog."""
        BudgetDialog(self, self.app, budget=None, on_saved=self._load)

    def _edit(self, budget):
        """Open the edit-budget dialog for one budget.

        The report row only carries comparison figures, so the full budget
        record is fetched before the dialog is opened.
        """
        try:
            full = queries.get_budget_by_id(budget["budget_id"],
                                            self.app.current_user["id"])
        except mysql.connector.Error as exc:
            messagebox.showerror("Database Error",
                                 "Could not load the budget.\n\n" + str(exc))
            return
        if full is None:
            messagebox.showinfo("Budget not found",
                                "This budget no longer exists. Refreshing.")
            self._load()
            return
        BudgetDialog(self, self.app, budget=full, on_saved=self._load)

    def _delete(self, budget_id):
        """Delete a budget after confirmation."""
        if not messagebox.askyesno(
                "Delete Budget",
                "Delete this budget?\n\nThis does not affect your transactions."):
            return
        try:
            queries.delete_budget(budget_id, self.app.current_user["id"])
        except mysql.connector.Error as exc:
            messagebox.showerror("Database Error",
                                 "Could not delete the budget.\n\n" + str(exc))
            return
        self._load()

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    def _load(self):
        """Reload the budget list from the database."""
        user_id = self.app.current_user["id"]
        try:
            budgets = queries.get_budget_report(user_id)
        except mysql.connector.Error as exc:
            messagebox.showerror("Database Error",
                                 "Could not load budgets.\n\n" + str(exc))
            return

        for child in list(self.list_frame.winfo_children()):
            child.destroy()
        self.budgets = {}

        if not budgets:
            self._show_empty_state()
            return

        for budget in budgets:
            self._build_budget_row(budget)

    def _show_empty_state(self):
        """Show a friendly empty state with an add action."""
        card = theme.Card(self.list_frame, padding=0)
        card.pack(fill="both", expand=True)
        theme.EmptyState(
            card.body,
            title="No budgets yet",
            message="Create a budget to track spending limits for a category "
                    "and date range.",
            icon="budgets",
            action_text="Add Your First Budget",
            action_command=self._add,
        ).pack(fill="both", expand=True, pady=SPACING["6"])

    def _build_budget_row(self, budget):
        """Create one budget row with actual vs budgeted comparison."""
        budgeted = budget["budgeted"]
        actual = budget["actual"]
        remaining = budget["remaining"]
        pct = float(budget["pct_used"])

        if budget["is_over"]:
            state = "over_budget"
            state_text = "Over budget"
            bar_color = COLORS["expense"]
        elif pct >= 80:
            state = "near_limit"
            state_text = "Near limit"
            bar_color = COLORS["warning"]
        else:
            state = "on_track"
            state_text = "Within budget"
            bar_color = COLORS["income"]

        card = tk.Frame(self.list_frame, bg=COLORS["card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1, bd=0)
        card.pack(fill="x", pady=(0, SPACING["3"]))
        inner = tk.Frame(card, bg=COLORS["card"])
        inner.pack(fill="x", padx=SPACING["5"], pady=SPACING["4"])

        # Title row
        top = tk.Frame(inner, bg=COLORS["card"])
        top.pack(fill="x")
        tk.Label(top, text=budget["name"], bg=COLORS["card"],
                 fg=COLORS["text"], font=theme.font("2xl", "bold"),
                 anchor="w", justify="left").pack(side="left")
        theme.StatusBadge(top, state, label=state_text).pack(
            side="right", anchor="n")

        # Scope and period
        scope = budget["category"] or "All expense categories"
        period = "%s · %s to %s" % (
            str(budget["period_type"]).title(),
            _date_text(budget["start_date"]),
            _date_text(budget["end_date"]))
        tk.Label(inner, text=scope, bg=COLORS["card"],
                 fg=COLORS["primary"], font=theme.font("sm"),
                 anchor="w").pack(fill="x", pady=(SPACING["1"], 0))
        tk.Label(inner, text=period, bg=COLORS["card"],
                 fg=COLORS["text_muted"], font=theme.font("xs"),
                 anchor="w").pack(fill="x")

        # Amount columns
        amounts = tk.Frame(inner, bg=COLORS["card"])
        amounts.pack(fill="x", pady=(SPACING["3"], SPACING["2"]))
        for column in range(3):
            amounts.columnconfigure(column, weight=1)

        values = [
            ("Budgeted", budgeted, COLORS["text"]),
            ("Actual expenses", actual,
             COLORS["expense"] if budget["is_over"] else COLORS["text"]),
            ("Remaining", remaining,
             COLORS["income"] if remaining >= 0 else COLORS["expense"]),
        ]
        for column, (label, value, color) in enumerate(values):
            cell = tk.Frame(amounts, bg=COLORS["card"])
            cell.grid(row=0, column=column, sticky="w")
            tk.Label(cell, text=label, bg=COLORS["card"],
                     fg=COLORS["text_muted"],
                     font=theme.font("xs")).pack(anchor="w")
            tk.Label(cell, text=CURRENCY + "{:,.2f}".format(float(value)),
                     bg=COLORS["card"], fg=color,
                     font=theme.font("xl", "bold")).pack(anchor="w")

        # Progress
        progress_row = tk.Frame(inner, bg=COLORS["card"])
        progress_row.pack(fill="x", pady=(0, SPACING["2"]))
        bar = theme.ProgressBar(progress_row, value=pct, color=bar_color,
                                height=8, bg=COLORS["card"])
        bar.pack(side="left", fill="x", expand=True)
        tk.Label(progress_row, text="%.0f%% used" % pct, bg=COLORS["card"],
                 fg=COLORS["text_secondary"], font=theme.font("xs"),
                 width=12, anchor="e").pack(side="left", padx=(SPACING["2"], 0))

        # Actions
        actions = tk.Frame(inner, bg=COLORS["card"])
        actions.pack(fill="x", pady=(SPACING["2"], 0))
        theme.RoundedButton(actions, "Edit",
                            command=lambda b=budget: self._edit(b),
                            width=72, height=32, style="secondary",
                            parent_bg=COLORS["card"]).pack(side="left")
        theme.RoundedButton(actions, "Delete",
                            command=lambda b=budget: self._delete(b["budget_id"]),
                            width=76, height=32, style="danger",
                            parent_bg=COLORS["card"]).pack(
                                side="left", padx=(SPACING["2"], 0))

        self.budgets[str(budget["budget_id"])] = budget

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def _export_report(self):
        """Export the budget vs actual report to CSV."""
        user_id = self.app.current_user["id"]
        try:
            budgets = queries.get_budget_report(user_id)
        except mysql.connector.Error as exc:
            messagebox.showerror("Database Error",
                                 "Could not load budget data.\n\n" + str(exc))
            return

        if not budgets:
            messagebox.showinfo("Export", "There are no budgets to export.")
            return

        path = filedialog.asksaveasfilename(
            title="Save budget report as CSV",
            defaultextension=".csv",
            initialfile="sakani_budget_report_%s.csv" % datetime.now().strftime("%Y%m%d"),
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.writer(handle)
                writer.writerow(["Budget Name", "Category", "Period Type",
                                 "Start Date", "End Date",
                                 "Budgeted", "Actual", "Remaining",
                                 "% Used", "Over Budget"])
                for budget in budgets:
                    writer.writerow([
                        budget["name"],
                        budget["category"] or "All Expenses",
                        str(budget["period_type"]).title(),
                        _date_text(budget["start_date"]),
                        _date_text(budget["end_date"]),
                        "%.2f" % float(budget["budgeted"]),
                        "%.2f" % float(budget["actual"]),
                        "%.2f" % float(budget["remaining"]),
                        "%.1f" % float(budget["pct_used"]),
                        "Yes" if budget["is_over"] else "No",
                    ])
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))
            return

        messagebox.showinfo("Export complete",
                            "Budget report saved to:\n%s" % path)

    def refresh(self):
        """Reload the budget list whenever the page is shown."""
        self._load()
        if hasattr(self, "scroll"):
            self.scroll.scroll_to_top()
