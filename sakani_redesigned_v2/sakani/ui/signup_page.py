"""Sakani sign-up screen with validation and password hashing."""

import tkinter as tk
from tkinter import messagebox

import mysql.connector

from config import COLORS, SPACING
from database import queries
from models import auth
from ui import brand, theme


class SignupPage(tk.Frame):
    """Create-account screen."""

    def __init__(self, master, app):
        super().__init__(master, bg=COLORS["background"])
        self.app = app
        self.show_var = tk.BooleanVar(value=False)
        self._build()

    def _build(self):
        """Create the branding panel and the sign-up form card."""
        side = tk.Frame(self, bg=COLORS["deep_forest"], width=400)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        self.side_canvas = tk.Canvas(side, bg=COLORS["deep_forest"],
                                     highlightthickness=0, bd=0)
        self.side_canvas.pack(fill="both", expand=True)
        self.side_canvas.bind("<Configure>", self._draw_side)

        right = tk.Frame(self, bg=COLORS["background"])
        right.pack(side="right", fill="both", expand=True)

        card = theme.Card(right, padding=SPACING["5"])
        card.place(relx=0.5, rely=0.5, anchor="center")
        form = tk.Frame(card.body, bg=COLORS["card"])
        form.pack()
        tk.Frame(form, bg=COLORS["card"], width=330, height=1).pack()

        tk.Label(form, text="Create account", bg=COLORS["card"],
                 fg=COLORS["text"],
                 font=theme.display_font("5xl", "bold")).pack(anchor="w")
        tk.Label(form, text="Start tracking your farm today.",
                 bg=COLORS["card"], fg=COLORS["text_secondary"],
                 font=theme.font("base")).pack(anchor="w",
                                                pady=(SPACING["1"], SPACING["3"]))

        self.full_name = theme.LabeledEntry(form, "Full name", required=True)
        self.full_name.pack(fill="x", pady=(0, SPACING["2"]))
        self.email = theme.LabeledEntry(form, "Email address", required=True)
        self.email.pack(fill="x", pady=(0, SPACING["2"]))
        self.password = theme.LabeledEntry(form, "Password", show="*",
                                           required=True)
        self.password.pack(fill="x", pady=(0, SPACING["2"]))
        self.confirm = theme.LabeledEntry(form, "Confirm password", show="*",
                                          required=True)
        self.confirm.pack(fill="x")

        tk.Checkbutton(
            form, text="Show passwords", variable=self.show_var,
            command=self._toggle_password, bg=COLORS["card"],
            activebackground=COLORS["card"], fg=COLORS["text_secondary"],
            font=theme.font("sm"), bd=0, highlightthickness=0,
            cursor="hand2").pack(anchor="w", pady=(SPACING["2"], 0))

        self.error_label = tk.Label(
            form, text="", bg=COLORS["card"], fg=COLORS["danger"],
            font=theme.font("sm"), justify="left", wraplength=320, anchor="w")
        self.error_label.pack(fill="x", pady=(SPACING["2"], SPACING["1"]))

        theme.RoundedButton(
            form, "Create Account", command=self._signup, width=320,
            height=42, parent_bg=COLORS["card"]).pack(fill="x")

        link = tk.Label(
            form, text="Already have an account?  Log In", bg=COLORS["card"],
            fg=COLORS["primary"], font=theme.font("sm", "bold"),
            cursor="hand2")
        link.pack(pady=(SPACING["3"], 0))
        link.bind("<Button-1>", lambda _event: self.app.show_login())

        for field in (self.full_name, self.email, self.password, self.confirm):
            field.entry.bind("<Return>", lambda _event: self._signup())

    def _draw_side(self, event):
        """Redraw the decorative green panel when it is resized."""
        brand.draw_brand_panel(self.side_canvas, event.width, event.height)

    def _toggle_password(self):
        """Show or hide both password fields."""
        show = "" if self.show_var.get() else "*"
        self.password.entry.config(show=show)
        self.confirm.entry.config(show=show)

    def _show_error(self, message):
        """Display a validation message under the fields."""
        self.error_label.config(text=message)

    def _signup(self):
        """Validate the form, hash the password and create the account."""
        full_name = self.full_name.get()
        email = self.email.get()
        password = self.password.get()
        confirm = self.confirm.get()

        ok, message = auth.validate_signup(full_name, email, password, confirm)
        if not ok:
            self._show_error(message)
            return

        try:
            existing = queries.get_user_by_email(email)
            if existing is not None:
                self._show_error("This email is already registered.")
                return
            password_hash, salt = auth.hash_password(password)
            queries.create_user(full_name, email, password_hash, salt)
        except mysql.connector.Error as exc:
            messagebox.showerror("Database Error",
                                 "Could not create the account.\n\n" + str(exc))
            return

        messagebox.showinfo("Account created",
                            "Welcome to Sakani! Please log in.")
        self.app.show_login()

    def refresh(self):
        """Clear all fields whenever the page is shown."""
        self._show_error("")
        self.full_name.clear()
        self.email.clear()
        self.password.clear()
        self.confirm.clear()
        self.show_var.set(False)
        self._toggle_password()
        self.full_name.focus()
