"""History Transactions page with filters, editing, deleting and export."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import mysql.connector

from config import COLORS, CURRENCY, SPACING
from database import queries
from models import validators
from ui import theme
from ui.transaction_dialog import EditTransactionDialog
from utils.export import export_transactions_csv


class HistoryPage(tk.Frame):
    """Searchable table of all transactions belonging to the current user."""

    def __init__(self, master, app):
        super().__init__(master, bg=COLORS["background"])
        self.app = app
        self.rows = {}
        self._build()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _build(self):
        """Create the header, filter bar, table and action bar."""
        theme.PageHero(
            self, "History Transactions",
            "Search, filter, edit or export your recorded transactions.",
            badge="Sakani \u00b7 History", crumb="History",
            on_home=lambda: self.app.open_page("dashboard")).pack(fill="x")

        wrapper = tk.Frame(self, bg=COLORS["background"])
        wrapper.pack(fill="both", expand=True, padx=SPACING["6"],
                     pady=SPACING["5"])

        header = tk.Frame(wrapper, bg=COLORS["background"])
        header.pack(fill="x", pady=(0, SPACING["4"]))

        theme.RoundedButton(header, "Export CSV", command=self._export,
                            width=124, height=38,
                            parent_bg=COLORS["background"]).pack(
                                side="right", anchor="e")

        self._build_filters(wrapper)

        table_card = theme.Card(wrapper, padding=SPACING["3"])
        table_card.pack(fill="both", expand=True)
        table_body = table_card.body

        columns = ("date", "type", "category", "description", "amount")
        self.tree = ttk.Treeview(table_body, columns=columns, show="headings",
                                 selectmode="browse")
        headings = [("date", "Date", 100), ("type", "Type", 82),
                    ("category", "Category", 150),
                    ("description", "Description", 300),
                    ("amount", "Amount", 120)]
        for column, heading, width in headings:
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=width, minwidth=70,
                             anchor="e" if column == "amount" else "w",
                             stretch=(column == "description"))
        self.tree.tag_configure("income", foreground=COLORS["income"])
        self.tree.tag_configure("expense", foreground=COLORS["expense"])

        y_scroll = ttk.Scrollbar(table_body, orient="vertical",
                                 command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_body, orient="horizontal",
                                 command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set,
                            xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        table_body.rowconfigure(0, weight=1)
        table_body.columnconfigure(0, weight=1)

        self.empty_label = tk.Label(
            table_body,
            text="No transactions match these filters.\nTry clearing the search or date range.",
            bg=COLORS["card"], fg=COLORS["text_secondary"],
            font=theme.font("base"), justify="center")
        self._show_empty(False)

        actions = tk.Frame(wrapper, bg=COLORS["background"])
        actions.pack(fill="x", pady=(SPACING["3"], 0))
        theme.RoundedButton(actions, "Edit Selected", command=self._edit,
                            width=118, height=36, style="secondary",
                            parent_bg=COLORS["background"]).pack(side="left")
        theme.RoundedButton(actions, "Delete", command=self._delete,
                            width=92, height=36, style="danger",
                            parent_bg=COLORS["background"]).pack(
                                side="left", padx=(SPACING["2"], 0))
        self.count_label = tk.Label(actions, text="", bg=COLORS["background"],
                                    fg=COLORS["text_secondary"],
                                    font=theme.font("sm"))
        self.count_label.pack(side="right")

        self.tree.bind("<Double-1>", lambda _event: self._edit())
        self.search_entry.bind("<Return>", lambda _event: self._load())
        self.start_entry.bind("<Return>", lambda _event: self._load())
        self.end_entry.bind("<Return>", lambda _event: self._load())

    def _build_filters(self, parent):
        """Build the type, search and date filter card."""
        card = theme.Card(parent, padding=SPACING["3"])
        card.pack(fill="x", pady=(0, SPACING["3"]))
        body = card.body

        row1 = tk.Frame(body, bg=COLORS["card"])
        row1.pack(fill="x")

        tk.Label(row1, text="Type", bg=COLORS["card"],
                 fg=COLORS["text_muted"], font=theme.font("xs")).pack(side="left")
        self.type_combo = ttk.Combobox(row1, values=["All", "Income", "Expense"],
                                       state="readonly", width=9,
                                       font=theme.font("sm"))
        self.type_combo.current(0)
        self.type_combo.pack(side="left", padx=(SPACING["1"], SPACING["3"]))

        tk.Label(row1, text="Search", bg=COLORS["card"],
                 fg=COLORS["text_muted"], font=theme.font("xs")).pack(side="left")
        search_wrap = tk.Frame(row1, bg=COLORS["card"])
        search_wrap.pack(side="left", fill="x", expand=True,
                         padx=(SPACING["1"], SPACING["3"]))
        theme.Icon(search_wrap, "search", size=15,
                   color=COLORS["text_muted"], bg=COLORS["card"]).pack(
                       side="left", padx=(0, SPACING["1"]))
        self.search_entry = ttk.Entry(search_wrap, font=theme.font("sm"))
        self.search_entry.pack(side="left", fill="x", expand=True)

        theme.RoundedButton(row1, "Apply", command=self._load, width=78,
                            height=32, style="primary",
                            parent_bg=COLORS["card"]).pack(side="left")
        theme.RoundedButton(row1, "Reset", command=self._reset, width=78,
                            height=32, style="secondary",
                            parent_bg=COLORS["card"]).pack(
                                side="left", padx=(SPACING["2"], 0))

        row2 = tk.Frame(body, bg=COLORS["card"])
        row2.pack(fill="x", pady=(SPACING["2"], 0))
        tk.Label(row2, text="From", bg=COLORS["card"],
                 fg=COLORS["text_muted"], font=theme.font("xs")).pack(side="left")
        self.start_entry = ttk.Entry(row2, width=12, font=theme.font("sm"))
        self.start_entry.pack(side="left", padx=(SPACING["1"], SPACING["3"]))
        tk.Label(row2, text="To", bg=COLORS["card"],
                 fg=COLORS["text_muted"], font=theme.font("xs")).pack(side="left")
        self.end_entry = ttk.Entry(row2, width=12, font=theme.font("sm"))
        self.end_entry.pack(side="left", padx=(SPACING["1"], SPACING["3"]))
        tk.Label(row2, text="Dates use YYYY-MM-DD", bg=COLORS["card"],
                 fg=COLORS["text_muted"], font=theme.font("xs")).pack(side="left")

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    def _read_filters(self):
        """Validate the filter fields and return a filter dictionary."""
        selected = self.type_combo.get()
        transaction_type = None if selected in ("", "All") else selected.lower()
        start = self.start_entry.get().strip() or None
        end = self.end_entry.get().strip() or None
        for value in (start, end):
            if value:
                ok, _result = validators.validate_transaction_date(value)
                if not ok:
                    messagebox.showwarning(
                        "Invalid date",
                        "Please enter dates in YYYY-MM-DD format.")
                    return None
        return {
            "transaction_type": transaction_type,
            "search": self.search_entry.get().strip() or None,
            "start": start,
            "end": end,
        }

    def _load(self):
        """Query the transactions and refill the table."""
        filters = self._read_filters()
        if filters is None:
            return
        try:
            records = queries.get_transactions(
                self.app.current_user["id"],
                transaction_type=filters["transaction_type"],
                search=filters["search"],
                start=filters["start"],
                end=filters["end"],
            )
        except mysql.connector.Error as exc:
            messagebox.showerror("Database Error",
                                 "Could not load transactions.\n\n" + str(exc))
            return

        self.tree.delete(*self.tree.get_children())
        self.rows = {}
        for record in records:
            item_id = str(record["id"])
            raw_date = record["transaction_date"]
            date_text = (raw_date.strftime("%Y-%m-%d")
                         if hasattr(raw_date, "strftime") else str(raw_date))
            amount_text = CURRENCY + "{:,.2f}".format(float(record["amount"]))
            self.tree.insert(
                "", "end", iid=item_id,
                values=(date_text, str(record["type"]).title(),
                        record["category"], record.get("description") or "—",
                        amount_text),
                tags=(record["type"],),
            )
            self.rows[item_id] = record
        self.count_label.config(text="%d transaction(s)" % len(records))
        self._show_empty(len(records) == 0)

    def _selected_id(self):
        """Return the selected row id or show a hint and return None."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No selection",
                                "Please select a transaction first.")
            return None
        return selection[0]

    def _edit(self):
        """Open the edit dialog for the selected transaction."""
        item_id = self._selected_id()
        if item_id is None:
            return
        record = self.rows.get(item_id)
        if record is not None:
            EditTransactionDialog(self, self.app, record, on_saved=self._load)

    def _delete(self):
        """Delete the selected transaction after confirmation."""
        item_id = self._selected_id()
        if item_id is None:
            return
        record = self.rows.get(item_id)
        if record is None:
            return
        amount_text = CURRENCY + "{:,.2f}".format(float(record["amount"]))
        if not messagebox.askyesno(
                "Delete Transaction",
                "Delete this transaction?\n\n%s — %s (%s)" % (
                    record["category"],
                    record.get("description") or "No description",
                    amount_text)):
            return
        try:
            queries.delete_transaction(int(item_id),
                                       self.app.current_user["id"])
        except mysql.connector.Error as exc:
            messagebox.showerror(
                "Database Error",
                "Could not delete the transaction.\n\n" + str(exc))
            return
        self._load()

    def _export(self):
        """Export the currently displayed rows to a CSV file."""
        if not self.rows:
            messagebox.showinfo("Export", "There are no transactions to export.")
            return
        path = filedialog.asksaveasfilename(
            title="Save transactions as CSV",
            defaultextension=".csv",
            initialfile="sakani_transactions.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        ordered = [self.rows[item_id] for item_id in self.tree.get_children()
                   if item_id in self.rows]
        try:
            count = export_transactions_csv(ordered, path)
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))
            return
        messagebox.showinfo("Export complete",
                            "%d transaction(s) saved to:\n%s" % (count, path))

    def _show_empty(self, visible):
        """Show or hide the empty-state label."""
        if visible:
            self.empty_label.place(relx=0.5, rely=0.5)
        else:
            self.empty_label.place_forget()

    def _reset(self):
        """Clear all filters and reload the full history."""
        self.type_combo.current(0)
        self.search_entry.delete(0, "end")
        self.start_entry.delete(0, "end")
        self.end_entry.delete(0, "end")
        self._load()

    def refresh(self):
        """Reload the table whenever the page is shown."""
        self._load()
