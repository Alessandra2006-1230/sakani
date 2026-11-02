"""Sakani visual theme: design tokens, ttk styles and reusable widgets.

All visual helpers live here so pages stay free of duplicated styling code.
The "glass" look is simulated with layered flat surfaces, hairline borders and
generous spacing -- Tkinter has no real backdrop blur, so none is claimed.
"""

import sys
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import ttk

from config import (
    COLORS,
    FONT_BODY_CANDIDATES,
    FONT_DISPLAY_CANDIDATES,
    FONT_FALLBACK,
    FONT_FAMILY,
    FONT_SIZES,
    RADIUS,
    SPACING,
)

_font_family = FONT_FAMILY
_display_family = FONT_DISPLAY_CANDIDATES[-1]


def _size(size):
    if isinstance(size, str):
        return FONT_SIZES.get(size, FONT_SIZES["base"])
    return size


def font(size="base", weight="normal"):
    """Return a body font tuple using the resolved family.

    ``size`` may be a number (points) or one of the keys in ``FONT_SIZES``.
    """
    return (_font_family, _size(size), weight)


def display_font(size="5xl", weight="bold"):
    """Return a serif display font tuple for titles and large figures."""
    return (_display_family, _size(size), weight)


def _first_available(candidates, families, default):
    lowered = {name.lower(): name for name in families}
    for name in candidates:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return default


def load_bundled_fonts():
    """Make the .ttf/.otf files in ``assets/fonts`` usable by this process.

    Works on Windows (private fonts, nothing is installed). On other systems
    the fonts simply need to be installed normally. Failures are ignored so a
    missing or unsupported font never stops the app from starting.
    """
    if not sys.platform.startswith("win"):
        return
    fonts_dir = Path(__file__).resolve().parent.parent / "assets" / "fonts"
    if not fonts_dir.is_dir():
        return
    try:
        import ctypes
        add_font = ctypes.windll.gdi32.AddFontResourceExW
        for path in sorted(fonts_dir.iterdir()):
            if path.suffix.lower() in (".ttf", ".otf"):
                add_font(str(path), 0x10, 0)  # FR_PRIVATE
    except Exception:  # pragma: no cover - platform specific
        pass


def setup_theme(root):
    """Resolve the font families and configure all ttk styles."""
    global _font_family, _display_family
    load_bundled_fonts()
    try:
        families = set(tkfont.families(root))
        _font_family = _first_available(
            FONT_BODY_CANDIDATES, families,
            FONT_FALLBACK if FONT_FALLBACK in families else "TkDefaultFont")
        _display_family = _first_available(
            FONT_DISPLAY_CANDIDATES, families, _font_family)
    except tk.TclError:
        _font_family = FONT_FALLBACK
        _display_family = _font_family

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.option_add("*Font", font("base"))

    # --- frames ---------------------------------------------------------
    style.configure("TFrame", background=COLORS["background"])
    style.configure("Card.TFrame", background=COLORS["card"])
    style.configure("Surface.TFrame", background=COLORS["surface"])
    style.configure("PaleMint.TFrame", background=COLORS["pale_mint"])

    # --- labels ---------------------------------------------------------
    style.configure("TLabel", background=COLORS["background"],
                    foreground=COLORS["text"], font=font("base"))
    style.configure("Card.TLabel", background=COLORS["card"],
                    foreground=COLORS["text"], font=font("base"))
    style.configure("Secondary.TLabel", background=COLORS["background"],
                    foreground=COLORS["text_secondary"], font=font("sm"))
    style.configure("CardSecondary.TLabel", background=COLORS["card"],
                    foreground=COLORS["text_secondary"], font=font("sm"))
    style.configure("Muted.TLabel", background=COLORS["background"],
                    foreground=COLORS["text_muted"], font=font("xs"))
    style.configure("CardMuted.TLabel", background=COLORS["card"],
                    foreground=COLORS["text_muted"], font=font("xs"))
    style.configure("PageTitle.TLabel", background=COLORS["background"],
                    foreground=COLORS["text"], font=display_font("5xl", "bold"))
    style.configure("CardTitle.TLabel", background=COLORS["card"],
                    foreground=COLORS["text"], font=display_font("2xl", "bold"))
    style.configure("Stat.TLabel", background=COLORS["card"],
                    foreground=COLORS["text"], font=display_font("5xl", "bold"))

    # --- inputs ---------------------------------------------------------
    style.configure("TEntry", padding=(12, 8),
                    fieldbackground=COLORS["input_bg"],
                    bordercolor=COLORS["input_border"],
                    lightcolor=COLORS["input_border"],
                    darkcolor=COLORS["input_border"],
                    insertcolor=COLORS["text"])
    style.map("TEntry",
              bordercolor=[("focus", COLORS["primary"])],
              lightcolor=[("focus", COLORS["primary"])],
              darkcolor=[("focus", COLORS["primary"])])
    style.configure("TCombobox", padding=(12, 7),
                    fieldbackground=COLORS["input_bg"],
                    background=COLORS["input_bg"],
                    bordercolor=COLORS["input_border"],
                    arrowcolor=COLORS["text_secondary"])
    style.map("TCombobox",
              fieldbackground=[("readonly", COLORS["input_bg"])],
              bordercolor=[("focus", COLORS["primary"])],
              arrowcolor=[("active", COLORS["primary"])])
    style.configure("TSpinbox", padding=SPACING["1"])
    style.configure("TCheckbutton", background=COLORS["card"],
                    foreground=COLORS["text_secondary"], font=font("sm"))
    style.map("TCheckbutton", background=[("active", COLORS["card"])])
    style.configure("TRadiobutton", background=COLORS["card"],
                    foreground=COLORS["text"], font=font("base"))
    style.map("TRadiobutton", background=[("active", COLORS["card"])])

    # --- tables ---------------------------------------------------------
    style.configure("Treeview", background=COLORS["white"],
                    fieldbackground=COLORS["white"],
                    foreground=COLORS["text"], rowheight=38,
                    font=font("sm"), borderwidth=0, relief="flat")
    style.configure("Treeview.Heading", background=COLORS["surface_alt"],
                    foreground=COLORS["text_secondary"], font=font("sm", "bold"),
                    padding=(SPACING["3"], SPACING["2"]), borderwidth=0,
                    relief="flat")
    style.map("Treeview.Heading", background=[("active", COLORS["pale_mint"])])
    style.map("Treeview",
              background=[("selected", COLORS["pale_mint"])],
              foreground=[("selected", COLORS["text"])])

    # --- scrollbars -----------------------------------------------------
    style.configure("Vertical.TScrollbar", background=COLORS["border"],
                    troughcolor=COLORS["background"], borderwidth=0,
                    arrowsize=12, relief="flat")
    style.configure("Horizontal.TScrollbar", background=COLORS["border"],
                    troughcolor=COLORS["background"], borderwidth=0,
                    arrowsize=12, relief="flat")
    style.map("Vertical.TScrollbar", background=[("active", COLORS["text_muted"])])

    # --- frames / tabs --------------------------------------------------
    style.configure("TLabelframe", background=COLORS["card"],
                    bordercolor=COLORS["border"])
    style.configure("TLabelframe.Label", background=COLORS["card"],
                    foreground=COLORS["text"], font=font("sm", "bold"))
    style.configure("TNotebook", background=COLORS["background"], borderwidth=0)
    style.configure("TNotebook.Tab", background=COLORS["background"],
                    foreground=COLORS["text_secondary"],
                    font=font("sm", "bold"),
                    padding=(SPACING["4"], SPACING["2"]), borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", COLORS["card"])],
              foreground=[("selected", COLORS["primary"])])

    # --- buttons --------------------------------------------------------
    style.configure("Primary.TButton", background=COLORS["primary"],
                    foreground=COLORS["white"], font=font("base", "bold"),
                    padding=(SPACING["3"], SPACING["2"]), borderwidth=0)
    style.map("Primary.TButton",
              background=[("active", COLORS["primary_dark"]),
                          ("disabled", COLORS["border"])],
              foreground=[("disabled", COLORS["text_muted"])])
    style.configure("Secondary.TButton", background=COLORS["card"],
                    foreground=COLORS["primary"], font=font("base", "bold"),
                    padding=(SPACING["3"], SPACING["2"]), borderwidth=1,
                    bordercolor=COLORS["border"])
    style.map("Secondary.TButton",
              background=[("active", COLORS["pale_mint"])],
              foreground=[("disabled", COLORS["text_muted"])])
    style.configure("Danger.TButton", background=COLORS["expense"],
                    foreground=COLORS["white"], font=font("base", "bold"),
                    padding=(SPACING["3"], SPACING["2"]), borderwidth=0)
    style.map("Danger.TButton", background=[("active", COLORS["danger_dark"])])
    style.configure("Ghost.TButton", background=COLORS["card"],
                    foreground=COLORS["text_secondary"], font=font("base"),
                    padding=(SPACING["2"], SPACING["1"]), borderwidth=0)
    style.map("Ghost.TButton", background=[("active", COLORS["pale_mint"])],
              foreground=[("active", COLORS["primary"])])


# ---------------------------------------------------------------------------
# Canvas drawing helpers
# ---------------------------------------------------------------------------
def rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    """Draw a smooth rounded rectangle on a canvas and return its item id."""
    radius = max(1, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# Backwards-compatible private name.
_round_rect = rounded_rect


def _hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def blend(start, end, amount):
    """Return the colour ``amount`` (0-1) of the way from ``start`` to ``end``."""
    a = _hex_to_rgb(start)
    b = _hex_to_rgb(end)
    return "#%02X%02X%02X" % tuple(
        int(round(a[i] + (b[i] - a[i]) * amount)) for i in range(3))


def draw_gradient(canvas, x1, y1, x2, y2, start, end, vertical=False,
                  steps=48, tag="gradient"):
    """Fill a rectangle with a smooth two-colour gradient made of thin bands."""
    steps = max(2, int(steps))
    span = (y2 - y1) if vertical else (x2 - x1)
    for index in range(steps):
        color = blend(start, end, index / (steps - 1))
        low = span * index / steps
        high = span * (index + 1) / steps + 1  # 1px overlap hides seams
        if vertical:
            canvas.create_rectangle(x1, y1 + low, x2, y1 + high,
                                    fill=color, outline="", tags=tag)
        else:
            canvas.create_rectangle(x1 + low, y1, x1 + high, y2,
                                    fill=color, outline="", tags=tag)


def center_window(window, master):
    """Place a modal window in the middle of its parent window."""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = master.winfo_rootx() + max(0, (master.winfo_width() - width) // 2)
    y = master.winfo_rooty() + max(0, (master.winfo_height() - height) // 2)
    window.geometry("+%d+%d" % (x, y))


def _icon_commands(name):
    """Return drawing commands on a 24x24 grid for a named icon.

    Each command is a tuple ``(kind, coords, width)`` where kind is ``line``,
    ``rect`` or ``oval``. Icons stay vector-like and font-independent.
    """
    icons = {
        "dashboard": [
            ("rect", (3, 3, 10, 10), 0), ("rect", (14, 3, 21, 10), 0),
            ("rect", (3, 14, 10, 21), 0), ("rect", (14, 14, 21, 21), 0),
        ],
        "add": [
            ("line", (12, 4, 12, 20), 2), ("line", (4, 12, 20, 12), 2),
        ],
        "history": [
            ("rect", (4, 3, 20, 21), 1.6), ("line", (8, 8, 16, 8), 1.6),
            ("line", (8, 12, 16, 12), 1.6), ("line", (8, 16, 13, 16), 1.6),
        ],
        "summary": [
            ("line", (3, 21, 21, 21), 1.6), ("rect", (6, 12, 9, 20), 0),
            ("rect", (11, 8, 14, 20), 0), ("rect", (16, 4, 19, 20), 0),
        ],
        "cycles": [
            ("line", (12, 21, 12, 10), 1.8),
            ("oval", (5, 5, 13, 13), 1.6), ("oval", (11, 8, 20, 17), 1.6),
        ],
        "budgets": [
            ("rect", (3, 6, 21, 19), 1.6), ("line", (3, 10, 21, 10), 1.6),
            ("oval", (15, 12, 19, 16), 1.6),
        ],
        "income": [
            ("line", (12, 4, 12, 20), 2), ("line", (5, 11, 12, 4), 2),
            ("line", (19, 11, 12, 4), 2),
        ],
        "expense": [
            ("line", (12, 4, 12, 20), 2), ("line", (5, 13, 12, 20), 2),
            ("line", (19, 13, 12, 20), 2),
        ],
        "net": [
            ("line", (4, 18, 10, 11), 2), ("line", (10, 11, 14, 15), 2),
            ("line", (14, 15, 20, 6), 2),
        ],
        "transactions": [
            ("rect", (4, 4, 20, 20), 1.6), ("line", (8, 9, 16, 9), 1.6),
            ("line", (8, 13, 16, 13), 1.6), ("line", (8, 17, 12, 17), 1.6),
        ],
        "budget_remaining": [
            ("oval", (3, 3, 21, 21), 1.6), ("line", (8, 12, 11, 16), 1.8),
            ("line", (11, 16, 17, 8), 1.8),
        ],
        "over_budget": [
            ("line", (12, 3, 12, 15), 2),
            ("oval", (10, 18, 14, 22), 0),
            ("line", (12, 1, 12, 3), 0),
        ],
        "cycle_net": [
            ("line", (12, 21, 12, 9), 1.8),
            ("oval", (4, 3, 12, 11), 1.6), ("oval", (12, 6, 21, 15), 1.6),
        ],
        "active_cycles": [
            ("oval", (4, 4, 20, 20), 1.6), ("line", (12, 8, 12, 13), 1.8),
            ("line", (12, 13, 16, 15), 1.8),
        ],
        "leaf": [
            ("line", (12, 21, 12, 12), 1.8),
            ("oval", (4, 3, 13, 12), 1.6), ("oval", (11, 5, 21, 15), 1.6),
        ],
        "warning": [
            ("line", (12, 3, 21, 20), 1.6), ("line", (21, 20, 3, 20), 1.6),
            ("line", (3, 20, 12, 3), 1.6), ("line", (12, 9, 12, 14), 1.8),
            ("oval", (11, 16, 13, 18), 0),
        ],
        "search": [
            ("oval", (4, 4, 16, 16), 1.8), ("line", (15, 15, 21, 21), 2),
        ],
        "download": [
            ("line", (12, 3, 12, 15), 1.8), ("line", (7, 10, 12, 15), 1.8),
            ("line", (17, 10, 12, 15), 1.8), ("line", (4, 20, 20, 20), 1.8),
        ],
        "user": [
            ("oval", (8, 3, 16, 11), 1.6), ("line", (4, 21, 4, 17), 1.6),
            ("line", (4, 17, 20, 17), 1.6), ("line", (20, 17, 20, 21), 1.6),
        ],
        "logout": [
            ("line", (4, 4, 4, 20), 1.8), ("line", (4, 4, 12, 4), 1.8),
            ("line", (4, 20, 12, 20), 1.8), ("line", (10, 12, 21, 12), 1.8),
            ("line", (17, 8, 21, 12), 1.8), ("line", (17, 16, 21, 12), 1.8),
        ],
        "calendar": [
            ("rect", (3, 5, 21, 21), 1.6), ("line", (3, 10, 21, 10), 1.6),
            ("line", (8, 2, 8, 7), 1.6), ("line", (16, 2, 16, 7), 1.6),
        ],
    }
    return icons.get(name, [])


def draw_icon(canvas, name, size, color, cx=None, cy=None):
    """Draw a named icon centred on (cx, cy) of the given size."""
    canvas.delete("icon")
    if cx is None:
        cx = size / 2
    if cy is None:
        cy = size / 2
    scale = size / 24.0
    commands = _icon_commands(name)
    for kind, coords, width in commands:
        scaled = [c * scale for c in coords]
        if kind == "line":
            x1, y1, x2, y2 = scaled
            canvas.create_line(cx - size / 2 + x1, cy - size / 2 + y1,
                               cx - size / 2 + x2, cy - size / 2 + y2,
                               fill=color, width=max(1, int(round(width * scale))),
                               capstyle="round", tags="icon")
        elif kind == "rect":
            x1, y1, x2, y2 = scaled
            canvas.create_rectangle(cx - size / 2 + x1, cy - size / 2 + y1,
                                    cx - size / 2 + x2, cy - size / 2 + y2,
                                    outline=color, width=max(1, int(round(1.6 * scale))),
                                    tags="icon")
        elif kind == "oval":
            x1, y1, x2, y2 = scaled
            if width == 0:
                canvas.create_oval(cx - size / 2 + x1, cy - size / 2 + y1,
                                   cx - size / 2 + x2, cy - size / 2 + y2,
                                   fill=color, outline=color, tags="icon")
            else:
                canvas.create_oval(cx - size / 2 + x1, cy - size / 2 + y1,
                                   cx - size / 2 + x2, cy - size / 2 + y2,
                                   outline=color,
                                   width=max(1, int(round(width * scale))),
                                   tags="icon")


class Icon(tk.Canvas):
    """A small canvas that draws a vector icon (no emoji fonts needed)."""

    def __init__(self, master, name, size=20, color=COLORS["text_secondary"],
                 bg=None, **kwargs):
        if bg is None:
            bg = master.cget("bg")
        super().__init__(master, width=size, height=size, bg=bg,
                         highlightthickness=0, bd=0, **kwargs)
        self._name = name
        self._size = size
        self._color = color
        draw_icon(self, name, size, color)

    def set_color(self, color):
        """Recolour the icon in place."""
        self._color = color
        draw_icon(self, self._name, self._size, color)


class RoundedButton(tk.Canvas):
    """A flat, rounded button drawn on a Tkinter Canvas.

    Supports both the design-system ``style=`` keyword and the legacy
    ``color=/hover_color=/text_color=`` keywords used by older pages.
    """

    STYLES = {
        "primary": (COLORS["primary"], COLORS["primary_dark"], COLORS["white"]),
        "secondary": (COLORS["card"], COLORS["pale_mint"], COLORS["primary"]),
        "danger": (COLORS["expense"], COLORS["danger_dark"], COLORS["white"]),
        "ghost": (COLORS["card"], COLORS["pale_mint"], COLORS["text_secondary"]),
        "gold": (COLORS["gold_accent"], COLORS["gold_dark"], COLORS["deep_forest"]),
        "sidebar": (COLORS["forest_hover"], COLORS["forest_line"], COLORS["on_forest"]),
        "muted": (COLORS["background"], COLORS["border"], COLORS["text_secondary"]),
    }

    def __init__(self, master, text, command=None, width=160, height=38,
                 style="primary", parent_bg=None, radius=None,
                 color=None, hover_color=None, text_color=None, **kwargs):
        if parent_bg is None:
            parent_bg = master.cget("bg")
        super().__init__(master, width=width, height=height, bg=parent_bg,
                         highlightthickness=0, bd=0, cursor="hand2",
                         takefocus=True, **kwargs)
        self.command = command
        self.enabled = True
        self._width = width
        self._height = height
        self._radius = RADIUS["lg"] if radius is None else radius
        self._text = text
        self._focused = False
        self._pressed = False

        base, hover, fg = self.STYLES.get(style, self.STYLES["primary"])
        self.color = color or base
        self.hover_color = hover_color or hover
        self.text_color = text_color or fg

        self._shape = None
        self._label = None
        self._draw()

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Return>", lambda _event: self._invoke())
        self.bind("<space>", lambda _event: self._invoke())
        self.bind("<Configure>", self._on_configure)

    # -- drawing ---------------------------------------------------------
    def _draw(self):
        self.delete("all")
        w = max(self._width, 8)
        h = max(self._height, 8)
        fill = self.color if self.enabled else COLORS["border"]
        if self.enabled and (self._focused or self._pressed):
            fill = self.hover_color if self._pressed else self.color
        self._shape = rounded_rect(self, 1, 1, w - 1, h - 1, self._radius,
                                   fill=fill, outline="")
        if self._focused:
            rounded_rect(self, 1, 1, w - 1, h - 1, self._radius,
                         fill="", outline=COLORS["primary_light"], width=2)
        fg = self.text_color if self.enabled else COLORS["text_muted"]
        self._label = self.create_text(w / 2, h / 2, text=self._text,
                                       fill=fg, font=font("base", "bold"))

    def _on_configure(self, event):
        if (event.width, event.height) != (self._width, self._height):
            self._width = event.width
            self._height = event.height
            self._draw()

    # -- events ----------------------------------------------------------
    def _on_enter(self, _event):
        if self.enabled:
            self.itemconfigure(self._shape, fill=self.hover_color)

    def _on_leave(self, _event):
        self._pressed = False
        if self.enabled:
            self.itemconfigure(self._shape, fill=self.color)

    def _on_press(self, _event):
        if not self.enabled:
            return
        self.focus_set()
        self._pressed = True
        self.itemconfigure(self._shape, fill=self.hover_color)

    def _on_release(self, _event):
        if not self.enabled:
            return
        pressed = self._pressed
        self._pressed = False
        self.itemconfigure(self._shape, fill=self.hover_color
                           if self._inside() else self.color)
        if pressed and self._inside():
            self._invoke()

    def _inside(self):
        x = self.winfo_pointerx() - self.winfo_rootx()
        y = self.winfo_pointery() - self.winfo_rooty()
        return 0 <= x <= self.winfo_width() and 0 <= y <= self.winfo_height()

    def _on_focus_in(self, _event):
        self._focused = True
        self._draw()

    def _on_focus_out(self, _event):
        self._focused = False
        self._draw()

    def _invoke(self):
        if self.enabled and callable(self.command):
            self.command()

    # -- public API ------------------------------------------------------
    def set_text(self, text):
        """Change the label shown on the button."""
        self._text = text
        if self._label is not None:
            self.itemconfigure(self._label, text=text)

    def set_enabled(self, enabled):
        """Enable or disable the button without destroying it."""
        self.enabled = bool(enabled)
        self.configure(cursor="hand2" if self.enabled else "arrow")
        self._draw()

    def set_style(self, style):
        """Switch to another named button style in place."""
        base, hover, fg = self.STYLES.get(style, self.STYLES["primary"])
        self.color = base
        self.hover_color = hover
        self.text_color = fg
        self._draw()


class PageHero(tk.Canvas):
    """Full-width green banner: gold badge, serif title, subtitle, breadcrumb.

    Every page opens with one so the app has a single, recognisable header.
    ``on_home`` (optional) makes the "Home" crumb clickable.
    """

    def __init__(self, master, title, subtitle="", badge="", crumb="",
                 on_home=None, height=132):
        super().__init__(master, height=height, bg=COLORS["hero_start"],
                         highlightthickness=0, bd=0)
        self._title = title
        self._subtitle = subtitle
        self._badge = badge
        self._crumb = crumb
        self._on_home = on_home
        self._height = height
        self._fonts = {}
        self.tag_bind("crumb_home", "<Button-1>", self._go_home)
        self.tag_bind("crumb_home", "<Enter>",
                      lambda _e: self.configure(cursor="hand2"))
        self.tag_bind("crumb_home", "<Leave>",
                      lambda _e: self.configure(cursor=""))
        self.bind("<Configure>", lambda _event: self._draw())

    def _go_home(self, _event=None):
        if callable(self._on_home):
            self._on_home()

    def _measure(self, text, spec):
        """Width in pixels of ``text`` in the given font tuple."""
        try:
            if spec not in self._fonts:
                self._fonts[spec] = tkfont.Font(self, font=spec)
            return self._fonts[spec].measure(text)
        except tk.TclError:
            return len(text) * 8

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 240)
        height = self._height
        gold = COLORS["gold_accent"]

        draw_gradient(self, 0, 0, width, height, COLORS["hero_start"],
                      COLORS["hero_end"], steps=min(90, max(24, width // 14)))

        # Quiet decorative rings on the right-hand side.
        ring = blend(COLORS["hero_start"], COLORS["hero_end"], 0.80)
        self.create_oval(width - 280, -170, width + 120, 200,
                         outline=ring, width=1)
        self.create_oval(width - 190, -100, width + 210, 260,
                         outline=ring, width=1)

        pad = SPACING["8"]
        y = 20
        if self._badge:
            label = self._badge.upper()
            pill_font = font("xs", "bold")
            pill_w = self._measure(label, pill_font) + 48
            pill_h = 26
            rounded_rect(self, pad, y, pad + pill_w, y + pill_h, pill_h / 2,
                         fill=blend(COLORS["hero_start"], gold, 0.14),
                         outline=blend(COLORS["hero_start"], gold, 0.45))
            draw_icon(self, "leaf", 13, gold, cx=pad + 18, cy=y + pill_h / 2)
            self.create_text(pad + 32, y + pill_h / 2, text=label, anchor="w",
                             fill=gold, font=pill_font)
            y += pill_h + 12

        self.create_text(pad, y, text=self._title, anchor="nw",
                         fill=COLORS["white"],
                         font=display_font("5xl", "bold"))
        sub_y = y + 46
        if self._subtitle:
            self.create_text(pad, sub_y, text=self._subtitle, anchor="nw",
                             fill=blend(COLORS["hero_start"], "#FFFFFF", 0.72),
                             font=font("base"))

        if self._crumb:
            cy = sub_y + 9
            muted = blend(COLORS["hero_start"], "#FFFFFF", 0.66)
            current = self.create_text(width - pad, cy, text=self._crumb,
                                       anchor="e", fill=muted, font=font("base"))
            box = self.bbox(current)
            if box:
                sep = self.create_text(box[0] - 10, cy, text="\u203a",
                                       anchor="e", fill=muted,
                                       font=font("lg"))
                sep_box = self.bbox(sep)
                if sep_box:
                    self.create_text(sep_box[0] - 10, cy, text="Home",
                                     anchor="e", fill=gold,
                                     font=font("base", "bold"),
                                     tags="crumb_home")


def section_title(master, text, bg=COLORS["card"]):
    """A small uppercase green label used to introduce a card or filter."""
    return tk.Label(master, text=text.upper(), bg=bg, fg=COLORS["primary"],
                    font=font("sm", "bold"))


class Card(tk.Frame):
    """A white panel with a hairline border and inner padding."""

    def __init__(self, master, padding=SPACING["5"], **kwargs):
        super().__init__(master, bg=COLORS["card"],
                         highlightbackground=COLORS["border"],
                         highlightthickness=1, bd=0, **kwargs)
        self.body = tk.Frame(self, bg=COLORS["card"])
        self.body.pack(fill="both", expand=True, padx=padding, pady=padding)


class LabeledEntry(tk.Frame):
    """A label stacked above a ttk.Entry, with simple get/set helpers."""

    def __init__(self, master, label, show=None, bg=COLORS["card"],
                 width=28, required=False, hint=None, **kwargs):
        super().__init__(master, bg=bg, **kwargs)
        label_text = label + (" *" if required else "")
        tk.Label(self, text=label_text, bg=bg, fg=COLORS["text"],
                 font=font("sm")).pack(anchor="w", pady=(0, SPACING["1"]))
        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, width=width,
                               show=show or "", font=font("base"))
        self.entry.pack(fill="x", ipady=SPACING["1"])
        if hint:
            tk.Label(self, text=hint, bg=bg, fg=COLORS["text_muted"],
                     font=font("xs")).pack(anchor="w", pady=(2, 0))

    def get(self):
        """Return the current text."""
        return self.var.get()

    def set(self, value):
        """Replace the current text."""
        self.var.set("" if value is None else str(value))

    def clear(self):
        """Empty the entry."""
        self.var.set("")

    def focus(self):
        """Move keyboard focus to the entry."""
        self.entry.focus_set()


class StatusBadge(tk.Frame):
    """A compact pill-shaped status badge (flat colour, no emoji)."""

    PALETTE = {
        "planned": (COLORS["info_soft"], COLORS["info"]),
        "active": (COLORS["pale_mint"], COLORS["primary"]),
        "harvested": (COLORS["gold_soft"], COLORS["gold_dark"]),
        "archived": (COLORS["neutral_soft"], COLORS["text_secondary"]),
        "income": (COLORS["income_soft"], COLORS["income"]),
        "expense": (COLORS["expense_soft"], COLORS["expense"]),
        "over_budget": (COLORS["expense_soft"], COLORS["expense"]),
        "near_limit": (COLORS["warning_soft"], COLORS["gold_dark"]),
        "on_track": (COLORS["pale_mint"], COLORS["primary"]),
    }

    def __init__(self, master, status, label=None, **kwargs):
        bg, fg = self.PALETTE.get(
            str(status).lower(), (COLORS["neutral_soft"], COLORS["text_secondary"]))
        super().__init__(master, bg=bg, **kwargs)
        text = label if label is not None else str(status).replace("_", " ").title()
        tk.Label(self, text=text, bg=bg, fg=fg, font=font("xs", "bold"),
                 padx=SPACING["2"], pady=2).pack()


class ProgressBar(tk.Canvas):
    """A thin rounded progress bar that redraws on resize."""

    def __init__(self, master, value=0.0, color=COLORS["primary"],
                 track=COLORS["border"], height=8, bg=COLORS["card"], **kwargs):
        super().__init__(master, height=height, bg=bg,
                         highlightthickness=0, bd=0, **kwargs)
        self._value = max(0.0, min(100.0, float(value)))
        self._color = color
        self._track = track
        self._height = height
        self.bind("<Configure>", lambda _event: self._draw())

    def set_value(self, value, color=None):
        """Update the filled percentage (clamped to 0-100 for drawing)."""
        self._value = max(0.0, min(100.0, float(value)))
        if color is not None:
            self._color = color
        self._draw()

    def _draw(self):
        self.delete("all")
        w = max(self.winfo_width(), 10)
        h = self._height
        rounded_rect(self, 0, 0, w, h, h / 2, fill=self._track, outline="")
        filled = w * self._value / 100.0
        if filled > 0:
            rounded_rect(self, 0, 0, max(filled, h), h, h / 2,
                         fill=self._color, outline="")


class ScrollFrame(tk.Frame):
    """A vertically scrollable container whose body fills the width.

    The scrollbar hides itself when the content fits, which keeps short pages
    looking clean. Mouse-wheel scrolling is bound only while the pointer is
    inside the area, and is left alone over tables and text widgets.
    """

    def __init__(self, master, bg=COLORS["background"], **kwargs):
        super().__init__(master, bg=bg, **kwargs)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical",
                                       command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self._on_scroll)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.body = tk.Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window((0, 0), window=self.body,
                                                 anchor="nw")
        self._window_height = 0
        self._viewport_h = 0
        self.body.bind("<Configure>", self._on_body_configure)
        self.canvas.bind("<Configure>", self._sync_width)
        # One global wheel handler; it only acts when the pointer is anywhere
        # inside this frame (including over cards and other child widgets).
        self.bind("<Map>", self._bind_wheel, add="+")
        self.bind("<Unmap>", self._unbind_wheel, add="+")
        # The body is stretched to fill the viewport, so Tk stops sending
        # <Configure> when its content grows later (for example after data
        # loads). Watch the requested height so the scroll region follows.
        self._last_req_h = 0
        self._watch_content()

    def _watch_content(self):
        """Re-sync the scroll region whenever the content's height changes."""
        try:
            req = self.body.winfo_reqheight()
            if req != self._last_req_h:
                self._last_req_h = req
                self._sync_height()
                self._sync_region()
            self.after(150, self._watch_content)
        except tk.TclError:
            pass  # frame was destroyed

    def _on_body_configure(self, _event=None):
        self._sync_height()
        self._sync_region()

    def _sync_region(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _sync_width(self, event):
        self._viewport_h = event.height
        self.canvas.itemconfigure(self._window, width=event.width)
        self._sync_height()
        self._sync_region()

    def _sync_height(self):
        """Make short content fill the viewport; keep tall content scrollable."""
        canvas_h = self._viewport_h or self.canvas.winfo_height()
        requested_h = self.body.winfo_reqheight()
        height = max(requested_h, canvas_h) if canvas_h > 1 else requested_h
        if height != self._window_height:
            self._window_height = height
            self.canvas.itemconfigure(self._window, height=height)

    def _on_scroll(self, first, last):
        self.scrollbar.set(first, last)
        if float(first) <= 0.0 and float(last) >= 1.0:
            self.scrollbar.pack_forget()
        elif not self.scrollbar.winfo_ismapped():
            self.scrollbar.pack(side="right", fill="y")

    def _bind_wheel(self, _event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)
        self.canvas.bind_all("<Button-4>", self._on_wheel)
        self.canvas.bind_all("<Button-5>", self._on_wheel)

    def _unbind_wheel(self, _event=None):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _pointer_inside(self, event):
        """True when the pointer is over this frame or any of its children."""
        try:
            widget = self.winfo_containing(event.x_root, event.y_root)
        except (KeyError, tk.TclError):
            return False
        while widget is not None:
            if widget is self:
                return True
            widget = getattr(widget, "master", None)
        return False

    def _on_wheel(self, event):
        if not self._pointer_inside(event):
            return
        if event.widget.winfo_class() in ("Treeview", "Text", "Listbox",
                                          "TCombobox"):
            return
        # Nothing to scroll when the content fits.
        first, last = self.canvas.yview()
        if first <= 0.0 and last >= 1.0:
            return
        if getattr(event, "num", None) == 4:
            step = -1
        elif getattr(event, "num", None) == 5:
            step = 1
        else:
            delta = getattr(event, "delta", 0)
            step = -1 if delta > 0 else 1
        self.canvas.yview_scroll(step * 3, "units")
        return "break"

    def scroll_to_top(self):
        """Reset the scroll position (used when switching pages)."""
        self.canvas.yview_moveto(0.0)


class EmptyState(tk.Frame):
    """A consistent empty state with an optional call to action."""

    def __init__(self, master, title, message="", icon="leaf",
                 action_text=None, action_command=None,
                 bg=COLORS["card"], **kwargs):
        super().__init__(master, bg=bg, **kwargs)
        content = tk.Frame(self, bg=bg)
        content.pack(expand=True, padx=SPACING["8"], pady=SPACING["8"])

        badge = tk.Frame(content, bg=COLORS["pale_mint"], width=64, height=64)
        badge.pack(pady=(0, SPACING["4"]))
        badge.pack_propagate(False)
        Icon(badge, icon, size=30, color=COLORS["primary"],
             bg=COLORS["pale_mint"]).pack(expand=True)

        tk.Label(content, text=title, bg=bg, fg=COLORS["text"],
                 font=font("2xl", "bold")).pack(pady=(0, SPACING["1"]))
        if message:
            tk.Label(content, text=message, bg=bg, fg=COLORS["text_secondary"],
                     font=font("base"), wraplength=380,
                     justify="center").pack(pady=(0, SPACING["4"]))
        if action_text and callable(action_command):
            RoundedButton(content, action_text, command=action_command,
                          width=200, height=40, parent_bg=bg).pack()
