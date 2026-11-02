"""Sakani configuration: database settings, design tokens and constants.

Database credentials are read from environment variables so they are never
committed to source control. See `.env.example` for the expected variables.

    SAKANI_DB_HOST     MySQL host           (default: 127.0.0.1)
    SAKANI_DB_PORT     MySQL port           (default: 3306)
    SAKANI_DB_USER     MySQL user           (default: sakani_user)
    SAKANI_DB_PASSWORD MySQL password       (required)
    SAKANI_DB_NAME     Sakani database name (default: sakani_db)

A local `.env` file is loaded automatically if present. Shell environment
variables take priority over `.env` values.
"""

import os
from pathlib import Path


def _load_env_file():
    """Load key=value pairs from .env file into os.environ if not already set.

    Shell environment variables take priority; .env values are only used
    as fallbacks when the variable is not already set in the environment.
    """
    env_path = Path(__file__).parent / ".env"
    if not env_path.is_file():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        # Only set if not already in environment (shell wins)
        if key and key not in os.environ:
            os.environ[key] = value


# Load .env before reading configuration
_load_env_file()

DB_CONFIG = {
    "host": os.environ.get("SAKANI_DB_HOST", "127.0.0.1"),
    "port": int(os.environ.get("SAKANI_DB_PORT", "3306")),
    "user": os.environ.get("SAKANI_DB_USER", "sakani_user"),
    "password": os.environ.get("SAKANI_DB_PASSWORD", ""),
    "database": os.environ.get("SAKANI_DB_NAME", "sakani_db"),
}

APP_NAME = "Sakani"
TAGLINE_MAIN = "Track · Save · Grow"
TAGLINE_AUTH = "Track Today, Grow Tomorrow."
CURRENCY = "\u20b1"

# ---------------------------------------------------------------------------
# Colour system
# Inspired by a calm marketplace look: a deep green gradient hero, warm cream
# pages, soft sage highlights and a single gold accent. Semantic colours are
# muted so numbers and charts stay easy on the eyes.
# `background`/`card`/`text_light` are kept for backwards compatibility with
# page code written before the design-system refactor.
# ---------------------------------------------------------------------------
COLORS = {
    # Greens
    "deep_forest": "#163F2A",
    "hero_start": "#1A4B33",
    "hero_end": "#437449",
    "primary": "#2C6247",
    "primary_dark": "#204C37",
    "primary_light": "#4C8A63",
    "pale_mint": "#E8EFEA",
    "soft_green": "#E8EFEA",

    # Surfaces
    "warm_cream": "#F8F7F3",
    "background": "#F8F7F3",
    "surface": "#FFFFFF",
    "surface_alt": "#FAF9F5",
    "card": "#FFFFFF",
    "white": "#FFFFFF",
    "input_bg": "#F5F3EC",
    "input_border": "#E5E2D6",

    # Text
    "text": "#1D2B24",
    "text_secondary": "#6F7A73",
    "text_light": "#6F7A73",
    "text_muted": "#9AA19C",

    # Semantic
    "income": "#2C6247",
    "expense": "#C4504B",
    "danger": "#C4504B",
    "danger_dark": "#A53F3B",
    "warning": "#C98E2B",
    "info": "#3F6FA8",
    "gold_accent": "#E2B93B",
    "gold_dark": "#B8932A",
    "accent": "#E2B93B",
    "muted": "#9AA19C",

    # Lines and glass-inspired surfaces
    "border": "#ECEAE1",
    "border_focus": "#2C6247",
    "glass_surface": "#FFFFFF",
    "glass_border": "#F0EEE6",

    # Tints used for card accents (kept flat; no real transparency in Tk)
    "income_soft": "#E8EFEA",
    "expense_soft": "#F8EBE8",
    "warning_soft": "#FAF1D6",
    "info_soft": "#E9EFF6",
    "gold_soft": "#FAF1D6",
    "neutral_soft": "#F0EFE6",

    # Dark sidebar / brand-panel layers (on top of `deep_forest`)
    "forest_raised": "#1E4E37",
    "forest_hover": "#1A4631",
    "forest_line": "#2F5E47",
    "on_forest": "#DCE9E0",
    "on_forest_muted": "#93AF9F",
}

# Typography. The first installed family in each list is used, so the app
# looks right on Windows, macOS and Linux. For the exact look, install (or
# drop into assets/fonts/) the free Google fonts "Playfair Display" and
# "DM Sans"; otherwise Georgia and Segoe UI are used.
FONT_BODY_CANDIDATES = [
    "DM Sans", "Segoe UI Variable Text", "Segoe UI", "SF Pro Text",
    "Helvetica Neue", "Inter", "DejaVu Sans",
]
FONT_DISPLAY_CANDIDATES = [
    "Playfair Display", "Georgia", "Cambria", "Palatino Linotype", "Lora",
    "DejaVu Serif",
]
# Kept for older imports.
FONT_FAMILY = "Segoe UI"
FONT_FALLBACK = "DejaVu Sans"

FONT_SIZES = {
    "xs": 8,
    "sm": 9,
    "base": 10,
    "lg": 11,
    "xl": 12,
    "2xl": 14,
    "3xl": 16,
    "4xl": 20,
    "5xl": 24,
    "6xl": 28,
}

# Spacing scale (pixels)
SPACING = {
    "0": 0,
    "1": 4,
    "2": 8,
    "3": 12,
    "4": 16,
    "5": 20,
    "6": 24,
    "8": 32,
    "10": 40,
    "12": 48,
}

RADIUS = {"sm": 6, "md": 10, "lg": 14, "xl": 20, "full": 9999}

WINDOW_SIZE = "1200x760"
WINDOW_MIN = (900, 620)

# Asset paths. Drop a real logo at assets/images/sakani_logo.png to replace
# the drawn placeholder in the sidebar.
ASSETS_DIR = Path(__file__).parent / "assets"
LOGO_PATH = ASSETS_DIR / "images" / "sakani_logo.png"
