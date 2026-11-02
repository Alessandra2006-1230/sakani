"""Canvas chart helpers: a grouped bar chart and a donut chart.

No external chart library is used. Everything is drawn on a Tkinter Canvas so
the app keeps its dependency footprint small.
"""

from config import COLORS, CURRENCY
from ui import theme

PIE_COLORS = [
    "#2C6247", "#E2B93B", "#4C8A63", "#3F6FA8", "#8DBF9F",
    "#EDD27E", "#7FA3CB", "#163F2A", "#B7D3C0", "#B9B7A5",
]


def _canvas_size(canvas, fallback_width=400, fallback_height=220):
    """Return a usable canvas size, even before it is mapped on screen."""
    width = canvas.winfo_width()
    height = canvas.winfo_height()
    if width <= 1:
        width = int(canvas["width"]) if canvas["width"] else fallback_width
    if height <= 1:
        height = int(canvas["height"]) if canvas["height"] else fallback_height
    return max(int(width), 200), max(int(height), 120)


def _short_money(value):
    """Format an axis label in a compact way."""
    value = float(value)
    if value >= 1_000_000:
        return "%.1fM" % (value / 1_000_000)
    if value >= 1_000:
        return "%.0fk" % (value / 1_000)
    return "%.0f" % value


def _nice_max(value):
    """Round an axis maximum up to a friendly number."""
    if value <= 0:
        return 1.0
    magnitude = 10 ** (len(str(int(value))) - 1)
    for step in (1, 2, 2.5, 5, 10):
        candidate = step * magnitude
        if candidate >= value:
            return candidate
    return magnitude * 10


def _empty(canvas, width, height, message):
    theme.draw_icon(canvas, "summary", 30, COLORS["border"], cx=width / 2,
                    cy=height / 2 - 16)
    canvas.create_text(width / 2, height / 2 + 20, text=message,
                       fill=COLORS["text_secondary"], font=theme.font("sm"))


def draw_bar_chart(canvas, labels, series):
    """Draw grouped vertical bars.

    labels: list of x-axis labels.
    series: list of {"label": str, "values": list, "color": hex}.
    """
    canvas.delete("all")
    width, height = _canvas_size(canvas)
    if not labels or not series:
        _empty(canvas, width, height, "No chart data for this period")
        return

    highest = 0.0
    for item in series:
        for value in item["values"]:
            highest = max(highest, float(value))
    if highest <= 0:
        _empty(canvas, width, height, "No income or expenses recorded yet")
        return

    highest = _nice_max(highest)
    left, right, top, bottom = 64, 16, 38, 32
    plot_w = max(width - left - right, 40)
    plot_h = max(height - top - bottom, 40)

    # Horizontal grid + y labels
    for step in range(5):
        y = top + plot_h * step / 4
        value = highest * (4 - step) / 4
        if step:
            canvas.create_line(left, y, left + plot_w, y,
                               fill=COLORS["border"], dash=(2, 4))
        else:
            canvas.create_line(left, y, left + plot_w, y,
                               fill=COLORS["border"])
        canvas.create_text(left - 10, y, text=_short_money(value), anchor="e",
                           fill=COLORS["text_muted"], font=theme.font("xs"))

    group_w = plot_w / len(labels)
    bar_w = max(6.0, min(26.0, group_w / (len(series) + 1.2)))
    gap = 3
    total_w = bar_w * len(series) + gap * (len(series) - 1)

    for index, label in enumerate(labels):
        center = left + group_w * (index + 0.5)
        start_x = center - total_w / 2
        for s_index, item in enumerate(series):
            value = float(item["values"][index]) if index < len(item["values"]) else 0.0
            bar_h = (value / highest) * plot_h
            x1 = start_x + s_index * (bar_w + gap)
            x2 = x1 + bar_w
            y1 = top + plot_h - bar_h
            if bar_h > 0:
                theme.rounded_rect(canvas, x1, y1, x2, top + plot_h, radius=3,
                                   fill=item.get("color", COLORS["primary"]),
                                   outline="")
                if bar_w >= 14:
                    canvas.create_text((x1 + x2) / 2, y1 - 9,
                                       text=_short_money(value),
                                       fill=COLORS["text_secondary"],
                                       font=theme.font("xs"))
        canvas.create_text(center, top + plot_h + 14, text=label,
                           fill=COLORS["text_secondary"], font=theme.font("xs"))

    # Legend pills
    legend_x = left
    for item in series:
        theme.rounded_rect(canvas, legend_x, 8, legend_x + 10, 18, radius=3,
                           fill=item.get("color", COLORS["primary"]), outline="")
        canvas.create_text(legend_x + 16, 13, text=item["label"], anchor="w",
                           fill=COLORS["text"], font=theme.font("sm"))
        legend_x += 26 + len(item["label"]) * 7


def draw_line_chart(canvas, labels, series):
    """Draw a clean line chart for income vs expenses."""
    canvas.delete("all")
    width, height = _canvas_size(canvas)
    if not labels or not series:
        _empty(canvas, width, height, "No chart data for this period")
        return

    highest = 0.0
    for item in series:
        for value in item.get("values", []):
            highest = max(highest, float(value))
    if highest <= 0:
        _empty(canvas, width, height, "No income or expenses recorded yet")
        return

    highest = _nice_max(highest)
    left, right, top, bottom = 64, 18, 42, 38
    plot_w = max(width - left - right, 40)
    plot_h = max(height - top - bottom, 40)

    # Grid
    for step in range(5):
        y = top + plot_h * step / 4
        value = highest * (4 - step) / 4
        if step:
            canvas.create_line(left, y, left + plot_w, y,
                               fill=COLORS["border"], dash=(2, 4))
        else:
            canvas.create_line(left, y, left + plot_w, y,
                               fill=COLORS["border"])
        canvas.create_text(left - 10, y, text=_short_money(value), anchor="e",
                           fill=COLORS["text_muted"], font=theme.font("xs"))

    n = len(labels)
    if n == 0:
        return
    step_x = plot_w / max(n - 1, 1)

    # Draw lines and points
    for item in series:
        color = item.get("color", COLORS["primary"])
        values = item.get("values", [])
        coords = []
        for i, label in enumerate(labels):
            val = float(values[i]) if i < len(values) else 0.0
            x = left + i * step_x
            y = top + plot_h - (val / highest) * plot_h
            coords.append((x, y))
        # Draw connecting segments
        if len(coords) >= 2:
            for j in range(len(coords) - 1):
                x1c, y1c = coords[j]
                x2c, y2c = coords[j + 1]
                canvas.create_line(x1c, y1c, x2c, y2c, fill=color, width=2.5,
                                   capstyle="round", joinstyle="round")
        # Draw markers on top
        for x, y in coords:
            canvas.create_oval(x - 4, y - 4, x + 4, y + 4,
                               fill=color, outline=COLORS["card"], width=2)

    # X labels (avoid crowding)
    max_labels = 8
    skip = max(1, n // max_labels)
    for i, label in enumerate(labels):
        if i % skip != 0 and i != n - 1:
            continue
        x = left + i * step_x
        canvas.create_text(x, top + plot_h + 16, text=label, anchor="n",
                           fill=COLORS["text_secondary"], font=theme.font("xs"))

    # Legend
    legend_x = left
    for item in series:
        color = item.get("color", COLORS["primary"])
        canvas.create_oval(legend_x, 12, legend_x + 8, 20, fill=color,
                           outline=COLORS["card"], width=1)
        canvas.create_text(legend_x + 14, 16, text=item["label"], anchor="w",
                           fill=COLORS["text"], font=theme.font("sm"))
        legend_x += 90 + len(item["label"]) * 4


def draw_pie_chart(canvas, data, center_label="Total"):
    """Draw a donut chart with a legend.

    data: list of {"label": str, "value": number}.
    """
    canvas.delete("all")
    width, height = _canvas_size(canvas)
    clean = [
        {"label": item["label"], "value": float(item["value"])}
        for item in data if float(item["value"]) > 0
    ]
    total = sum(item["value"] for item in clean)
    if not clean or total <= 0:
        _empty(canvas, width, height, "No category data yet")
        return

    clean.sort(key=lambda item: item["value"], reverse=True)
    legend_w = min(max(width * 0.48, 120), 240)
    diameter = min(height - 28, width - legend_w - 36)
    diameter = max(diameter, 64)
    x1 = 20
    y1 = (height - diameter) / 2
    x2 = x1 + diameter
    y2 = y1 + diameter

    start = 90.0
    for index, item in enumerate(clean):
        extent = -360.0 * item["value"] / total
        canvas.create_arc(x1, y1, x2, y2, start=start, extent=extent,
                          fill=PIE_COLORS[index % len(PIE_COLORS)],
                          outline=COLORS["card"], width=2)
        start += extent

    # Donut hole with total
    inner = diameter * 0.56
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    canvas.create_oval(cx - inner / 2, cy - inner / 2, cx + inner / 2,
                       cy + inner / 2, fill=COLORS["card"], outline="")
    canvas.create_text(cx, cy - 8, text=center_label,
                       fill=COLORS["text_muted"], font=theme.font("xs"))
    canvas.create_text(cx, cy + 9, text=_short_money(total),
                       fill=COLORS["text"], font=theme.font("lg", "bold"))

    legend_x = x2 + 18
    row_h = 21
    available = max(1, int((height - 8) / row_h))
    shown = clean if len(clean) <= available else clean[:max(1, available - 1)]
    extra = len(clean) - len(shown)
    legend_y = (height - len(shown) * row_h) / 2 + 4
    for index, item in enumerate(shown):
        theme.rounded_rect(canvas, legend_x, legend_y - 5, legend_x + 9,
                           legend_y + 4, radius=2,
                           fill=PIE_COLORS[index % len(PIE_COLORS)], outline="")
        label = item["label"]
        max_chars = max(6, int((width - legend_x - 60) / 7))
        if len(label) > max_chars:
            label = label[:max_chars - 1] + "…"
        percent = item["value"] / total * 100
        canvas.create_text(legend_x + 15, legend_y, text=label, anchor="w",
                           fill=COLORS["text"], font=theme.font("xs"))
        canvas.create_text(legend_x + 15, legend_y + 10,
                           text="%.0f%%" % percent,
                           anchor="w", fill=COLORS["text_muted"],
                           font=theme.font("xs"))
        legend_y += row_h
    if extra:
        canvas.create_text(legend_x + 15, legend_y, text="+%d more" % extra,
                           anchor="w", fill=COLORS["text_muted"],
                           font=theme.font("xs"))
