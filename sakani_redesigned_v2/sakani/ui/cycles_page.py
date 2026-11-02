"""Crop Production Cycles page: list cycles with income/expense/net results."""

import tkinter as tk
from tkinter import messagebox

import mysql.connector

from config import COLORS, CURRENCY, SPACING
from database import queries
from ui import theme
from ui.breakeven_dialog import BreakevenDialog
from ui.cycle_dialog import CycleDialog


class CyclesPage(tk.Frame):
    """User-scoped list of production cycles with per-cycle totals."""

    def __init__(self, master, app):
        super().__init__(master, bg=COLORS["background"])
        self.app = app
        self.cycles = {}
        self.active_dialog = None
        self.cards = []
        self._columns = 0
        self._resize_job = None
        self._build()
        self.bind("<Configure>", self._on_resize)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _build(self):
        """Create header, action bar and a responsive, scrollable grid."""
        theme.PageHero(
            self, "Crop Production Cycles",
            "Track each crop from planting to harvest and see its result.",
            badge="Sakani \u00b7 Crop Cycles", crumb="Crop Cycles",
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
        theme.RoundedButton(actions, "Add Cycle", command=self._add,
                            width=128, height=38,
                            parent_bg=COLORS["background"]).pack(side="right")

        self.grid_frame = tk.Frame(self.content, bg=COLORS["background"])
        self.grid_frame.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Responsive layout
    # ------------------------------------------------------------------
    def _on_resize(self, event):
        if event.widget is not self:
            return
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(80, lambda: self._reflow(event.width))

    def _reflow(self, width=None):
        self._resize_job = None
        if width is None:
            width = self.winfo_width()
        columns = 1 if width < 780 else (2 if width < 1460 else 3)
        if columns == self._columns:
            return
        self._columns = columns
        self._layout_cards(columns)

    def _layout_cards(self, columns):
        for card, _labels in self.cards:
            card.grid_forget()
        for index in range(3):
            self.grid_frame.columnconfigure(
                index, weight=1 if index < columns else 0,
                uniform="cycle" if index < columns else "")
        for index, (card, labels) in enumerate(self.cards):
            row, column = divmod(index, columns)
            card.grid(row=row, column=column, sticky="nsew",
                      padx=(0 if column == 0 else SPACING["3"], 0),
                      pady=(0, SPACING["3"]))
            if columns == 1:
                wrap = max(240, self.winfo_width() - 120)
            else:
                wrap = max(200, (self.winfo_width() - 90) // columns - 160)
            for label in labels:
                label.configure(wraplength=wrap)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _add(self):
        """Open the create-cycle dialog."""
        self.active_dialog = CycleDialog(self, self.app, cycle=None,
                                         on_saved=self._load)
        return self.active_dialog

    def _edit(self, cycle):
        """Open the edit-cycle dialog for one cycle."""
        self.active_dialog = CycleDialog(self, self.app, cycle=cycle,
                                         on_saved=self._load)
        return self.active_dialog

    def _delete(self, cycle_id):
        """Delete a cycle after confirmation."""
        if not messagebox.askyesno(
                "Delete Production Cycle",
                "Delete this production cycle?\n\n"
                "Linked transactions will be kept but unassigned."):
            return
        try:
            queries.delete_cycle(cycle_id, self.app.current_user["id"])
        except mysql.connector.Error as exc:
            messagebox.showerror("Database Error",
                                 "Could not delete the cycle.\n\n" + str(exc))
            return
        self._load()

    def _breakeven(self, cycle):
        """Open break-even analysis for a cycle."""
        cycle_with_totals = dict(cycle)
        try:
            income, expense, net, _count = queries.get_cycle_totals(
                cycle["id"], self.app.current_user["id"])
            cycle_with_totals["cycle_income"] = income
            cycle_with_totals["cycle_costs"] = expense
            cycle_with_totals["cycle_net"] = net
        except mysql.connector.Error as exc:
            messagebox.showerror(
                "Database Error",
                "Could not load cycle totals.\n\n" + str(exc))
            return
        BreakevenDialog(self, self.app, cycle_with_totals)

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    def _load(self):
        """Reload the cycle list from the database."""
        user_id = self.app.current_user["id"]
        try:
            cycles = queries.get_cycles(user_id)
        except mysql.connector.Error as exc:
            messagebox.showerror("Database Error",
                                 "Could not load production cycles.\n\n" + str(exc))
            return

        for child in list(self.grid_frame.winfo_children()):
            child.destroy()
        self.cycles = {}
        self.cards = []

        if not cycles:
            self._show_empty_state()
            return

        for cycle in cycles:
            self._build_cycle_card(cycle, user_id)

        self._columns = 0
        self._reflow()

    def _show_empty_state(self):
        """Show a friendly empty state with an add action."""
        card = theme.Card(self.grid_frame, padding=0)
        card.pack(fill="both", expand=True)
        theme.EmptyState(
            card.body,
            title="No production cycles yet",
            message="Create your first cycle to group transactions by crop "
                    "and see profit per harvest.",
            icon="cycles",
            action_text="Add Your First Cycle",
            action_command=self._add,
        ).pack(fill="both", expand=True, pady=SPACING["6"])

    def _build_cycle_card(self, cycle, user_id):
        """Create one cycle card with details, totals and actions."""
        try:
            income, expense, net, count = queries.get_cycle_totals(
                cycle["id"], user_id)
        except mysql.connector.Error as exc:
            messagebox.showerror(
                "Database Error",
                "Could not load cycle totals.\n\n" + str(exc))
            return

        card = tk.Frame(self.grid_frame, bg=COLORS["card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1, bd=0)
        inner = tk.Frame(card, bg=COLORS["card"])
        inner.pack(fill="both", expand=True, padx=SPACING["5"],
                   pady=SPACING["5"])

        wrap_labels = []

        # Header: crop name / variety + status badge
        header = tk.Frame(inner, bg=COLORS["card"])
        header.pack(fill="x", pady=(0, SPACING["3"]))

        name_box = tk.Frame(header, bg=COLORS["card"])
        name_box.pack(side="left", fill="x", expand=True)
        crop_name = cycle["crop_name"] or "Untitled crop"
        name_label = tk.Label(name_box, text=crop_name, bg=COLORS["card"],
                              fg=COLORS["text"], font=theme.font("2xl", "bold"),
                              anchor="w", justify="left")
        name_label.pack(anchor="w", fill="x")
        wrap_labels.append(name_label)
        if cycle["variety"]:
            variety_label = tk.Label(
                name_box, text="Variety: %s" % cycle["variety"],
                bg=COLORS["card"], fg=COLORS["text_secondary"],
                font=theme.font("sm"), anchor="w", justify="left")
            variety_label.pack(anchor="w", fill="x")
            wrap_labels.append(variety_label)

        status = cycle["status"] or "planned"
        theme.StatusBadge(header, status).pack(side="right", anchor="n",
                                               padx=(SPACING["2"], 0))

        # Details grid
        details = tk.Frame(inner, bg=COLORS["card"])
        details.pack(fill="x", pady=(0, SPACING["3"]))
        details.columnconfigure(0, weight=1)
        details.columnconfigure(1, weight=1)
        detail_rows = [
            ("Plot", cycle["plot_name"] or "—"),
            ("Started", self._as_date(cycle["start_date"])),
            ("Expected harvest", self._as_date(cycle["expected_harvest_date"])),
            ("Actual harvest", self._as_date(cycle["actual_harvest_date"])),
        ]
        for index, (label, value) in enumerate(detail_rows):
            cell = tk.Frame(details, bg=COLORS["card"])
            cell.grid(row=index // 2, column=index % 2, sticky="ew",
                      pady=1, padx=(0, SPACING["2"]))
            tk.Label(cell, text=label, bg=COLORS["card"],
                     fg=COLORS["text_muted"], font=theme.font("xs"),
                     anchor="w").pack(fill="x")
            value_label = tk.Label(cell, text=value, bg=COLORS["card"],
                                   fg=COLORS["text"], font=theme.font("sm"),
                                   anchor="w", justify="left")
            value_label.pack(fill="x")
            wrap_labels.append(value_label)

        # Financial strip
        totals = tk.Frame(inner, bg=COLORS["pale_mint"])
        totals.pack(fill="x", pady=(0, SPACING["3"]))
        totals_inner = tk.Frame(totals, bg=COLORS["pale_mint"])
        totals_inner.pack(fill="x", padx=SPACING["3"], pady=SPACING["2"])
        for column in range(3):
            totals_inner.columnconfigure(column, weight=1)

        for column, (label, value, color) in enumerate((
                ("Income", income, COLORS["income"]),
                ("Expenses", expense, COLORS["expense"]),
                ("Net", net, COLORS["income"] if net >= 0 else COLORS["expense"]))):
            cell = tk.Frame(totals_inner, bg=COLORS["pale_mint"])
            cell.grid(row=0, column=column, sticky="w")
            tk.Label(cell, text=label, bg=COLORS["pale_mint"],
                     fg=COLORS["text_secondary"],
                     font=theme.font("xs")).pack(anchor="w")
            tk.Label(cell, text=CURRENCY + "{:,.2f}".format(float(value)),
                     bg=COLORS["pale_mint"], fg=color,
                     font=theme.font("lg", "bold")).pack(anchor="w")

        tk.Label(inner, text="%d transaction(s) linked" % count,
                 bg=COLORS["card"], fg=COLORS["text_muted"],
                 font=theme.font("xs")).pack(anchor="w", pady=(0, SPACING["3"]))

        # Actions
        actions = tk.Frame(inner, bg=COLORS["card"])
        actions.pack(fill="x")
        theme.RoundedButton(actions, "Edit",
                            command=lambda c=cycle: self._edit(c),
                            width=72, height=32, style="secondary",
                            parent_bg=COLORS["card"]).pack(side="left")
        theme.RoundedButton(actions, "Delete",
                            command=lambda c=cycle: self._delete(c["id"]),
                            width=76, height=32, style="danger",
                            parent_bg=COLORS["card"]).pack(
                                side="left", padx=(SPACING["2"], 0))
        theme.RoundedButton(actions, "Break-even",
                            command=lambda c=cycle: self._breakeven(c),
                            width=104, height=32, style="primary",
                            parent_bg=COLORS["card"]).pack(side="right")

        self.cards.append((card, wrap_labels))
        self.cycles[str(cycle["id"])] = cycle

    @staticmethod
    def _as_date(value):
        if value is None:
            return "—"
        if hasattr(value, "strftime"):
            return value.strftime("%b %d, %Y")
        return str(value)

    def refresh(self):
        """Reload the cycle list whenever the page is shown."""
        self._load()
        if hasattr(self, "scroll"):
            self.scroll.scroll_to_top()
