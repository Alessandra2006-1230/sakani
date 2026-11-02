"""Modal dialog used by the History page to edit a transaction."""

import tkinter as tk
from tkinter import messagebox, ttk

import mysql.connector

from config import COLORS, CURRENCY, SPACING
from database import queries
from models import validators
from ui import theme

NO_CYCLE = "No production cycle"


class EditTransactionDialog(tk.Toplevel):
    """Small modal window that updates one existing transaction."""

    def __init__(self, master, app, row, on_saved=None):
        super().__init__(master)
        self.app = app
        self.row = row
        self.on_saved = on_saved
        self.category_map = {}
        self.cycle_map = {}
        self.type_var = tk.StringVar(value=row["type"])
        self.cycle_var = tk.StringVar(value=NO_CYCLE)
        self.type_buttons = {}

        self.title("Edit Transaction")
        self.configure(bg=COLORS["card"])
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self._build()
        self._load_categories(row.get("category"))
        self._load_cycles()
        self._refresh_type_buttons()
        theme.center_window(self, master)
        self.bind("<Escape>", lambda _event: self.destroy())
        self.amount.focus()

    def _build(self):
        """Create the edit form inside the dialog."""
        container = tk.Frame(self, bg=COLORS["card"])
        container.pack(fill="both", expand=True, padx=SPACING["6"],
                       pady=SPACING["5"])

        tk.Label(container, text="Edit Transaction", bg=COLORS["card"],
                 fg=COLORS["text"],
                 font=theme.font("3xl", "bold")).pack(anchor="w")
        tk.Label(container, text="Update the details and save your changes.",
                 bg=COLORS["card"], fg=COLORS["text_secondary"],
                 font=theme.font("sm")).pack(anchor="w",
                                              pady=(SPACING["1"], SPACING["3"]))

        tk.Label(container, text="Type", bg=COLORS["card"],
                 fg=COLORS["text_muted"],
                 font=theme.font("xs")).pack(anchor="w")
        toggle = tk.Frame(container, bg=COLORS["card"])
        toggle.pack(anchor="w", pady=(SPACING["1"], SPACING["3"]))
        for value, label in (("income", "Income"), ("expense", "Expense")):
            button = theme.RoundedButton(
                toggle, label,
                command=lambda v=value: self._set_type(v),
                width=104, height=34, style="secondary",
                parent_bg=COLORS["card"])
            button.pack(side="left", padx=(0, SPACING["2"]))
            self.type_buttons[value] = button

        category_box = tk.Frame(container, bg=COLORS["card"])
        category_box.pack(fill="x", pady=(0, SPACING["2"]))
        tk.Label(category_box, text="Category", bg=COLORS["card"],
                 fg=COLORS["text"], font=theme.font("sm")).pack(
                     anchor="w", pady=(0, SPACING["1"]))
        self.category_combo = ttk.Combobox(category_box, state="readonly",
                                           font=theme.font("base"))
        self.category_combo.pack(fill="x")

        row = tk.Frame(container, bg=COLORS["card"])
        row.pack(fill="x", pady=(0, SPACING["2"]))
        self.amount = theme.LabeledEntry(row, "Amount (%s)" % CURRENCY,
                                         required=True)
        self.amount.pack(side="left", fill="x", expand=True,
                         padx=(0, SPACING["2"]))
        self.date = theme.LabeledEntry(row, "Date", required=True,
                                       hint="YYYY-MM-DD")
        self.date.pack(side="left", fill="x", expand=True)

        self.description = theme.LabeledEntry(container,
                                              "Description (optional)")
        self.description.pack(fill="x", pady=(0, SPACING["2"]))

        cycle_box = tk.Frame(container, bg=COLORS["card"])
        cycle_box.pack(fill="x", pady=(0, SPACING["2"]))
        tk.Label(cycle_box, text="Production cycle (optional)",
                 bg=COLORS["card"], fg=COLORS["text"],
                 font=theme.font("sm")).pack(anchor="w",
                                              pady=(0, SPACING["1"]))
        self.cycle_combo = ttk.Combobox(cycle_box, textvariable=self.cycle_var,
                                        state="readonly",
                                        font=theme.font("base"))
        self.cycle_combo.pack(fill="x")
        tk.Label(cycle_box,
                 text="Linking a record includes it in that crop cycle's totals.",
                 bg=COLORS["card"], fg=COLORS["text_muted"],
                 font=theme.font("xs")).pack(anchor="w", pady=(2, 0))

        self.error_label = tk.Label(
            container, text="", bg=COLORS["card"], fg=COLORS["danger"],
            font=theme.font("sm"), justify="left", wraplength=420, anchor="w")
        self.error_label.pack(fill="x", pady=(SPACING["2"], 0))

        buttons = tk.Frame(container, bg=COLORS["card"])
        buttons.pack(fill="x", pady=(SPACING["4"], 0))
        theme.RoundedButton(buttons, "Cancel", command=self.destroy,
                            width=96, height=36, style="secondary",
                            parent_bg=COLORS["card"]).pack(side="right")
        theme.RoundedButton(buttons, "Save Changes", command=self._save,
                            width=140, height=36,
                            parent_bg=COLORS["card"]).pack(
                                side="right", padx=(0, SPACING["2"]))

        self.amount.set("%.2f" % float(self.row["amount"]))
        self.date.set(self._as_date_text(self.row["transaction_date"]))
        self.description.set(self.row.get("description") or "")
        self.amount.entry.bind("<Return>", lambda _event: self._save())
        self.date.entry.bind("<Return>", lambda _event: self._save())

    @staticmethod
    def _as_date_text(value):
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d")
        return str(value)

    def _set_type(self, value):
        if self.type_var.get() == value:
            return
        self.type_var.set(value)
        self._refresh_type_buttons()
        self._load_categories()

    def _refresh_type_buttons(self):
        selected = self.type_var.get()
        for value, button in self.type_buttons.items():
            button.set_style("primary" if value == selected else "secondary")

    def _load_cycles(self):
        """Load the user's production cycles for the link selector."""
        try:
            cycles = queries.get_cycles(self.app.current_user["id"])
        except mysql.connector.Error as exc:
            self.error_label.config(text="Could not load cycles: " + str(exc))
            cycles = []

        self.cycle_map = {}
        labels = [NO_CYCLE]
        for cycle in sorted(cycles, key=lambda item: item["id"]):
            label = "%s · %s" % (cycle["crop_name"], cycle["status"])
            # Disambiguate duplicate crop names by appending the id.
            if label in self.cycle_map:
                label = "%s #%d" % (label, cycle["id"])
            self.cycle_map[label] = cycle["id"]
            labels.append(label)
        self.cycle_combo["values"] = labels

        current_id = self.row.get("production_cycle_id")
        selected = NO_CYCLE
        if current_id is not None:
            for label, cycle_id in self.cycle_map.items():
                if int(cycle_id) == int(current_id):
                    selected = label
                    break
        self.cycle_var.set(selected)

    def _load_categories(self, selected=None):
        """Reload the dropdown for the chosen type and select a value."""
        try:
            categories = queries.get_categories(self.type_var.get())
        except mysql.connector.Error as exc:
            self.error_label.config(text="Could not load categories: " + str(exc))
            return

        self.category_map = {item["name"]: item["id"] for item in categories}
        names = [item["name"] for item in categories]
        self.category_combo["values"] = names
        if selected in names:
            self.category_combo.set(selected)
        elif names:
            self.category_combo.current(0)
        else:
            self.category_combo.set("")

    def _save(self):
        """Validate the fields and update the transaction."""
        category_name = self.category_combo.get().strip()
        if category_name not in self.category_map:
            self.error_label.config(text="Please choose a category.")
            return

        ok, result, amount = validators.validate_amount(self.amount.get())
        if not ok:
            self.error_label.config(text=result)
            return

        ok, transaction_date = validators.validate_transaction_date(
            self.date.get())
        if not ok:
            self.error_label.config(text=transaction_date)
            return

        ok, description = validators.validate_description(self.description.get())
        if not ok:
            self.error_label.config(text=description)
            return

        cycle_label = self.cycle_var.get()
        cycle_id = self.cycle_map.get(cycle_label)

        try:
            if cycle_id is not None:
                queries.link_transaction_to_cycle(
                    int(self.row["id"]), int(cycle_id),
                    self.app.current_user["id"])
            else:
                queries.unlink_transaction_from_cycle(
                    int(self.row["id"]), self.app.current_user["id"])
            queries.update_transaction(
                int(self.row["id"]),
                self.category_map[category_name],
                self.type_var.get(),
                amount,
                description,
                transaction_date,
                user_id=self.app.current_user["id"],
            )
        except mysql.connector.Error as exc:
            messagebox.showerror("Database Error",
                                 "Could not update the transaction.\n\n" + str(exc))
            return

        messagebox.showinfo("Updated", "Transaction updated successfully.")
        if callable(self.on_saved):
            self.on_saved()
        self.destroy()
