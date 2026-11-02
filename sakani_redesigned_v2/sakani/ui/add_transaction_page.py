"""Add Transaction page: record farm income or expenses."""

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

import mysql.connector

from config import COLORS, CURRENCY, SPACING
from database import queries
from models import validators
from ui import theme


class AddTransactionPage(tk.Frame):
    """Form for saving a new income or expense transaction."""

    def __init__(self, master, app):
        super().__init__(master, bg=COLORS["background"])
        self.app = app
        self.type_var = tk.StringVar(value="income")
        self.category_map = {}
        self.type_buttons = {}
        self._columns = 0
        self._resize_job = None
        self._build()
        self.bind("<Configure>", self._on_resize)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _build(self):
        """Create the header, form card and live preview panel."""
        theme.PageHero(
            self, "Add Transaction",
            "Record money earned or spent on your farm.",
            badge="Sakani \u00b7 Transactions", crumb="Add Transaction",
            on_home=lambda: self.app.open_page("dashboard")).pack(fill="x")

        scroll = theme.ScrollFrame(self, bg=COLORS["background"])
        scroll.pack(fill="both", expand=True)
        self.scroll = scroll

        wrapper = tk.Frame(scroll.body, bg=COLORS["background"])
        wrapper.pack(fill="both", expand=True, padx=SPACING["6"],
                     pady=SPACING["5"])

        self.grid_area = tk.Frame(wrapper, bg=COLORS["background"])
        self.grid_area.pack(fill="both", expand=True)

        self.form_card = theme.Card(self.grid_area, padding=SPACING["5"])
        self._build_form(self.form_card.body)

        side = tk.Frame(self.grid_area, bg=COLORS["background"])
        self.side = side
        self._build_preview(side)
        self._build_tips(side)

        for field in (self.amount, self.date, self.description):
            field.entry.bind("<Return>", lambda _event: self._save())

        self.date.set(datetime.now().strftime("%Y-%m-%d"))
        self._sync_preview()

    def _build_form(self, body):
        """Build the form fields inside the white card."""
        tk.Label(body, text="Transaction type", bg=COLORS["card"],
                 fg=COLORS["text_muted"], font=theme.font("xs")).pack(anchor="w")

        toggle = tk.Frame(body, bg=COLORS["card"])
        toggle.pack(anchor="w", pady=(SPACING["1"], SPACING["4"]))
        for value, label in (("income", "Income"), ("expense", "Expense")):
            button = theme.RoundedButton(
                toggle, label,
                command=lambda v=value: self._set_type(v),
                width=112, height=36, style="secondary",
                parent_bg=COLORS["card"])
            button.pack(side="left", padx=(0, SPACING["2"]))
            self.type_buttons[value] = button

        category_wrap = tk.Frame(body, bg=COLORS["card"])
        category_wrap.pack(fill="x", pady=(0, SPACING["3"]))
        tk.Label(category_wrap, text="Category *", bg=COLORS["card"],
                 fg=COLORS["text"], font=theme.font("sm")).pack(
                     anchor="w", pady=(0, SPACING["1"]))
        self.category_combo = ttk.Combobox(
            category_wrap, state="readonly", font=theme.font("base"))
        self.category_combo.pack(fill="x", ipady=2)
        self.category_combo.bind("<<ComboboxSelected>>",
                                 lambda _event: self._sync_preview())

        row = tk.Frame(body, bg=COLORS["card"])
        row.pack(fill="x", pady=(0, SPACING["3"]))
        self.amount = theme.LabeledEntry(
            row, "Amount (%s)" % CURRENCY, required=True)
        self.amount.pack(side="left", fill="x", expand=True,
                         padx=(0, SPACING["3"]))
        self.date = theme.LabeledEntry(
            row, "Date", required=True, hint="YYYY-MM-DD")
        self.date.pack(side="left", fill="x", expand=True)

        self.description = theme.LabeledEntry(
            body, "Description (optional)")
        self.description.pack(fill="x")
        self.description.entry.configure(width=50)

        self.error_label = tk.Label(
            body, text="", bg=COLORS["card"], fg=COLORS["danger"],
            font=theme.font("sm"), justify="left", wraplength=560,
            anchor="w")
        self.error_label.pack(fill="x", pady=(SPACING["3"], 0))

        buttons = tk.Frame(body, bg=COLORS["card"])
        buttons.pack(fill="x", pady=(SPACING["3"], 0))
        theme.RoundedButton(buttons, "Save Transaction", command=self._save,
                            width=170, height=40,
                            parent_bg=COLORS["card"]).pack(side="left")
        theme.RoundedButton(buttons, "Clear", command=self._clear, width=90,
                            height=40, style="secondary",
                            parent_bg=COLORS["card"]).pack(
                                side="left", padx=(SPACING["2"], 0))

        self.amount.var.trace_add("write", lambda *_a: self._sync_preview())
        self.date.var.trace_add("write", lambda *_a: self._sync_preview())
        self.description.var.trace_add(
            "write", lambda *_a: self._sync_preview())

    def _build_preview(self, parent):
        """Live summary of the values currently entered."""
        self.preview_card = theme.Card(parent, padding=SPACING["4"])
        body = self.preview_card.body
        tk.Label(body, text="Entry preview", bg=COLORS["card"],
                 fg=COLORS["text"], font=theme.font("xl", "bold")).pack(anchor="w")
        tk.Label(body, text="Updates as you type; nothing is saved yet.",
                 bg=COLORS["card"], fg=COLORS["text_muted"],
                 font=theme.font("xs")).pack(anchor="w", pady=(0, SPACING["3"]))

        self.preview_badge_slot = tk.Frame(body, bg=COLORS["card"])
        self.preview_badge_slot.pack(anchor="w", pady=(0, SPACING["2"]))

        self.preview_amount = tk.Label(body, text=CURRENCY + "0.00",
                                       bg=COLORS["card"], fg=COLORS["income"],
                                       font=theme.display_font("4xl", "bold"))
        self.preview_amount.pack(anchor="w")

        self.preview_meta = tk.Label(body, text="", bg=COLORS["card"],
                                     fg=COLORS["text_secondary"],
                                     font=theme.font("sm"), justify="left",
                                     anchor="w", wraplength=240)
        self.preview_meta.pack(anchor="w", fill="x", pady=(SPACING["2"], 0))

    def _build_tips(self, parent):
        """Short reminders about how transactions are used."""
        card = theme.Card(parent, padding=SPACING["4"])
        card.pack(fill="x", pady=(SPACING["3"], 0))
        body = card.body
        tk.Label(body, text="Good to know", bg=COLORS["card"],
                 fg=COLORS["text"], font=theme.font("xl", "bold")).pack(anchor="w")
        for text in (
                "Expenses reduce your net income and count toward budgets.",
                "Income does not count toward expense budgets.",
                "Open History Transactions to link a record to a crop cycle."):
            row = tk.Frame(body, bg=COLORS["card"])
            row.pack(fill="x", pady=(SPACING["1"], 0))
            theme.Icon(row, "leaf", size=13, color=COLORS["primary_light"],
                       bg=COLORS["card"]).pack(side="left", anchor="n")
            tk.Label(row, text=text, bg=COLORS["card"],
                     fg=COLORS["text_secondary"], font=theme.font("sm"),
                     wraplength=240, justify="left").pack(
                         side="left", padx=(SPACING["1"], 0), fill="x",
                         expand=True)

    # ------------------------------------------------------------------
    # Responsive layout
    # ------------------------------------------------------------------
    def _on_resize(self, event):
        if event.widget is not self:
            return
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(80, lambda: self._reflow(event.width))

    def _reflow(self, width):
        self._resize_job = None
        columns = 1 if width < 900 else 2
        if columns == self._columns:
            return
        self._columns = columns
        self.form_card.grid_forget()
        self.side.grid_forget()
        for index in range(2):
            self.grid_area.columnconfigure(
                index, weight=0, uniform="")
        if columns == 2:
            self.grid_area.columnconfigure(0, weight=3, uniform="add")
            self.grid_area.columnconfigure(1, weight=2, uniform="add")
            self.form_card.grid(row=0, column=0, sticky="nsew",
                                padx=(0, SPACING["3"]))
            self.side.grid(row=0, column=1, sticky="nsew")
        else:
            self.grid_area.columnconfigure(0, weight=1, uniform="add")
            self.form_card.grid(row=0, column=0, sticky="nsew")
            self.side.grid(row=1, column=0, sticky="nsew",
                           pady=(SPACING["3"], 0))

    # ------------------------------------------------------------------
    # Behaviour
    # ------------------------------------------------------------------
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
        self._sync_preview()

    def _sync_preview(self):
        """Update the entry preview from current form values."""
        if not hasattr(self, "preview_amount"):
            return
        is_income = self.type_var.get() == "income"
        color = COLORS["income"] if is_income else COLORS["expense"]
        raw = (self.amount.get() or "").replace(",", "").strip()
        try:
            amount = float(raw) if raw else 0.0
        except ValueError:
            amount = 0.0
        self.preview_amount.config(
            text=CURRENCY + "{:,.2f}".format(amount), fg=color)

        for child in self.preview_badge_slot.winfo_children():
            child.destroy()
        theme.StatusBadge(
            self.preview_badge_slot,
            "income" if is_income else "expense",
            label="Income" if is_income else "Expense").pack()

        category = (self.category_combo.get() or "No category selected").strip()
        date_text = self.date.get().strip() or "No date yet"
        description = self.description.get().strip()
        meta = "%s\n%s" % (category, date_text)
        if description:
            meta += "\n" + description
        self.preview_meta.config(text=meta)

    def _load_categories(self):
        """Reload the category dropdown for the selected type."""
        transaction_type = self.type_var.get()
        try:
            categories = queries.get_categories(transaction_type)
        except mysql.connector.Error as exc:
            self.category_map = {}
            self.category_combo["values"] = []
            self.category_combo.set("")
            self._set_error("Could not load categories: " + str(exc))
            return

        self.category_map = {item["name"]: item["id"] for item in categories}
        names = [item["name"] for item in categories]
        self.category_combo["values"] = names
        if not names:
            self.category_combo.set("")
        elif self.category_combo.get() not in names:
            self.category_combo.current(0)
        self._sync_preview()

    def _set_error(self, message):
        """Show a validation message below the form."""
        self.error_label.config(text=message)

    def _save(self):
        """Validate the form and insert the transaction."""
        category_name = self.category_combo.get().strip()
        if category_name not in self.category_map:
            self._set_error("Please choose a category.")
            return

        ok, result, amount = validators.validate_amount(self.amount.get())
        if not ok:
            self._set_error(result)
            return

        ok, transaction_date = validators.validate_transaction_date(self.date.get())
        if not ok:
            self._set_error(transaction_date)
            return

        ok, description = validators.validate_description(self.description.get())
        if not ok:
            self._set_error(description)
            return

        try:
            queries.add_transaction(
                self.app.current_user["id"],
                self.category_map[category_name],
                self.type_var.get(),
                amount,
                description,
                transaction_date,
            )
        except mysql.connector.Error as exc:
            messagebox.showerror("Database Error",
                                 "Could not save the transaction.\n\n" + str(exc))
            return

        messagebox.showinfo(
            "Saved",
            "%s of %s%s saved." % (self.type_var.get().title(), CURRENCY,
                                   "{:,.2f}".format(float(amount))),
        )
        self._clear()

    def _clear(self):
        """Reset the form to its default state."""
        self.type_var.set("income")
        self._refresh_type_buttons()
        self.amount.clear()
        self.description.clear()
        self.date.set(datetime.now().strftime("%Y-%m-%d"))
        self._set_error("")
        self._load_categories()
        self.amount.focus()

    def refresh(self):
        """Reload categories whenever the page is shown."""
        self._refresh_type_buttons()
        self._load_categories()
        if not self.date.get().strip():
            self.date.set(datetime.now().strftime("%Y-%m-%d"))
        if hasattr(self, "scroll"):
            self.scroll.scroll_to_top()
