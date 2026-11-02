"""Sakani login screen with a split forest-green and cream layout."""

import tkinter as tk
from tkinter import messagebox

import mysql.connector

from config import APP_NAME, COLORS, SPACING
from database import queries
from models import auth
from ui import brand, theme


class LoginPage(tk.Frame):
    """Email and password login screen."""

    def __init__(self, master, app):
        super().__init__(master, bg=COLORS["background"])
        self.app = app
        self.show_var = tk.BooleanVar(value=False)
        self._build()

    def _build(self):
        """Create the branding panel and the login form card."""
        side = tk.Frame(self, bg=COLORS["deep_forest"], width=440)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        self.side_canvas = tk.Canvas(side, bg=COLORS["deep_forest"],
                                     highlightthickness=0, bd=0)
        self.side_canvas.pack(fill="both", expand=True)
        self.side_canvas.bind("<Configure>", self._draw_side)

        right = tk.Frame(self, bg=COLORS["background"])
        right.pack(side="right", fill="both", expand=True)

        card = theme.Card(right, padding=SPACING["6"])
        card.place(relx=0.5, rely=0.5, anchor="center")
        form = tk.Frame(card.body, bg=COLORS["card"])
        form.pack()
        tk.Frame(form, bg=COLORS["card"], width=330, height=1).pack()

        tk.Label(form, text="Welcome back", bg=COLORS["card"],
                 fg=COLORS["text"],
                 font=theme.display_font("5xl", "bold")).pack(anchor="w")
        tk.Label(form, text="Log in to keep tracking your farm.",
                 bg=COLORS["card"], fg=COLORS["text_secondary"],
                 font=theme.font("base")).pack(anchor="w", pady=(SPACING["1"], SPACING["5"]))

        self.email = theme.LabeledEntry(form, "Email address", required=True)
        self.email.pack(fill="x", pady=(0, SPACING["3"]))
        self.password = theme.LabeledEntry(form, "Password", show="*",
                                           required=True)
        self.password.pack(fill="x")

        tk.Checkbutton(
            form, text="Show password", variable=self.show_var,
            command=self._toggle_password, bg=COLORS["card"],
            activebackground=COLORS["card"], fg=COLORS["text_secondary"],
            font=theme.font("sm"), bd=0, highlightthickness=0,
            cursor="hand2").pack(anchor="w", pady=(SPACING["2"], 0))

        self.error_label = tk.Label(
            form, text="", bg=COLORS["card"], fg=COLORS["danger"],
            font=theme.font("sm"), justify="left", wraplength=320, anchor="w")
        self.error_label.pack(fill="x", pady=(SPACING["2"], SPACING["1"]))

        theme.RoundedButton(
            form, "Log In", command=self._login, width=320, height=42,
            parent_bg=COLORS["card"]).pack(fill="x", pady=(SPACING["2"], 0))

        link = tk.Label(
            form, text="Don't have an account?  Sign Up", bg=COLORS["card"],
            fg=COLORS["primary"], font=theme.font("sm", "bold"),
            cursor="hand2")
        link.pack(pady=(SPACING["4"], 0))
        link.bind("<Button-1>", lambda _event: self.app.show_signup())

        self.email.entry.bind("<Return>", lambda _event: self._login())
        self.password.entry.bind("<Return>", lambda _event: self._login())

    def _draw_side(self, event):
        """Redraw the decorative green panel when it is resized."""
        brand.draw_brand_panel(self.side_canvas, event.width, event.height)

    def _toggle_password(self):
        """Show or hide the password characters."""
        self.password.entry.config(show="" if self.show_var.get() else "*")

    def _show_error(self, message):
        """Display a validation or login message under the fields."""
        self.error_label.config(text=message)

    def _login(self):
        """Validate the form, check the password and open the app."""
        email = self.email.get().strip()
        password = self.password.get()
        ok, message = auth.validate_login(email, password)
        if not ok:
            self._show_error(message)
            return

        try:
            user = queries.get_user_by_email(email)
        except mysql.connector.Error as exc:
            messagebox.showerror("Database Error",
                                 "Could not log in.\n\n" + str(exc))
            return

        if user is None or not auth.verify_password(
                password, user["password_hash"], user["salt"]):
            self._show_error("Incorrect email or password.")
            return

        self._show_error("")
        self.app.login_success(user)

    def refresh(self):
        """Reset the form whenever the page is shown again."""
        self._show_error("")
        self.password.clear()
        self.show_var.set(False)
        self.password.entry.config(show="*")
        self.email.focus()
