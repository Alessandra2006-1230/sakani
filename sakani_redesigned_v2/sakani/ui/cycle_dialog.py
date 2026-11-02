"""Modal dialog used to create and edit a crop production cycle."""

import tkinter as tk
from tkinter import ttk

import mysql.connector

from config import COLORS, SPACING
from database import queries
from models import cycle as cycle_model
from ui import theme


class CycleDialog(tk.Toplevel):
    """Modal window that creates or edits one production cycle."""

    def __init__(self, master, app, cycle=None, on_saved=None):
        super().__init__(master)
        self.app = app
        self.cycle = cycle
        self.on_saved = on_saved
        self.status_var = tk.StringVar(value="planned")

        self.title("Add Production Cycle" if cycle is None
                   else "Edit Production Cycle")
        self.configure(bg=COLORS["card"])
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self._build()
        if cycle is not None:
            self._load_values()
        theme.center_window(self, master)
        self.bind("<Escape>", lambda _event: self.destroy())
        self.crop_name.focus()

    def _build(self):
        """Create the cycle form inside the dialog."""
        container = tk.Frame(self, bg=COLORS["card"])
        container.pack(fill="both", expand=True, padx=SPACING["6"],
                       pady=SPACING["5"])

        heading = "Add Production Cycle" if self.cycle is None \
            else "Edit Production Cycle"
        tk.Label(container, text=heading, bg=COLORS["card"],
                 fg=COLORS["text"],
                 font=theme.font("3xl", "bold")).pack(anchor="w")
        tk.Label(container,
                 text="Group transactions under a crop and follow it to harvest.",
                 bg=COLORS["card"], fg=COLORS["text_secondary"],
                 font=theme.font("sm")).pack(anchor="w",
                                              pady=(SPACING["1"], SPACING["4"]))

        self.crop_name = theme.LabeledEntry(
            container, "Crop name", required=True)
        self.crop_name.pack(fill="x", pady=(0, SPACING["2"]))

        row = tk.Frame(container, bg=COLORS["card"])
        row.pack(fill="x", pady=(0, SPACING["2"]))
        self.variety = theme.LabeledEntry(row, "Variety", width=18)
        self.variety.pack(side="left", fill="x", expand=True,
                          padx=(0, SPACING["2"]))
        self.plot_name = theme.LabeledEntry(row, "Plot / field", width=18)
        self.plot_name.pack(side="left", fill="x", expand=True)

        tk.Label(container, text="Dates", bg=COLORS["card"],
                 fg=COLORS["text_muted"],
                 font=theme.font("xs")).pack(anchor="w", pady=(SPACING["2"], 0))
        row = tk.Frame(container, bg=COLORS["card"])
        row.pack(fill="x", pady=(SPACING["1"], SPACING["2"]))
        self.start_date = theme.LabeledEntry(
            row, "Start date", required=True, hint="YYYY-MM-DD")
        self.start_date.pack(side="left", fill="x", expand=True,
                             padx=(0, SPACING["2"]))
        self.expected_harvest = theme.LabeledEntry(
            row, "Expected harvest", hint="YYYY-MM-DD")
        self.expected_harvest.pack(side="left", fill="x", expand=True,
                                   padx=(0, SPACING["2"]))
        self.actual_harvest = theme.LabeledEntry(
            row, "Actual harvest", hint="YYYY-MM-DD")
        self.actual_harvest.pack(side="left", fill="x", expand=True)

        row = tk.Frame(container, bg=COLORS["card"])
        row.pack(fill="x", pady=(SPACING["2"], SPACING["2"]))
        status_box = tk.Frame(row, bg=COLORS["card"])
        status_box.pack(side="left", fill="x", expand=True,
                        padx=(0, SPACING["2"]))
        tk.Label(status_box, text="Status", bg=COLORS["card"],
                 fg=COLORS["text"], font=theme.font("sm")).pack(
                     anchor="w", pady=(0, SPACING["1"]))
        self.status_combo = ttk.Combobox(
            status_box, textvariable=self.status_var, state="readonly",
            values=list(cycle_model.CYCLE_STATUSES), font=theme.font("base"))
        self.status_combo.pack(fill="x")

        notes_box = tk.Frame(row, bg=COLORS["card"])
        notes_box.pack(side="left", fill="x", expand=True)
        self.notes = theme.LabeledEntry(notes_box, "Notes")
        self.notes.pack(fill="x")

        self.error_label = tk.Label(
            container, text="", bg=COLORS["card"], fg=COLORS["danger"],
            font=theme.font("sm"), justify="left", wraplength=460, anchor="w")
        self.error_label.pack(fill="x", pady=(SPACING["2"], 0))

        buttons = tk.Frame(container, bg=COLORS["card"])
        buttons.pack(fill="x", pady=(SPACING["4"], 0))
        theme.RoundedButton(buttons, "Cancel", command=self.destroy,
                            width=96, height=36, style="secondary",
                            parent_bg=COLORS["card"]).pack(side="right")
        theme.RoundedButton(buttons, "Save Cycle", command=self._save,
                            width=136, height=36,
                            parent_bg=COLORS["card"]).pack(
                                side="right", padx=(0, SPACING["2"]))

    def _load_values(self):
        """Fill the form from an existing cycle."""
        self.crop_name.set(self.cycle["crop_name"] or "")
        self.variety.set(self.cycle["variety"] or "")
        self.plot_name.set(self.cycle["plot_name"] or "")
        self.start_date.set(self._as_date_text(self.cycle["start_date"]))
        self.expected_harvest.set(
            self._as_date_text(self.cycle["expected_harvest_date"]))
        self.actual_harvest.set(
            self._as_date_text(self.cycle["actual_harvest_date"]))
        self.status_var.set(self.cycle["status"])
        self.notes.set(self.cycle["notes"] or "")

    @staticmethod
    def _as_date_text(value):
        if value is None:
            return ""
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d")
        return str(value)

    def _save(self):
        """Validate the form and save the cycle."""
        ok, message, values = cycle_model.validate_cycle_fields({
            "crop_name": self.crop_name.get(),
            "variety": self.variety.get(),
            "plot_name": self.plot_name.get(),
            "start_date": self.start_date.get(),
            "expected_harvest_date": self.expected_harvest.get(),
            "actual_harvest_date": self.actual_harvest.get(),
            "status": self.status_var.get(),
            "notes": self.notes.get(),
        })
        if not ok:
            self.error_label.config(text=message)
            return

        status = values["status"]
        if self.cycle is not None:
            current_status = self.cycle["status"]
            if status != current_status and not cycle_model.is_valid_transition(
                    current_status, status):
                self.error_label.config(
                    text="Status cannot move from %s to %s." % (
                        current_status, status))
                return

        payload = (
            values["crop_name"], values["variety"], values["plot_name"],
            values["start_date"], values["expected_harvest_date"],
            values["actual_harvest_date"], status, values["notes"],
        )
        try:
            if self.cycle is None:
                queries.add_cycle(self.app.current_user["id"], *payload)
            else:
                queries.update_cycle(int(self.cycle["id"]),
                                     self.app.current_user["id"], *payload)
        except mysql.connector.Error:
            self.error_label.config(
                text="Could not save the production cycle. Please try again.")
            return

        if callable(self.on_saved):
            self.on_saved()
        self.destroy()
