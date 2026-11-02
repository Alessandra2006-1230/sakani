"""Modal dialog that exports a financial summary for a custom date range."""

import tkinter as tk
from tkinter import filedialog, messagebox

import mysql.connector

from config import COLORS, SPACING
from database import queries
from models import validators
from ui import theme
from utils.export import export_summary_csv


class ExportRangeDialog(tk.Toplevel):
    """Small modal window used by the Financial Summary page."""

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.title("Export Custom Range")
        self.configure(bg=COLORS["card"])
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self._build()
        self._center_on(master)
        self.bind("<Escape>", lambda _event: self.destroy())

    def _build(self):
        container = tk.Frame(self, bg=COLORS["card"])
        container.pack(fill="both", expand=True, padx=SPACING["6"],
                       pady=SPACING["5"])

        tk.Label(container, text="Export Custom Range", bg=COLORS["card"],
                 fg=COLORS["text"],
                 font=theme.font("3xl", "bold")).pack(anchor="w")
        tk.Label(container,
                 text="Choose a start and end date. The exported totals match "
                      "the same date range queried from your records.",
                 bg=COLORS["card"], fg=COLORS["text_secondary"],
                 font=theme.font("sm"), justify="left", wraplength=380).pack(
                     anchor="w", pady=(SPACING["1"], SPACING["4"]))

        row = tk.Frame(container, bg=COLORS["card"])
        row.pack(fill="x")
        self.start = theme.LabeledEntry(row, "Start date", required=True,
                                        hint="YYYY-MM-DD", width=16)
        self.start.pack(side="left", fill="x", expand=True,
                        padx=(0, SPACING["3"]))
        self.end = theme.LabeledEntry(row, "End date", required=True,
                                      hint="YYYY-MM-DD", width=16)
        self.end.pack(side="left", fill="x", expand=True)

        self.error_label = tk.Label(
            container, text="", bg=COLORS["card"], fg=COLORS["danger"],
            font=theme.font("sm"), justify="left", wraplength=380, anchor="w")
        self.error_label.pack(fill="x", pady=(SPACING["2"], 0))

        buttons = tk.Frame(container, bg=COLORS["card"])
        buttons.pack(fill="x", pady=(SPACING["4"], 0))
        theme.RoundedButton(buttons, "Export", command=self._do_export,
                            width=110, height=36,
                            parent_bg=COLORS["card"]).pack(side="left")
        theme.RoundedButton(buttons, "Cancel", command=self.destroy,
                            width=96, height=36, style="secondary",
                            parent_bg=COLORS["card"]).pack(
                                side="left", padx=(SPACING["2"], 0))

        self.start.focus()

    def _center_on(self, master):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = master.winfo_rootx() + max(0, (master.winfo_width() - width) // 2)
        y = master.winfo_rooty() + max(0, (master.winfo_height() - height) // 2)
        self.geometry("+%d+%d" % (x, y))

    def _do_export(self):
        ok, message, start = validators.validate_transaction_date(
            self.start.get().strip())
        if not ok:
            self.error_label.config(text=message)
            return
        ok, message, end = validators.validate_transaction_date(
            self.end.get().strip())
        if not ok:
            self.error_label.config(text=message)
            return
        if start > end:
            self.error_label.config(text="Start date must not be after end date.")
            return

        user_id = self.app.current_user["id"]
        try:
            monthly = queries.get_monthly_summary_range(user_id, start, end)
            expense_breakdown = queries.get_category_breakdown_range(
                user_id, "expense", start, end)
            income_breakdown = queries.get_category_breakdown_range(
                user_id, "income", start, end)
        except mysql.connector.Error as exc:
            messagebox.showerror("Database Error",
                                 "Could not load data for export.\n\n" + str(exc))
            self.destroy()
            return

        if not monthly and not expense_breakdown and not income_breakdown:
            messagebox.showinfo("Export",
                                "There is no data to export for this range.")
            return

        total_income = sum((row["income"] for row in monthly), 0)
        total_expense = sum((row["expense"] for row in monthly), 0)
        net = total_income - total_expense

        path = filedialog.asksaveasfilename(
            title="Save financial summary as CSV",
            defaultextension=".csv",
            initialfile="sakani_summary_%s_to_%s.csv" % (
                start.isoformat(), end.isoformat()),
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            export_summary_csv(monthly, expense_breakdown, income_breakdown,
                               total_income, total_expense, net, path)
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))
            return

        messagebox.showinfo("Export complete",
                            "Summary for %s to %s saved to:\n%s" % (
                                start.isoformat(), end.isoformat(), path))
        self.destroy()
