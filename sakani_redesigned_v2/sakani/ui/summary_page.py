"""Financial Summary page: yearly totals, monthly table and donut charts."""

import calendar
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import mysql.connector

from config import COLORS, CURRENCY, SPACING
from database import queries
from models import validators
from ui import charts, theme
from utils.export import export_summary_csv


class SummaryPage(tk.Frame):
    """Yearly financial overview with monthly and category breakdowns."""

    def __init__(self, master, app):
        super().__init__(master, bg=COLORS["background"])
        self.app = app
        self.year_var = tk.StringVar(value=str(datetime.now().year))
        self.expense_data = []
        self.income_data = []
        self._monthly_data = []
        self._expense_breakdown = []
        self._income_breakdown = []
        self._total_income = 0
        self._total_expense = 0
        self._net_total = 0
        self._columns = 0
        self._resize_job = None
        self._build()
        self.bind("<Configure>", self._on_resize)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _build(self):
        """Create the header, totals, charts and monthly table."""
        theme.PageHero(
            self, "Financial Summary",
            "Yearly totals and category breakdown.",
            badge="Sakani \u00b7 Summary", crumb="Summary",
            on_home=lambda: self.app.open_page("dashboard")).pack(fill="x")

        scroll = theme.ScrollFrame(self, bg=COLORS["background"])
        scroll.pack(fill="both", expand=True)
        self.scroll = scroll

        wrapper = tk.Frame(scroll.body, bg=COLORS["background"])
        wrapper.pack(fill="both", expand=True, padx=SPACING["6"],
                     pady=SPACING["5"])

        self._build_header(wrapper)

        # Totals
        stats = tk.Frame(wrapper, bg=COLORS["background"])
        stats.pack(fill="x", pady=(0, SPACING["4"]))
        for column in range(3):
            stats.columnconfigure(column, weight=1, uniform="summary")
        self.income_value, self.income_caption = self._stat_card(
            stats, 0, "Total Income", "income", COLORS["income"],
            COLORS["income_soft"])
        self.expense_value, self.expense_caption = self._stat_card(
            stats, 1, "Total Expenses", "expense", COLORS["expense"],
            COLORS["expense_soft"])
        self.net_value, self.net_caption = self._stat_card(
            stats, 2, "Net Result", "net", COLORS["primary"],
            COLORS["pale_mint"])

        # Charts
        self.charts_row = tk.Frame(wrapper, bg=COLORS["background"])
        self.charts_row.pack(fill="x", pady=(0, SPACING["4"]))

        self.expense_card = self._chart_card(
            self.charts_row, "Expenses by Category",
            "Where your money went this year.")
        self.expense_canvas = self.expense_card.canvas

        self.income_card = self._chart_card(
            self.charts_row, "Income by Category",
            "Where your money came from this year.")
        self.income_canvas = self.income_card.canvas

        # Monthly table
        table_card = theme.Card(wrapper, padding=SPACING["3"])
        table_card.pack(fill="both", expand=True)
        head = tk.Frame(table_card.body, bg=COLORS["card"])
        head.pack(fill="x", pady=(0, SPACING["2"]))
        tk.Label(head, text="Monthly Totals", bg=COLORS["card"],
                 fg=COLORS["text"], font=theme.font("xl", "bold")).pack(side="left")
        self.table_caption = tk.Label(head, text="", bg=COLORS["card"],
                                      fg=COLORS["text_muted"],
                                      font=theme.font("xs"))
        self.table_caption.pack(side="right")

        table_box = tk.Frame(table_card.body, bg=COLORS["card"])
        table_box.pack(fill="both", expand=True)

        columns = ("month", "income", "expense", "net")
        self.monthly_tree = ttk.Treeview(table_box, columns=columns,
                                         show="headings", height=5)
        for column, heading in (("month", "Month"), ("income", "Income"),
                                ("expense", "Expense"), ("net", "Net")):
            self.monthly_tree.heading(column, text=heading)
            self.monthly_tree.column(
                column, width=140, minwidth=90,
                anchor="w" if column == "month" else "e", stretch=True)
        self.monthly_tree.tag_configure("positive", foreground=COLORS["income"])
        self.monthly_tree.tag_configure("negative", foreground=COLORS["expense"])

        scrollbar = ttk.Scrollbar(table_box, orient="vertical",
                                  command=self.monthly_tree.yview)
        self.monthly_tree.configure(yscrollcommand=scrollbar.set)
        self.monthly_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.table_empty = tk.Label(
            table_box, text="No transactions recorded for this year.",
            bg=COLORS["card"], fg=COLORS["text_secondary"],
            font=theme.font("sm"))

    def _build_header(self, parent):
        header = tk.Frame(parent, bg=COLORS["background"])
        header.pack(fill="x", pady=(0, SPACING["4"]))

        controls = tk.Frame(header, bg=COLORS["background"])
        controls.pack(side="right", anchor="e")

        top_row = tk.Frame(controls, bg=COLORS["background"])
        top_row.pack(anchor="e")
        tk.Label(top_row, text="Year", bg=COLORS["background"],
                 fg=COLORS["text_muted"], font=theme.font("xs")).pack(
                     side="left", padx=(0, SPACING["1"]))
        self.year_combo = ttk.Combobox(
            top_row, textvariable=self.year_var, state="readonly", width=7,
            values=[str(datetime.now().year)], font=theme.font("sm"))
        self.year_combo.pack(side="left")
        self.year_combo.bind("<<ComboboxSelected>>", lambda _event: self._load())

        buttons = tk.Frame(controls, bg=COLORS["background"])
        buttons.pack(anchor="e", pady=(SPACING["2"], 0))
        theme.RoundedButton(buttons, "Export Summary",
                            command=self._export_yearly, width=146, height=34,
                            style="secondary",
                            parent_bg=COLORS["background"]).pack(
                                side="right", padx=(SPACING["2"], 0))
        theme.RoundedButton(buttons, "Export Custom Range",
                            command=self._export_custom, width=178, height=34,
                            parent_bg=COLORS["background"]).pack(side="right")

    def _stat_card(self, parent, column, title, icon, color, tint):
        """Create one totals card and return (value, caption) labels."""
        card = theme.Card(parent, padding=SPACING["4"])
        card.grid(row=0, column=column, sticky="nsew",
                  padx=(0 if column == 0 else SPACING["3"], 0))

        top = tk.Frame(card.body, bg=COLORS["card"])
        top.pack(fill="x")
        chip = tk.Frame(top, bg=tint, width=28, height=28)
        chip.pack(side="left")
        chip.pack_propagate(False)
        theme.Icon(chip, icon, size=16, color=color, bg=tint).pack(expand=True)
        tk.Label(top, text=title, bg=COLORS["card"],
                 fg=COLORS["text_secondary"],
                 font=theme.font("sm")).pack(side="left", padx=(SPACING["2"], 0))

        value = tk.Label(card.body, text=CURRENCY + "0.00",
                         bg=COLORS["card"], fg=color,
                         font=theme.display_font("4xl", "bold"))
        value.pack(anchor="w", pady=(SPACING["2"], 0))
        caption = tk.Label(card.body, text="", bg=COLORS["card"],
                           fg=COLORS["text_muted"], font=theme.font("xs"),
                           anchor="w", justify="left", wraplength=220)
        caption.pack(anchor="w", fill="x")
        return value, caption

    def _chart_card(self, parent, title, subtitle):
        """Create a chart card with a title and a resizable canvas."""
        card = theme.Card(parent, padding=SPACING["4"])
        tk.Label(card.body, text=title, bg=COLORS["card"], fg=COLORS["text"],
                 font=theme.font("xl", "bold")).pack(anchor="w")
        tk.Label(card.body, text=subtitle, bg=COLORS["card"],
                 fg=COLORS["text_muted"], font=theme.font("xs")).pack(
                     anchor="w", pady=(0, SPACING["1"]))
        card.canvas = tk.Canvas(card.body, bg=COLORS["card"], height=200,
                                highlightthickness=0, bd=0)
        card.canvas.pack(fill="both", expand=True)
        card.canvas.bind("<Configure>", lambda _event: self._draw_charts())
        return card

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
        self.expense_card.grid_forget()
        self.income_card.grid_forget()
        for index in range(2):
            self.charts_row.columnconfigure(index, weight=0, uniform="")
        if columns == 2:
            self.charts_row.columnconfigure(0, weight=1, uniform="chart")
            self.charts_row.columnconfigure(1, weight=1, uniform="chart")
            self.expense_card.grid(row=0, column=0, sticky="nsew")
            self.income_card.grid(row=0, column=1, sticky="nsew",
                                  padx=(SPACING["3"], 0))
        else:
            self.charts_row.columnconfigure(0, weight=1, uniform="chart")
            self.expense_card.grid(row=0, column=0, sticky="nsew")
            self.income_card.grid(row=1, column=0, sticky="nsew",
                                  pady=(SPACING["3"], 0))

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    def _money(self, value):
        """Format a number with the peso sign."""
        return CURRENCY + "{:,.2f}".format(value)

    def _draw_charts(self):
        """Redraw both category donut charts."""
        if self.expense_canvas.winfo_exists():
            charts.draw_pie_chart(self.expense_canvas, self.expense_data,
                                  center_label="Expenses")
        if self.income_canvas.winfo_exists():
            charts.draw_pie_chart(self.income_canvas, self.income_data,
                                  center_label="Income")

    def _load(self):
        """Load the selected year and update totals, charts and table."""
        try:
            year = int(self.year_var.get())
        except ValueError:
            year = datetime.now().year
            self.year_var.set(str(year))

        user_id = self.app.current_user["id"]
        try:
            monthly = queries.get_monthly_summary(user_id, year)
            expense_breakdown = queries.get_category_breakdown(
                user_id, "expense", year)
            income_breakdown = queries.get_category_breakdown(
                user_id, "income", year)
        except mysql.connector.Error as exc:
            messagebox.showerror(
                "Database Error",
                "Could not load the financial summary.\n\n" + str(exc))
            return

        total_income = sum((row["income"] for row in monthly), 0)
        total_expense = sum((row["expense"] for row in monthly), 0)
        net = total_income - total_expense

        self._monthly_data = list(monthly)
        self._expense_breakdown = list(expense_breakdown)
        self._income_breakdown = list(income_breakdown)
        self._total_income = total_income
        self._total_expense = total_expense
        self._net_total = net

        self.income_value.config(text=self._money(total_income))
        self.expense_value.config(text=self._money(total_expense))
        self.net_value.config(text=self._money(net),
                              fg=COLORS["income"] if net >= 0
                              else COLORS["expense"])

        for caption in (self.income_caption, self.expense_caption):
            caption.config(text="Year %d" % year)
        if net > 0:
            net_text = "Profit — income exceeds expenses"
            net_color = COLORS["primary"]
        elif net < 0:
            net_text = "Loss — expenses exceed income"
            net_color = COLORS["expense"]
        else:
            net_text = "Break-even — income equals expenses"
            net_color = COLORS["text_muted"]
        self.net_caption.config(text=net_text, fg=net_color)

        self.monthly_tree.delete(*self.monthly_tree.get_children())
        for row in monthly:
            tag = "positive" if row["net"] >= 0 else "negative"
            self.monthly_tree.insert(
                "", "end",
                values=(calendar.month_name[row["month"]],
                        self._money(row["income"]),
                        self._money(row["expense"]),
                        self._money(row["net"])),
                tags=(tag,),
            )
        self.table_caption.config(text="%d month(s) with records" % len(monthly))
        if monthly:
            self.table_empty.place_forget()
        else:
            self.table_empty.place(relx=0.5, rely=0.5)

        self.expense_data = [
            {"label": row["category"], "value": row["total"]}
            for row in expense_breakdown
        ]
        self.income_data = [
            {"label": row["category"], "value": row["total"]}
            for row in income_breakdown
        ]
        self._draw_charts()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def _export_yearly(self):
        """Export the financial summary for the selected year to CSV."""
        if (not self._monthly_data and not self._expense_breakdown
                and not self._income_breakdown):
            messagebox.showinfo("Export", "There is no data to export for this year.")
            return

        try:
            year = int(self.year_var.get())
        except ValueError:
            year = datetime.now().year

        path = filedialog.asksaveasfilename(
            title="Save financial summary as CSV",
            defaultextension=".csv",
            initialfile="sakani_summary_%d.csv" % year,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            export_summary_csv(
                self._monthly_data, self._expense_breakdown,
                self._income_breakdown, self._total_income,
                self._total_expense, self._net_total, path)
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))
            return

        messagebox.showinfo("Export complete",
                            "Summary for %d saved to:\n%s" % (year, path))

    def _export_custom(self):
        """Export a summary for a custom date range to CSV."""
        from ui.export_range_dialog import ExportRangeDialog

        ExportRangeDialog(self, self.app)

    def refresh(self):
        """Refresh the year list and reload the selected year."""
        user_id = self.app.current_user["id"]
        try:
            years = queries.get_available_years(user_id)
        except mysql.connector.Error:
            years = []
        current_year = datetime.now().year
        options = sorted(set(years + [current_year]), reverse=True)
        labels = [str(year) for year in options]
        self.year_combo["values"] = labels
        if self.year_var.get() not in labels:
            self.year_var.set(str(current_year))
        self._load()
        if hasattr(self, "scroll"):
            self.scroll.scroll_to_top()
