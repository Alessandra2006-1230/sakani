"""Modal dialog for break-even analysis on a production cycle."""

import csv
import tkinter as tk
from decimal import Decimal, InvalidOperation
from tkinter import filedialog, messagebox

from config import COLORS, CURRENCY, SPACING
from models import breakeven
from ui import theme


class BreakevenDialog(tk.Toplevel):
    """Modal window for break-even analysis on a cycle.

    Recorded cycle expenses are used as the costs to cover. Results are
    estimates and are labelled as such.
    """

    def __init__(self, master, app, cycle, on_done=None):
        super().__init__(master)
        self.app = app
        self.cycle = cycle
        self.on_done = on_done
        self.price_var = tk.StringVar(value="")
        self.qty_var = tk.StringVar(value="")
        self._result = None

        self.title("Break-even Analysis — %s" % (cycle["crop_name"] or "Cycle"))
        self.configure(bg=COLORS["card"])
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self._build()
        theme.center_window(self, master)
        self.bind("<Escape>", lambda _event: self.destroy())
        self.price_entry.focus()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _build(self):
        container = tk.Frame(self, bg=COLORS["card"])
        container.pack(fill="both", expand=True, padx=SPACING["6"],
                       pady=SPACING["5"])

        tk.Label(container, text="Break-even Analysis", bg=COLORS["card"],
                 fg=COLORS["text"],
                 font=theme.font("3xl", "bold")).pack(anchor="w")
        tk.Label(container,
                 text="See how many units you need to sell to cover this "
                      "cycle's recorded expenses.",
                 bg=COLORS["card"], fg=COLORS["text_secondary"],
                 font=theme.font("sm")).pack(anchor="w",
                                              pady=(SPACING["1"], SPACING["3"]))

        self._build_summary(container)

        body = tk.Frame(container, bg=COLORS["card"])
        body.pack(fill="both", expand=True, pady=(SPACING["3"], 0))
        body.columnconfigure(0, weight=1, uniform="be")
        body.columnconfigure(1, weight=1, uniform="be")

        inputs = tk.Frame(body, bg=COLORS["card"])
        inputs.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING["3"]))
        tk.Label(inputs, text="Your inputs", bg=COLORS["card"],
                 fg=COLORS["text"],
                 font=theme.font("xl", "bold")).pack(anchor="w",
                                                     pady=(0, SPACING["2"]))

        price_box = tk.Frame(inputs, bg=COLORS["card"])
        price_box.pack(fill="x", pady=(0, SPACING["2"]))
        self.price_entry = theme.LabeledEntry(
            price_box, "Expected selling price per unit (%s)" % CURRENCY,
            required=True)
        self.price_entry.pack(fill="x")

        qty_box = tk.Frame(inputs, bg=COLORS["card"])
        qty_box.pack(fill="x", pady=(0, SPACING["2"]))
        self.qty_entry = theme.LabeledEntry(
            qty_box, "Expected quantity (optional)")
        self.qty_entry.pack(fill="x")

        self.error_label = tk.Label(
            inputs, text="", bg=COLORS["card"], fg=COLORS["danger"],
            font=theme.font("sm"), justify="left", wraplength=280, anchor="w")
        self.error_label.pack(fill="x", pady=(SPACING["2"], 0))

        theme.RoundedButton(inputs, "Calculate", command=self._calculate,
                            width=130, height=38,
                            parent_bg=COLORS["card"]).pack(anchor="w",
                                                           pady=(SPACING["3"], 0))

        self.results_frame = tk.Frame(body, bg=COLORS["surface_alt"],
                                      highlightbackground=COLORS["border"],
                                      highlightthickness=1)
        self.results_frame.grid(row=0, column=1, sticky="nsew")
        self._show_placeholder()

        self.assumptions = tk.Label(
            container,
            text="Assumptions: break-even uses only recorded cycle expenses "
                 "as costs to cover. Income, taxes, depreciation, and "
                 "unrecorded costs are excluded. Results are estimates.",
            bg=COLORS["card"], fg=COLORS["text_muted"],
            font=theme.font("xs"), wraplength=640, justify="left")
        self.assumptions.pack(anchor="w", pady=(SPACING["3"], 0))

        self._build_buttons(container)

    def _build_summary(self, parent):
        summary = tk.Frame(parent, bg=COLORS["pale_mint"])
        summary.pack(fill="x")
        inner = tk.Frame(summary, bg=COLORS["pale_mint"])
        inner.pack(fill="x", padx=SPACING["4"], pady=SPACING["3"])

        name = self.cycle["crop_name"] or "Untitled cycle"
        if self.cycle["variety"]:
            name += " — " + self.cycle["variety"]
        tk.Label(inner, text=name, bg=COLORS["pale_mint"],
                 fg=COLORS["text"],
                 font=theme.font("xl", "bold")).pack(anchor="w")
        if self.cycle["plot_name"]:
            tk.Label(inner, text="Plot: %s" % self.cycle["plot_name"],
                     bg=COLORS["pale_mint"], fg=COLORS["text_secondary"],
                     font=theme.font("xs")).pack(anchor="w")

        income = self.cycle.get("cycle_income", Decimal("0"))
        expense = self.cycle.get("cycle_costs", Decimal("0"))
        net = self.cycle.get("cycle_net", Decimal("0"))
        row = tk.Frame(inner, bg=COLORS["pale_mint"])
        row.pack(fill="x", pady=(SPACING["2"], 0))
        for label, value, color in (
                ("Recorded income", income, COLORS["income"]),
                ("Recorded expenses", expense, COLORS["expense"]),
                ("Net", net, COLORS["income"] if net >= 0
                 else COLORS["expense"])):
            cell = tk.Frame(row, bg=COLORS["pale_mint"])
            cell.pack(side="left", padx=(0, SPACING["5"]))
            tk.Label(cell, text=label, bg=COLORS["pale_mint"],
                     fg=COLORS["text_secondary"],
                     font=theme.font("xs")).pack(anchor="w")
            tk.Label(cell, text=CURRENCY + "{:,.2f}".format(float(value)),
                     bg=COLORS["pale_mint"], fg=color,
                     font=theme.font("lg", "bold")).pack(anchor="w")

    def _build_buttons(self, parent):
        buttons = tk.Frame(parent, bg=COLORS["card"])
        buttons.pack(fill="x", pady=(SPACING["3"], 0))
        theme.RoundedButton(buttons, "Close", command=self.destroy,
                            width=96, height=36, style="secondary",
                            parent_bg=COLORS["card"]).pack(side="right")
        self.export_button = theme.RoundedButton(
            buttons, "Export CSV", command=self._export_result,
            width=120, height=36, style="primary",
            parent_bg=COLORS["card"])
        self.export_button.pack(side="right", padx=(0, SPACING["2"]))
        self.export_button.set_enabled(False)

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------
    def _show_placeholder(self):
        for child in list(self.results_frame.winfo_children()):
            child.destroy()
        tk.Label(self.results_frame, text="Results", bg=COLORS["surface_alt"],
                 fg=COLORS["text"],
                 font=theme.font("xl", "bold")).pack(anchor="w",
                                                     padx=SPACING["4"],
                                                     pady=(SPACING["4"], 0))
        tk.Label(self.results_frame,
                 text="Enter a selling price and press Calculate.",
                 bg=COLORS["surface_alt"], fg=COLORS["text_secondary"],
                 font=theme.font("sm"), wraplength=260,
                 justify="left").pack(anchor="w", padx=SPACING["4"],
                                      pady=(SPACING["1"], SPACING["4"]))

    def _calculate(self):
        self.error_label.config(text="")

        price_text = self.price_entry.get().strip()
        if not price_text:
            self.error_label.config(
                text="Please enter a selling price per unit.")
            return
        try:
            price = Decimal(price_text.replace(",", ""))
        except (InvalidOperation, ValueError):
            self.error_label.config(text="Please enter a valid price.")
            return
        if price <= 0:
            self.error_label.config(
                text="Selling price must be greater than zero.")
            return

        qty = None
        qty_text = self.qty_entry.get().strip()
        if qty_text:
            try:
                qty = int(qty_text)
            except ValueError:
                self.error_label.config(
                    text="Expected quantity must be a whole number.")
                return
            if qty <= 0:
                self.error_label.config(
                    text="Expected quantity must be positive.")
                return

        cycle_costs = self.cycle.get("cycle_costs", Decimal("0"))
        if cycle_costs <= 0:
            self.error_label.config(
                text="This cycle has no recorded expenses to analyse.")
            return

        result = breakeven.analyze_cycle_break_even(
            self.cycle["id"], self.app.current_user["id"],
            float(price), qty)
        if "error" in result:
            self.error_label.config(text=result["error"])
            return

        self._result = result
        self._show_results(result)

    def _show_results(self, result):
        for child in list(self.results_frame.winfo_children()):
            child.destroy()

        tk.Label(self.results_frame, text="Results", bg=COLORS["surface_alt"],
                 fg=COLORS["text"],
                 font=theme.font("xl", "bold")).pack(anchor="w",
                                                     padx=SPACING["4"],
                                                     pady=(SPACING["4"], SPACING["2"]))

        self._result_row("Costs to cover",
                         CURRENCY + "{:,.2f}".format(
                             float(result["cycle_costs"])))
        self._result_row("Break-even quantity",
                         "{:,} units".format(
                             int(result["break_even_quantity"])),
                         emphasis=True)
        self._result_row("Break-even revenue",
                         CURRENCY + "{:,.2f}".format(
                             float(result["break_even_revenue"])))

        if "expected_revenue" in result:
            self._result_row("Expected quantity",
                             "{:,} units".format(result["expected_quantity"]))
            self._result_row("Expected revenue",
                             CURRENCY + "{:,.2f}".format(
                                 float(result["expected_revenue"])))
            net = result.get("estimated_net")
            if net is not None:
                self._result_row(
                    "Estimated net result",
                    CURRENCY + "{:,.2f}".format(float(net)),
                    color=COLORS["income"] if net >= 0 else COLORS["expense"],
                    emphasis=True)

        tk.Frame(self.results_frame, bg=COLORS["border"], height=1).pack(
            fill="x", padx=SPACING["4"], pady=SPACING["2"])
        tk.Label(self.results_frame,
                 text="Break-even is the number of units you must sell at "
                      "this price to cover recorded expenses.",
                 bg=COLORS["surface_alt"], fg=COLORS["text_muted"],
                 font=theme.font("xs"), wraplength=260,
                 justify="left").pack(anchor="w", padx=SPACING["4"],
                                      pady=(0, SPACING["4"]))
        self.export_button.set_enabled(True)

    def _result_row(self, label, value, color=None, emphasis=False):
        row = tk.Frame(self.results_frame, bg=COLORS["surface_alt"])
        row.pack(fill="x", padx=SPACING["4"], pady=2)
        tk.Label(row, text=label, bg=COLORS["surface_alt"],
                 fg=COLORS["text_secondary"],
                 font=theme.font("sm")).pack(side="left")
        tk.Label(row, text=value, bg=COLORS["surface_alt"],
                 fg=color or COLORS["text"],
                 font=theme.font("lg" if emphasis else "sm", "bold")).pack(
                     side="right")

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def _export_result(self):
        if self._result is None:
            messagebox.showinfo("Export", "Calculate a result first.")
            return
        result = self._result
        path = filedialog.asksaveasfilename(
            title="Save break-even analysis as CSV",
            defaultextension=".csv",
            initialfile="sakani_breakeven_%s.csv" % self.cycle["id"],
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.writer(handle)
                writer.writerow(["Item", "Value"])
                writer.writerow(["Cycle ID", self.cycle["id"]])
                writer.writerow(["Crop Name", self.cycle["crop_name"] or ""])
                writer.writerow(["Variety", self.cycle["variety"] or ""])
                writer.writerow(["Plot", self.cycle["plot_name"] or ""])
                writer.writerow(["Recorded Expenses",
                                 "%.2f" % float(result["cycle_costs"])])
                writer.writerow(["Recorded Income",
                                 "%.2f" % float(result["cycle_income"])])
                writer.writerow(["Cycle Net",
                                 "%.2f" % float(result["cycle_net"])])
                writer.writerow(["Selling Price per Unit",
                                 "%.2f" % float(result["price_per_unit"])])
                writer.writerow(["Break-even Quantity",
                                 int(result["break_even_quantity"])])
                writer.writerow(["Break-even Revenue",
                                 "%.2f" % float(result["break_even_revenue"])])
                if "expected_quantity" in result:
                    writer.writerow(["Expected Quantity",
                                     result["expected_quantity"]])
                    writer.writerow(["Expected Revenue",
                                     "%.2f" % float(result["expected_revenue"])])
                    writer.writerow(["Estimated Net",
                                     "%.2f" % float(result["estimated_net"])])
                writer.writerow([])
                writer.writerow(["Assumptions"])
                writer.writerow([
                    "Break-even calculated using recorded cycle expenses as "
                    "costs to cover.",
                    "Income, taxes, depreciation, and unrecorded costs are "
                    "excluded.",
                    "Results are estimates, not professional financial advice.",
                ])
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))
            return

        messagebox.showinfo("Export complete",
                            "Break-even analysis saved to:\n%s" % path)
