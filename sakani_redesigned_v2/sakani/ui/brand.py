"""Shared decorative branding panel used by the login and sign-up screens."""

from config import APP_NAME, COLORS, TAGLINE_AUTH, TAGLINE_MAIN
from ui import theme


def draw_brand_panel(canvas, width, height):
    """Draw the deep-green authentication side panel on a resized canvas.

    Everything is composed from flat shapes and vector icons; no emoji fonts
    or image assets are required.
    """
    canvas.delete("all")
    width = max(int(width), 10)
    height = max(int(height), 10)

    # Deep-green wash that lightens towards the bottom, like the page banners.
    theme.draw_gradient(canvas, 0, 0, width, height, COLORS["hero_start"],
                        theme.blend(COLORS["hero_start"], COLORS["hero_end"], 0.55),
                        vertical=True, steps=min(80, max(20, height // 10)))

    line = COLORS["forest_line"]

    # Soft concentric rings, clipped by the panel edges.
    canvas.create_oval(-width * 0.60, -height * 0.38, width * 0.60,
                       height * 0.48, outline=line, width=1)
    canvas.create_oval(-width * 0.40, -height * 0.18, width * 0.80,
                       height * 0.68, outline=COLORS["forest_raised"], width=1)
    canvas.create_oval(width * 0.10, height * 0.58, width * 1.40,
                       height * 1.90, outline=line, width=1)
    canvas.create_oval(width * 0.30, height * 0.78, width * 1.20,
                       height * 1.60, outline=COLORS["forest_raised"], width=1)

    if height < 380:
        return

    center_y = height * 0.32

    # Logo motif: a gold-ringed disc with a leaf.
    size = 84
    canvas.create_oval(width / 2 - size / 2 - 10, center_y - size / 2 - 10,
                       width / 2 + size / 2 + 10, center_y + size / 2 + 10,
                       fill=COLORS["forest_raised"], outline=COLORS["gold_accent"],
                       width=1)
    theme.draw_icon(canvas, "leaf", 50, COLORS["gold_accent"],
                    cx=width / 2, cy=center_y)

    canvas.create_text(width / 2, center_y + 82, text=APP_NAME,
                       fill=COLORS["white"], font=theme.display_font("6xl", "bold"))
    canvas.create_text(width / 2, center_y + 112, text=TAGLINE_AUTH,
                       fill=COLORS["on_forest"],
                       font=theme.display_font("lg", "italic"))

    canvas.create_line(width / 2 - 28, center_y + 138,
                       width / 2 + 28, center_y + 138,
                       fill=COLORS["gold_accent"], width=1)

    bullets = [
        "Track income and farm expenses",
        "Compare budgets with real spending",
        "See profit for every crop cycle",
    ]
    for index, text in enumerate(bullets):
        y = center_y + 172 + index * 32
        canvas.create_oval(width / 2 - 108, y - 3, width / 2 - 102, y + 3,
                           fill=COLORS["gold_accent"], outline="")
        canvas.create_text(width / 2 - 92, y, text=text, anchor="w",
                           fill=COLORS["on_forest"], font=theme.font("sm"))

    canvas.create_text(width / 2, height - 34, text=TAGLINE_MAIN.upper(),
                       fill=COLORS["on_forest_muted"], font=theme.font("xs"))
