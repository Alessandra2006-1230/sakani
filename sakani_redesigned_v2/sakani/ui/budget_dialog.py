"""Modal dialog used to create and edit a budget."""

import tkinter as tk
from tkinter import ttk

import mysql.connector

from config import COLORS, CURRENCY, SPACING
from database import queries
from models import budget as budget_model
from ui import theme

NO_CATEGORY = "All expense categories"
PERIOD_LABELS = {
    "monthly": "Monthly",
    "quarterly": "Quarterly",
    "yearly": "Yearly",
    "custom": "Custom range",
}


class BudgetDialog(tk.Toplevel):
    """Modal window that creates or edits a budget."""

    def __init__(self, master, app, budget=None, on_saved=None):
        super().__init__(master)
        self.app = app
        self.budget = budget
        self.on_saved = on_saved
        self.category_map = {}
        self.category_var = tk.StringVar(value=NO_CATEGORY)
        self.period_var = tk.StringVar(value="Monthly")

        self.title("Add Budget" if budget is None else "Edit Budget")
        self.configure(bg=COLORS["card"])
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self._build()
        self._load_categories()
        if budget is not None:
            self._load_values()
        theme.center_window(self, master)
        self.bind("<Escape>", lambda _event: self.destroy())
        self.name_entry.focus()

    def _build(self):
        """Create the budget form inside the dialog."""
        container = tk.Frame(self, bg=COLORS["card"])
        container.pack(fill="both", expand=True, padx=SPACING["6"],
                       pady=SPACING["5"])

        tk.Label(container, text="Add Budget" if self.budget is None
                 else "Edit Budget", bg=COLORS["card"], fg=COLORS["text"],
                 font=theme.font("3xl", "bold")).pack(anchor="w")
        tk.Label(container,
                 text="Set a spending limit for a category and date range.",
                 bg=COLORS["card"], fg=COLORS["text_secondary"],
                 font=theme.font("sm")).pack(anchor="w",
                                              pady=(SPACING["1"], SPACING["4"]))

        self.name_entry = theme.LabeledEntry(
            container, "Budget name", required=True)
        self.name_entry.pack(fill="x", pady=(0, SPACING["2"]))

        row = tk.Frame(container, bg=COLORS["card"])
        row.pack(fill="x", pady=(0, SPACING["2"]))
        category_box = tk.Frame(row, bg=COLORS["card"])
        category_box.pack(side="left", fill="x", expand=True,
                          padx=(0, SPACING["2"]))
        tk.Label(category_box, text="Category", bg=COLORS["card"],
                 fg=COLORS["text"], font=theme.font("sm")).pack(
                     anchor="w", pady=(0, SPACING["1"]))
        self.category_combo = ttk.Combobox(
            category_box, textvariable=self.category_var, state="readonly",
            font=theme.font("base"))
        self.category_combo.pack(fill="x")

        period_box = tk.Frame(row, bg=COLORS["card"])
        period_box.pack(side="left", fill="x", expand=True)
        tk.Label(period_box, text="Period", bg=COLORS["card"],
                 fg=COLORS["text"], font=theme.font("sm")).pack(
                     anchor="w", pady=(0, SPACING["1"]))
        self.period_combo = ttk.Combobox(
            period_box, textvariable=self.period_var, state="readonly",
            values=[PERIOD_LABELS[p] for p in budget_model.BUDGET_PERIODS],
            font=theme.font("base"))
        self.period_combo.pack(fill="x")

        amount_row = tk.Frame(container, bg=COLORS["card"])
        amount_row.pack(fill="x", pady=(SPACING["2"], SPACING["2"]))
        self.amount = theme.LabeledEntry(
            amount_row, "Amount (%s)" % CURRENCY, required=True)
        self.amount.pack(fill="x")

        tk.Label(container, text="Date range", bg=COLORS["card"],
                 fg=COLORS["text_muted"],
                 font=theme.font("xs")).pack(anchor="w",
                                              pady=(SPACING["2"], 0))
        row = tk.Frame(container, bg=COLORS["card"])
        row.pack(fill="x", pady=(SPACING["1"], SPACING["2"]))
        self.start_date = theme.LabeledEntry(
            row, "Start date", required=True, hint="YYYY-MM-DD")
        self.start_date.pack(side="left", fill="x", expand=True,
                             padx=(0, SPACING["2"]))
        self.end_date = theme.LabeledEntry(
            row, "End date", required=True, hint="YYYY-MM-DD")
        self.end_date.pack(side="left", fill="x", expand=True)

        self.notes = theme.LabeledEntry(container, "Notes")
        self.notes.pack(fill="x", pady=(SPACING["2"], 0))

        self.error_label = tk.Label(
            container, text="", bg=COLORS["card"], fg=COLORS["danger"],
            font=theme.font("sm"), justify="left", wraplength=460, anchor="w")
        self.error_label.pack(fill="x", pady=(SPACING["2"], 0))

        buttons = tk.Frame(container, bg=COLORS["card"])
        buttons.pack(fill="x", pady=(SPACING["4"], 0))
        theme.RoundedButton(buttons, "Cancel", command=self.destroy,
                            width=96, height=36, style="secondary",
                            parent_bg=COLORS["card"]).pack(side="right")
        theme.RoundedButton(buttons, "Save Budget", command=self._save,
                            width=136, height=36,
                            parent_bg=COLORS["card"]).pack(
                                side="right", padx=(0, SPACING["2"]))

    def _load_categories(self):
        """Load expense categories for the budget."""
        try:
            categories = queries.get_categories("expense")
        except mysql.connector.Error:
            categories = []
        self.category_map = {item["name"]: item["id"] for item in categories}
        self.category_combo["values"] = [NO_CATEGORY] + list(self.category_map)
        if self.category_var.get() not in self.category_combo["values"]:
            self.category_var.set(NO_CATEGORY)

    def _load_values(self):
        """Fill the form from an existing budget."""
        self.name_entry.set(self.budget["name"] or "")
        self.amount.set("%.2f" % float(self.budget["amount"]))
        self.period_var.set(PERIOD_LABELS.get(self.budget["period_type"],
                                              "Monthly"))
        self.start_date.set(self._as_date_text(self.budget["start_date"]))
        self.end_date.set(self._as_date_text(self.budget["end_date"]))
        self.notes.set(self.budget["notes"] or "")
        category_id = self.budget["category_id"]
        if category_id is None:
            self.category_var.set(NO_CATEGORY)
        else:
            for name, cid in self.category_map.items():
                if cid == category_id:
                    self.category_var.set(name)
                    break

    @staticmethod
    def _as_date_text(value):
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d")
        return str(value)

    def _save(self):
        """Validate the form and save the budget."""
        category_name = self.category_var.get()
        category_id = self.category_map.get(category_name)

        period = None
        for key, label in PERIOD_LABELS.items():
            if label == self.period_var.get():
                period = key
                break

        exclude_id = int(self.budget["id"]) if self.budget is not None else None

        ok, message, values = budget_model.validate_budget({
            "name": self.name_entry.get(),
            "amount": self.amount.get(),
            "period_type": period or "",
            "start_date": self.start_date.get(),
            "end_date": self.end_date.get(),
            "notes": self.notes.get(),
            "category_id": category_id,
        }, user_id=self.app.current_user["id"], exclude_id=exclude_id)
        if not ok:
            self.error_label.config(text=message)
            return

        try:
            if self.budget is None:
                queries.add_budget(
                    self.app.current_user["id"], values["name"], category_id,
                    values["amount"], values["period_type"],
                    values["start_date"], values["end_date"], values["notes"],
                )
            else:
                queries.update_budget(
                    int(self.budget["id"]), self.app.current_user["id"],
                    values["name"], category_id, values["amount"],
                    values["period_type"], values["start_date"],
                    values["end_date"], values["notes"],
                )
        except mysql.connector.Error as exc:
            message = str(exc).lower()
            if "overlapping" in message or "45000" in message:
                self.error_label.config(
                    text="A budget already exists for this category and "
                         "overlapping date range.")
            else:
                self.error_label.config(
                    text="Could not save the budget. Please try again.")
            return

        if callable(self.on_saved):
            self.on_saved()
        self.destroy()
