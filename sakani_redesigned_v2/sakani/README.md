# Sakani — Farm Expense and Income Tracker

**Tagline:** *Track · Save · Grow*  
**Auth tagline:** *Track Today, Grow Tomorrow.*

Sakani is a desktop farm expense and income tracker built with Python (Tkinter/ttk) and a local MySQL database. Everything runs fully offline.

## Features

- **Authentication** — Sign Up / Log In with PBKDF2-HMAC-SHA256 hashed passwords (random salt)
- **Add Transaction** — Record income or expenses with category, amount, date, and description
- **Dashboard** — At-a-glance totals, income vs expense bar chart, recent transactions, and budget/cycle insights
- **History Transactions** — Search, filter by type/date, edit, delete, and export to CSV
- **Financial Summary** — Yearly totals, monthly breakdown table, expense/income category pie charts, custom date-range export
- **Crop Production Cycles** — Track crops across production cycles with status (planned/active/harvested/archived), link transactions, and view per-cycle financial totals
- **Break-even Analysis** — Calculate break-even quantity, revenue, and estimated net results for production cycles
- **Budget Management** — Create budgets by category and period, compare actual vs budgeted spending with visual progress indicators
- **Local only** — No internet, APIs, cloud services, or external dependencies beyond `mysql-connector-python`

## Tech Stack

| Layer | Choice |
|-------|--------|
| Language | Python 3.10+ |
| GUI | Tkinter + ttk (custom styling, Canvas charts) |
| Database | MySQL Server (local) — database name `sakani_db` |
| Connector | `mysql-connector-python` |
| Security | `hashlib.pbkdf2_hmac` + `os.urandom` salts |
| Charts | Tkinter `Canvas` only (no matplotlib/pandas) |
| Math | `decimal.Decimal` for all financial calculations |

## Project Structure

```
sakani/
├── main.py                  # Entry point
├── config.py                # DB settings (from env), colours, fonts, constants
├── requirements.txt         # Dependencies
├── .env.example             # Template for local DB credentials
├── README.md
├── MANUAL_QA.md             # Manual QA checklist
├── database/                # Schema, connection, queries
├── models/                  # Auth helpers, validators, domain values
├── ui/                      # Tkinter pages, theme, sidebar, app
├── utils/                   # CSV export
├── tests/                   # Unit tests (stdlib unittest)
└── design/                  # Optional HTML/CSS/JS mockups
```

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure MySQL**
   - Copy the template and fill in real values:
     ```bash
     cp .env.example .env
     ```
     Then edit `.env` and set `SAKANI_DB_PASSWORD` (and optionally other `SAKANI_DB_*` variables).
     The application automatically loads `.env` on startup; shell environment variables take priority over `.env` values.
   - Make sure MySQL Server is running locally on port `3306` (or set `SAKANI_DB_PORT`).
   - Confirm the `SAKANI_DB_USER` and `SAKANI_DB_PASSWORD` values match your local MySQL account.

3. **Run the app**
   ```bash
   python main.py
   ```
   On first run, `sakani_db` and all tables are created automatically, and default income/expense categories are seeded.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Backup and restore guidance

- Back up the MySQL data directory or run:
  ```bash
  mysqldump -u <user> -p sakani_db > sakani_backup_YYYYMMDD.sql
  ```
- To restore, create the database and re-import the dump. Never run destructive reset scripts against the live database.

## Usage Notes

- **Currency:** `₱` (Philippine Peso)
- **Passwords:** Never stored in plain text. Passwords must be at least 8 characters.
- **Validation:** All forms validate inputs; errors are shown inline or via message boxes.
- **Exports:** CSV exports are saved locally (fully offline) with UTF-8-SIG encoding.
- **Charts:** Drawn on Tkinter `Canvas`. Empty states show "No data yet".
- **Theming:** Green nature theme throughout the app.
- **Break-even Assumptions:** Break-even is calculated using recorded cycle expenses as fixed costs. Income, taxes, depreciation, and unrecorded costs are excluded. Results are estimates, not professional financial advice.

## Troubleshooting

- **"Database password is not configured"** — Set the `SAKANI_DB_PASSWORD` environment variable.
- **"Access denied for user ..."** — Check the `SAKANI_DB_USER` and `SAKANI_DB_PASSWORD` values.
- **"Can't connect to MySQL server"** — Ensure MySQL is running and the host/port are correct.
- **Module errors** — Run from the `sakani/` directory or ensure it's on `PYTHONPATH`.

## Design & Assets

- **Logo asset:** Place a real logo at `assets/images/sakani_logo.png` (recommended ~112×112 px or square ≥44 px). If missing, the sidebar shows a drawn vector leaf placeholder. Keep image references alive (no fake placeholder files are committed).
- **Fonts:** Titles use Playfair Display and body text uses DM Sans when available (see `assets/fonts/README.md`); otherwise Georgia and Segoe UI are used.
- **Design system:** The UI uses a glass-inspired flat design with forest greens (`#164E3B`, `#237A57`, `#39A875`), warm neutrals, and semantic accents. No real backdrop blur/transparency is used in Tkinter.
- **Verification notes:** UI changes were smoke-tested headlessly (Xvfb) across 1440/1100/900 widths for all pages and key dialogs. Tests run with `python3 -m unittest discover -s tests -v` (47 passed, 1 skipped). Budget integration tests require `SAKANI_DB_PASSWORD`. Visual clicks/interaction flows were programmatically exercised where possible; some environments may need a display server for live interaction testing.

## Design Mockups

The `design/` folder contains optional static HTML/CSS/JS mockups for visual reference only. They are not used by the Tkinter application.
