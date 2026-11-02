"""Dashboard page: totals, income vs expense chart and recent records."""

import calendar
import tkinter as tk
from datetime import date, timedelta
from decimal import Decimal
from tkinter import messagebox, ttk

import mysql.connector

from config import COLORS, CURRENCY, SPACING
from database import queries
from ui import charts, theme

PERIODS = [
    ("All time", "all"),
    ("This month", "this_month"),
    ("Last month", "last_month"),
    ("This year", "this_year"),
    ("Custom range", "custom"),
]


class DashboardPage(tk.Frame):
    """Overview of the farm's money, chart and latest transactions."""

    def __init__(self, master, app):
        super().__init__(master, bg=COLORS["background"])
        self.app = app
        self.chart_labels = []
        self.chart_series = []
        self.stat_values = {}
        self.stat_captions = {}
        self.kpi_cards = []
        self.insight_cards = []
        self.period_var = tk.StringVar(value=PERIODS[0][0])
        self._columns = 0
        self._bottom_columns = 0
        self._resize_job = None
        self._build()
        self.bind("<Configure>", self._on_resize)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _build(self):
        """Create the hero banner, KPI cards, chart and recent list."""
        user = self.app.current_user or {}
        full_name = (user.get("full_name") or "Farmer").strip()
        first_name = full_name.split()[0] if full_name else "Farmer"
        theme.PageHero(
            self, "Welcome back, %s" % first_name,
            "Here is how your farm is doing financially.",
            badge="Sakani \u00b7 Dashboard", crumb="Dashboard",
            on_home=lambda: self.app.open_page("dashboard")).pack(fill="x")

        scroll = theme.ScrollFrame(self, bg=COLORS["background"])
        scroll.pack(fill="both", expand=True)
        self.scroll = scroll
        wrapper = tk.Frame(scroll.body, bg=COLORS["background"])
        wrapper.pack(fill="both", expand=True, padx=SPACING["6"],
                     pady=SPACING["5"])

        self._build_header(wrapper)

        # Primary KPI cards
        self.kpi_frame = tk.Frame(wrapper, bg=COLORS["background"])
        self.kpi_frame.pack(fill="x", pady=(0, SPACING["3"]))
        kpi_defs = [
            ("income", "Total Income", "income", COLORS["income"],
             COLORS["income_soft"]),
            ("expense", "Total Expenses", "expense", COLORS["expense"],
             COLORS["expense_soft"]),
            ("net", "Net Income", "net", COLORS["primary"],
             COLORS["pale_mint"]),
            ("count", "Transactions", "transactions", COLORS["info"],
             COLORS["info_soft"]),
        ]
        for key, title, icon, color, tint in kpi_defs:
            card = self._make_kpi_card(self.kpi_frame, key, title, icon,
                                       color, tint, primary=True)
            self.kpi_cards.append(card)

        # Secondary insight cards
        self.insight_frame = tk.Frame(wrapper, bg=COLORS["background"])
        self.insight_frame.pack(fill="x", pady=(0, SPACING["4"]))
        insight_defs = [
            ("budget_remaining", "Remaining Budget", "budget_remaining",
             COLORS["primary"], COLORS["pale_mint"]),
            ("budget_over", "Over Budget", "over_budget", COLORS["expense"],
             COLORS["expense_soft"]),
            ("cycle_net", "Latest Cycle Net", "cycle_net", COLORS["info"],
             COLORS["info_soft"]),
            ("cycle_count", "Active Cycles", "active_cycles",
             COLORS["gold_accent"], COLORS["gold_soft"]),
        ]
        for key, title, icon, color, tint in insight_defs:
            card = self._make_kpi_card(self.insight_frame, key, title, icon,
                                       color, tint, primary=False)
            self.insight_cards.append(card)

        # Bottom section: chart + recent transactions
        self.bottom = tk.Frame(wrapper, bg=COLORS["background"])
        self.bottom.pack(fill="both", expand=True)

        self.chart_card = theme.Card(self.bottom, padding=SPACING["4"])
        chart_header = tk.Frame(self.chart_card.body, bg=COLORS["card"])
        chart_header.pack(fill="x", pady=(0, SPACING["2"]))
        theme.section_title(chart_header, "Income vs Expenses").pack(side="left")
        self.chart_period = tk.Label(chart_header, text="", bg=COLORS["card"],
                                     fg=COLORS["text_muted"],
                                     font=theme.font("xs"))
        self.chart_period.pack(side="right")

        self.canvas = tk.Canvas(self.chart_card.body, bg=COLORS["card"],
                                height=280, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _event: self._draw_chart())

        self.recent_card = theme.Card(self.bottom, padding=SPACING["4"])
        recent_header = tk.Frame(self.recent_card.body, bg=COLORS["card"])
        recent_header.pack(fill="x", pady=(0, SPACING["2"]))
        theme.section_title(recent_header, "Recent Transactions").pack(side="left")

        tree_wrap = tk.Frame(self.recent_card.body, bg=COLORS["card"])
        tree_wrap.pack(fill="both", expand=True)

        columns = ("date", "category", "amount")
        self.recent_tree = ttk.Treeview(tree_wrap, columns=columns,
                                        show="headings", height=7,
                                        selectmode="browse")
        for column, heading, width, anchor in (
                ("date", "Date", 84, "w"),
                ("category", "Category", 130, "w"),
                ("amount", "Amount", 100, "e")):
            self.recent_tree.heading(column, text=heading)
            self.recent_tree.column(column, width=width, anchor=anchor,
                                    stretch=(column == "category"))
        self.recent_tree.tag_configure("income", foreground=COLORS["income"])
        self.recent_tree.tag_configure("expense", foreground=COLORS["expense"])

        recent_scroll = ttk.Scrollbar(tree_wrap, orient="vertical",
                                      command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=recent_scroll.set)
        self.recent_tree.pack(side="left", fill="both", expand=True)
        recent_scroll.pack(side="right", fill="y")

        self.recent_empty = tk.Label(
            tree_wrap, text="No transactions yet", bg=COLORS["card"],
            fg=COLORS["text_secondary"], font=theme.font("sm"))
        self._show_recent_empty(True)

    def _build_header(self, parent):
        """Welcome header with a compact period selector."""
        header = tk.Frame(parent, bg=COLORS["background"])
        header.pack(fill="x", pady=(0, SPACING["4"]))

        controls = tk.Frame(header, bg=COLORS["background"])
        controls.pack(side="right", anchor="e")

        tk.Label(controls, text="Reporting period", bg=COLORS["background"],
                 fg=COLORS["text_muted"], font=theme.font("xs")).pack(anchor="e")

        row = tk.Frame(controls, bg=COLORS["background"])
        row.pack(anchor="e", pady=(2, 0))

        self.period_combo = ttk.Combobox(
            row, textvariable=self.period_var, state="readonly",
            values=[label for label, _key in PERIODS],
            font=theme.font("sm"), width=14)
        self.period_combo.pack(side="left")
        self.period_combo.bind("<<ComboboxSelected>>",
                               lambda _event: self._on_period_change())

        self.custom_frame = tk.Frame(row, bg=COLORS["background"])
        self.start_entry = ttk.Entry(self.custom_frame, width=11,
                                     font=theme.font("sm"))
        self.start_entry.pack(side="left", padx=(SPACING["2"], 0))
        tk.Label(self.custom_frame, text="to", bg=COLORS["background"],
                 fg=COLORS["text_muted"], font=theme.font("xs")).pack(
                     side="left", padx=4)
        self.end_entry = ttk.Entry(self.custom_frame, width=11,
                                   font=theme.font("sm"))
        self.end_entry.pack(side="left")
        theme.RoundedButton(self.custom_frame, "Apply",
                            command=self.refresh, width=64, height=28,
                            style="secondary",
                            parent_bg=COLORS["background"]).pack(
                                side="left", padx=(4, 0))

        self.period_label = tk.Label(parent, text="", bg=COLORS["background"],
                                     fg=COLORS["text_muted"],
                                     font=theme.font("xs"))
        self.period_label.pack(anchor="e", pady=(SPACING["1"], 0))

        self._update_custom_visibility()

    def _make_kpi_card(self, parent, key, title, icon, color, tint,
                       primary=True):
        """Create one KPI card and store its value/caption labels."""
        card = tk.Frame(parent, bg=COLORS["card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1, bd=0)
        if primary:
            # Thin colour strip along the top edge ties each card to its metric.
            tk.Frame(card, bg=color, height=3).pack(fill="x")
        inner = tk.Frame(card, bg=COLORS["card"])
        inner.pack(fill="both", expand=True, padx=SPACING["4"],
                   pady=SPACING["4"] if primary else SPACING["3"])

        top = tk.Frame(inner, bg=COLORS["card"])
        top.pack(fill="x")
        chip = tk.Frame(top, bg=tint, width=28, height=28)
        chip.pack(side="left")
        chip.pack_propagate(False)
        theme.Icon(chip, icon, size=16, color=color, bg=tint).pack(expand=True)
        tk.Label(top, text=title.upper(), bg=COLORS["card"],
                 fg=COLORS["primary"],
                 font=theme.font("xs", "bold")).pack(side="left", padx=(SPACING["2"], 0))

        value = tk.Label(inner, text=CURRENCY + "0.00" if key not in
                         ("count", "budget_over", "cycle_count") else "0",
                         bg=COLORS["card"], fg=color,
                         font=theme.display_font("4xl" if primary else "3xl", "bold"))
        value.pack(anchor="w", pady=(SPACING["2"], 0))

        caption = tk.Label(inner, text="All time", bg=COLORS["card"],
                           fg=COLORS["text_muted"], font=theme.font("xs"))
        caption.pack(anchor="w")

        self.stat_values[key] = value
        self.stat_captions[key] = caption
        return card

    # ------------------------------------------------------------------
    # Responsive layout
    # ------------------------------------------------------------------
    def _on_resize(self, event):
        if event.widget is not self:
            return
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(80, lambda: self._apply_layout(event.width))

    def _apply_layout(self, width):
        self._resize_job = None
        columns = 4 if width >= 1040 else (2 if width >= 620 else 1)
        if columns != self._columns:
            self._columns = columns
            self._grid_cards(self.kpi_frame, self.kpi_cards, columns)
            self._grid_cards(self.insight_frame, self.insight_cards, columns)

        bottom_columns = 2 if width >= 900 else 1
        if bottom_columns != self._bottom_columns:
            self._bottom_columns = bottom_columns
            for frame in (self.chart_card, self.recent_card):
                frame.grid_forget()
            if bottom_columns == 2:
                self.bottom.rowconfigure(0, weight=1)
                self.bottom.rowconfigure(1, weight=0)
                self.bottom.columnconfigure(0, weight=3, uniform="")
                self.bottom.columnconfigure(1, weight=2, uniform="")
                self.chart_card.grid(row=0, column=0, sticky="nsew",
                                     padx=(0, SPACING["3"]))
                self.recent_card.grid(row=0, column=1, sticky="nsew")
            else:
                self.bottom.rowconfigure(0, weight=1)
                self.bottom.rowconfigure(1, weight=1)
                self.bottom.columnconfigure(0, weight=1, uniform="")
                self.bottom.columnconfigure(1, weight=0, uniform="")
                self.chart_card.grid(row=0, column=0, sticky="nsew",
                                     pady=(0, SPACING["3"]))
                self.recent_card.grid(row=1, column=0, sticky="nsew")

    @staticmethod
    def _grid_cards(parent, cards, columns):
        for card in cards:
            card.grid_forget()
        for index in range(4):
            parent.columnconfigure(index, weight=1 if index < columns else 0,
                                   uniform="kpi" if index < columns else "")
        for index, card in enumerate(cards):
            row, column = divmod(index, columns)
            card.grid(row=row, column=column, sticky="nsew",
                      padx=(0 if column == 0 else SPACING["3"], 0),
                      pady=(0, SPACING["3"]))

    # ------------------------------------------------------------------
    # Period handling
    # ------------------------------------------------------------------
    def _period_key(self):
        selected = self.period_var.get()
        for label, key in PERIODS:
            if label == selected:
                return key
        return "all"

    def _update_custom_visibility(self):
        if self._period_key() == "custom":
            self.custom_frame.pack(side="left", pady=(SPACING["1"], 0))
        else:
            self.custom_frame.pack_forget()

    def _get_period_bounds(self):
        """Return (start_date, end_date) or (None, None) for the period."""
        choice = self._period_key()
        today = date.today()
        if choice == "this_month":
            start = date(today.year, today.month, 1)
            end = date(today.year, today.month,
                       calendar.monthrange(today.year, today.month)[1])
            return start, end
        if choice == "last_month":
            first_this = date(today.year, today.month, 1)
            last_month = first_this - timedelta(days=1)
            start = date(last_month.year, last_month.month, 1)
            end = date(last_month.year, last_month.month,
                       calendar.monthrange(last_month.year, last_month.month)[1])
            return start, end
        if choice == "this_year":
            return date(today.year, 1, 1), date(today.year, 12, 31)
        if choice == "custom":
            try:
                start = date.fromisoformat(self.start_entry.get().strip())
                end = date.fromisoformat(self.end_entry.get().strip())
                if start > end:
                    start, end = end, start
                return start, end
            except ValueError:
                return None, None
        return None, None

    @staticmethod
    def _period_label_text(start, end):
        if start is None and end is None:
            return "All time"
        if start is not None and end is not None:
            return "%s to %s" % (start.isoformat(), end.isoformat())
        if start is not None:
            return "Since %s" % start.isoformat()
        return "Until %s" % end.isoformat()

    def _on_period_change(self):
        self._update_custom_visibility()
        self.refresh()

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    def _show_recent_empty(self, visible):
        if visible:
            self.recent_empty.place(relx=0.5, rely=0.5)
        else:
            self.recent_empty.place_forget()

    def _draw_chart(self):
        if self.canvas.winfo_exists():
            charts.draw_line_chart(self.canvas, self.chart_labels,
                                   self.chart_series)

    def _fill_recent(self, records):
        """Replace the recent-transactions list."""
        self.recent_tree.delete(*self.recent_tree.get_children())
        for record in records:
            raw_date = record["transaction_date"]
            date_text = (raw_date.strftime("%b %d")
                         if hasattr(raw_date, "strftime") else str(raw_date))
            amount_text = CURRENCY + "{:,.2f}".format(float(record["amount"]))
            self.recent_tree.insert(
                "", "end",
                values=(date_text, record["category"], amount_text),
                tags=(record["type"],),
            )
        self._show_recent_empty(not records)

    def refresh(self):
        """Reload totals, chart data and recent transactions."""
        user_id = self.app.current_user["id"]
        start, end = self._get_period_bounds()
        try:
            income, expense, net, count = queries.get_totals(user_id, start, end)
            monthly = queries.get_monthly_summary_range(user_id, start, end)
            recent = queries.get_recent_transactions(user_id, 5)

            budget_report = queries.get_budget_report(user_id)
            today = date.today()
            relevant = []
            for b in budget_report:
                try:
                    end_d = b.get("end_date")
                    start_d = b.get("start_date")
                    if end_d and hasattr(end_d, "year") and end_d < today:
                        # skip very old expired budgets to avoid misleading totals
                        continue
                except Exception:
                    pass
                relevant.append(b)
            total_budgeted = sum((b["budgeted"] for b in relevant),
                                 Decimal("0"))
            total_actual = sum((b["actual"] for b in relevant),
                               Decimal("0"))
            total_remaining = total_budgeted - total_actual
            over_budget_count = sum(1 for b in relevant if b["is_over"])
            if not relevant:
                self.stat_captions["budget_remaining"].config(
                    text="no active budgets")
            else:
                self.stat_captions["budget_remaining"].config(
                    text="across %d budget(s)" % len(relevant))

            cycles = queries.get_cycles(user_id)
            active_cycles = [c for c in cycles
                             if c["status"] in ("planned", "active")]
            latest_cycle_net = Decimal("0")
            latest_cycle_name = "No active cycle"
            if active_cycles:
                latest = active_cycles[0]
                _inc, _exp, latest_cycle_net, _n = queries.get_cycle_totals(
                    latest["id"], user_id)
                latest_cycle_name = latest["crop_name"] or "Latest cycle"
        except mysql.connector.Error as exc:
            messagebox.showerror(
                "Database Error",
                "Could not load the dashboard.\n\n" + str(exc))
            return

        period_text = self._period_label_text(start, end)

        # Primary cards
        self.stat_values["income"].config(
            text=CURRENCY + "{:,.2f}".format(float(income)))
        self.stat_values["expense"].config(
            text=CURRENCY + "{:,.2f}".format(float(expense)))
        self.stat_values["net"].config(
            text=CURRENCY + "{:,.2f}".format(float(net)),
            fg=COLORS["income"] if net >= 0 else COLORS["expense"])
        self.stat_values["count"].config(text="{:,.0f}".format(int(count)))

        for key in ("income", "expense", "net", "count"):
            self.stat_captions[key].config(text=period_text)

        # Insight cards
        self.stat_values["budget_remaining"].config(
            text=CURRENCY + "{:,.2f}".format(float(total_remaining)),
            fg=COLORS["income"] if total_remaining >= 0 else COLORS["expense"])
        if not relevant:
            self.stat_captions["budget_remaining"].config(
                text="no active budgets")
        else:
            self.stat_captions["budget_remaining"].config(
                text="across %d budget(s)" % len(relevant))

        self.stat_values["budget_over"].config(
            text=str(over_budget_count),
            fg=COLORS["expense"] if over_budget_count else COLORS["income"])
        self.stat_captions["budget_over"].config(
            text="budgets exceeded" if over_budget_count else "all within budget")

        self.stat_values["cycle_net"].config(
            text=CURRENCY + "{:,.2f}".format(float(latest_cycle_net)),
            fg=COLORS["income"] if latest_cycle_net >= 0 else COLORS["expense"])
        self.stat_captions["cycle_net"].config(text=latest_cycle_name)

        self.stat_values["cycle_count"].config(text=str(len(active_cycles)))
        self.stat_captions["cycle_count"].config(text="planned or active")

        self.period_label.config(text="Showing: %s" % period_text)
        self.chart_period.config(text=period_text)

        # Choose aggregation based on period for better readability
        key = self._period_key()
        use_daily = key in ("this_month", "last_month", "custom")
        if not use_daily and key == "all":
            # If all history is within a short span, prefer daily for a more useful line
            try:
                daily_all = queries.get_daily_summary_range(user_id, start, end)
                if len(daily_all) > 1:
                    use_daily = True
                    daily = daily_all
                else:
                    daily = []
            except Exception:
                daily = []
        if use_daily and 'daily' not in locals():
            try:
                daily = queries.get_daily_summary_range(user_id, start, end)
            except Exception:
                daily = []
        if use_daily and daily:
            self.chart_labels = [
                (row["date"].strftime("%b %d") if hasattr(row["date"], "strftime") else str(row["date"])[-5:])
                for row in daily
            ]
            self.chart_series = [
                {
                    "label": "Income",
                    "values": [float(row["income"]) for row in daily],
                    "color": COLORS["income"],
                },
                {
                    "label": "Expenses",
                    "values": [float(row["expense"]) for row in daily],
                    "color": COLORS["expense"],
                },
            ]
        elif key in ("this_month", "last_month", "custom"):
            try:
                daily = queries.get_daily_summary_range(user_id, start, end)
            except Exception:
                daily = []
            if daily:
                self.chart_labels = [
                    (row["date"].strftime("%b %d") if hasattr(row["date"], "strftime") else str(row["date"])[-5:])
                    for row in daily
                ]
                self.chart_series = [
                    {"label": "Income", "values": [float(row["income"]) for row in daily], "color": COLORS["income"]},
                    {"label": "Expenses", "values": [float(row["expense"]) for row in daily], "color": COLORS["expense"]},
                ]
            else:
                self.chart_labels = [calendar.month_abbr[row["month"]]
                                     for row in monthly]
                self.chart_series = [
                    {"label": "Income", "values": [float(row["income"]) for row in monthly], "color": COLORS["income"]},
                    {"label": "Expenses", "values": [float(row["expense"]) for row in monthly], "color": COLORS["expense"]},
                ]
        else:
            self.chart_labels = [calendar.month_abbr[row["month"]]
                                 for row in monthly]
            self.chart_series = [
                {
                    "label": "Income",
                    "values": [float(row["income"]) for row in monthly],
                    "color": COLORS["income"],
                },
                {
                    "label": "Expenses",
                    "values": [float(row["expense"]) for row in monthly],
                    "color": COLORS["expense"],
                },
            ]
        self._draw_chart()
        self._fill_recent(recent)
        if hasattr(self, "scroll"):
            self.scroll.scroll_to_top()
