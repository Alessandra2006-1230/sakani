"""Left navigation sidebar shown after a successful login."""

import tkinter as tk
from tkinter import messagebox

from config import APP_NAME, COLORS, LOGO_PATH, SPACING, TAGLINE_MAIN
from ui import theme

MENU_ITEMS = [
    ("dashboard", "Dashboard", "dashboard"),
    ("add", "Add Transaction", "add"),
    ("history", "History Transactions", "history"),
    ("summary", "Financial Summary", "summary"),
    ("cycles", "Crop Cycles", "cycles"),
    ("budgets", "Budgets", "budgets"),
]


class NavItem(tk.Canvas):
    """One sidebar navigation row drawn on a canvas.

    Canvas drawing (instead of emoji glyphs) keeps icons consistent across
    Linux desktops with incomplete emoji font coverage.
    """

    HEIGHT = 44

    def __init__(self, master, label, icon, command):
        super().__init__(master, height=self.HEIGHT, bg=COLORS["deep_forest"],
                         highlightthickness=0, bd=0, cursor="hand2",
                         takefocus=True)
        self.label = label
        self.icon_name = icon
        self.command = command
        self.active = False
        self.hovered = False
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", lambda _event: self.command())
        self.bind("<Return>", lambda _event: self.command())
        self.bind("<space>", lambda _event: self.command())
        self.bind("<Configure>", lambda _event: self._draw())

    def set_active(self, active):
        self.active = bool(active)
        self._draw()

    def _on_enter(self, _event):
        self.hovered = True
        self._draw()

    def _on_leave(self, _event):
        self.hovered = False
        self._draw()

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 40)
        height = self.HEIGHT

        if self.active:
            fill, fg = COLORS["forest_raised"], COLORS["white"]
            icon_color = COLORS["gold_accent"]
        elif self.hovered:
            fill, fg = COLORS["forest_hover"], COLORS["white"]
            icon_color = COLORS["on_forest"]
        else:
            fill, fg = COLORS["deep_forest"], COLORS["on_forest"]
            icon_color = COLORS["on_forest_muted"]

        theme.rounded_rect(self, 0, 2, width - 2, height - 2,
                           radius=12, fill=fill, outline="")
        if self.active:
            theme.rounded_rect(self, 0, 12, 3, height - 12, radius=2,
                               fill=COLORS["gold_accent"], outline="")

        theme.draw_icon(self, self.icon_name, 18, icon_color, cx=26, cy=height / 2)
        self.create_text(46, height / 2, text=self.label, anchor="w",
                         fill=fg, font=theme.font("lg", "bold" if self.active else "normal"))


class Sidebar(tk.Frame):
    """Deep forest sidebar with navigation, user info and log out."""

    WIDTH = 250

    def __init__(self, master, app):
        super().__init__(master, bg=COLORS["deep_forest"], width=self.WIDTH)
        self.pack_propagate(False)
        self.app = app
        self.active_key = None
        self.buttons = {}
        self.logo_photo = None
        self._build()

    # -- construction ----------------------------------------------------
    def _build(self):
        """Create the logo, menu buttons, user card and log out button."""
        header = tk.Frame(self, bg=COLORS["deep_forest"])
        header.pack(fill="x", padx=SPACING["4"], pady=(SPACING["6"], SPACING["4"]))

        self._build_logo(header)

        text = tk.Frame(header, bg=COLORS["deep_forest"])
        text.pack(side="left", padx=(SPACING["3"], 0))
        tk.Label(text, text=APP_NAME, bg=COLORS["deep_forest"],
                 fg=COLORS["white"],
                 font=theme.display_font("4xl", "bold")).pack(anchor="w")
        tk.Label(text, text=TAGLINE_MAIN, bg=COLORS["deep_forest"],
                 fg=COLORS["gold_accent"], font=theme.font("xs")).pack(anchor="w")

        # Hairline divider between the brand block and the menu.
        tk.Frame(self, bg=COLORS["forest_line"], height=1).pack(
            fill="x", padx=SPACING["5"], pady=(0, SPACING["4"]))

        tk.Label(self, text="WORKSPACE", bg=COLORS["deep_forest"],
                 fg=COLORS["on_forest_muted"], font=theme.font("xs", "bold")).pack(
                     anchor="w", padx=SPACING["5"] + 4, pady=(0, SPACING["2"]))

        for key, label, icon in MENU_ITEMS:
            item = NavItem(self, label, icon,
                           command=lambda name=key: self.app.open_page(name))
            item.pack(fill="x", padx=SPACING["3"], pady=2)
            self.buttons[key] = item

        tk.Frame(self, bg=COLORS["deep_forest"]).pack(fill="both", expand=True)

        self._build_user_card()

    def _build_logo(self, parent):
        """Load ``assets/images/sakani_logo.png`` or draw a placeholder."""
        size = 46
        holder = tk.Frame(parent, bg=COLORS["deep_forest"], width=size, height=size)
        holder.pack(side="left")
        holder.pack_propagate(False)

        if LOGO_PATH.is_file():
            try:
                photo = tk.PhotoImage(file=str(LOGO_PATH))
                factor = max(1, round(photo.width() / size))
                if factor > 1:
                    photo = photo.subsample(factor, factor)
                self.logo_photo = photo
                tk.Label(holder, image=photo, bg=COLORS["deep_forest"]).pack(
                    expand=True)
                return
            except tk.TclError:
                pass

        canvas = tk.Canvas(holder, width=size, height=size,
                           bg=COLORS["deep_forest"], highlightthickness=0)
        canvas.pack()
        theme.rounded_rect(canvas, 1, 1, size - 1, size - 1, radius=14,
                           fill=COLORS["forest_raised"],
                           outline=COLORS["forest_line"])
        theme.draw_icon(canvas, "leaf", 26, COLORS["gold_accent"],
                        cx=size / 2, cy=size / 2)

    def _build_user_card(self):
        """Build the signed-in user card with a log out action."""
        user = self.app.current_user or {}
        full_name = (user.get("full_name") or "Farmer").strip()
        email = (user.get("email") or "").strip()
        initials = "".join(part[0] for part in full_name.split()[:2]).upper() or "S"

        card = tk.Frame(self, bg=COLORS["forest_raised"],
                        highlightbackground=COLORS["forest_line"],
                        highlightthickness=1)
        card.pack(fill="x", padx=SPACING["3"], pady=(SPACING["2"], SPACING["3"]))

        row = tk.Frame(card, bg=COLORS["forest_raised"])
        row.pack(fill="x", padx=SPACING["3"], pady=(SPACING["3"], SPACING["2"]))

        avatar = tk.Canvas(row, width=36, height=36, bg=COLORS["forest_raised"],
                           highlightthickness=0)
        avatar.pack(side="left")
        avatar.create_oval(0, 0, 36, 36, fill=COLORS["gold_accent"], outline="")
        avatar.create_text(18, 18, text=initials, fill=COLORS["deep_forest"],
                           font=theme.font("lg", "bold"))

        info = tk.Frame(row, bg=COLORS["forest_raised"])
        info.pack(side="left", padx=(SPACING["2"], 0), fill="x", expand=True)
        tk.Label(info, text=full_name, bg=COLORS["forest_raised"],
                 fg=COLORS["white"], font=theme.font("sm", "bold"),
                 anchor="w").pack(fill="x")
        if email:
            tk.Label(info, text=email, bg=COLORS["forest_raised"],
                     fg=COLORS["on_forest_muted"], font=theme.font("xs"),
                     anchor="w").pack(fill="x")

        theme.RoundedButton(card, "Log Out", command=self._logout,
                            width=200, height=34, style="sidebar",
                            parent_bg=COLORS["forest_raised"]).pack(
                                fill="x", padx=SPACING["3"], pady=(0, SPACING["3"]))

    # -- navigation ------------------------------------------------------
    def set_active(self, key):
        """Highlight the menu item for the current page."""
        self.active_key = key
        for name, button in self.buttons.items():
            button.set_active(name == key)

    def _logout(self):
        """Ask for confirmation, then return to the login screen."""
        if messagebox.askyesno("Log Out", "Are you sure you want to log out?"):
            self.app.logout()
