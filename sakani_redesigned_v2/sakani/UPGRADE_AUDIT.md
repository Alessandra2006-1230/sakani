# Sakani — Upgrade Audit

Date: 2026-10-29
Source: initial audit of the supplied `sakani` archive + live local database inspection.

## 1. Architecture snapshot

- Entry: `main.py` → `database.connection.init_database()` → `ui.app.SakaniApp` (Tkinter).
- Layers: `ui/` (pages, theme, sidebar, charts), `database/` (connection, queries, schema), `models/` (auth/validation), `utils/` (CSV export).
- GUI toolkit: Tkinter / ttk / Canvas (no matplotlib/pandas). Charts drawn on Canvas.
- Persistence: MySQL via `mysql-connector-python` (`sakani_db`, user `sakani_user`, port 3306).
- Money: currently handled as Python `float` end-to-end after DB decimal round-trip.
- No tests, no migrations framework, no CI.

## 2. Confirmed existing features (working at audit time)

1. Signup / login / logout.
2. PBKDF2-HMAC-SHA256 password hashing with random salt (`models/auth.py`).
3. Add income / expense transaction (category, amount, date, description).
4. Dashboard: income / expense / net / count cards, income-vs-expense bar chart, recent transactions.
5. History: search, type filter, date filters, edit, delete, CSV export, per-user scoping.
6. Summary: yearly totals, 12-month table, expense/income-by-category pie charts.
7. CSV export (`utils/export.py`, utf-8-sig).
8. Tkinter Canvas charts with empty states.

## 3. Audit findings and risks (prioritized)

### P0 — confirmed issues

1. **Hard-coded DB credentials in source** — `config.py` contains `password: "SakaniLocal2026!"` (now committed in initial checkpoint). Must move to env/local config. README also wrongly says port `3307`; live server is on `3306` (config default is already `3306`).
2. **No test suite** — none visible in archive; business logic and query behavior are untested.
3. **Floating-point money** — `queries.get_totals`, `get_monthly_summary`, `get_category_breakdown` convert DB `DECIMAL(12,2)` to `float`. Financial math should use `Decimal`.
4. **SQL injection-adjacent pattern** — `get_recent_transactions` builds `LIMIT " + str(limit)` via string concat (works today, but should be parameterized).
5. **No finite-amount validation** — `float("nan")` / `float("inf")` pass the current `amount <= 0` check; amounts above DECIMAL(12,2) range would cause DB errors.
6. **Error surfacing** — DB error messages are shown raw in UI (`str(exc)`), including possible server detail leakage.
7. **No backup/restore documentation** despite destructive-adjacent operations (delete, user cascade).

### P1 — gaps vs. upgrade plan

1. No production-cycle / crop entity or `production_cycle_id` on transactions.
2. No dashboard date-range filter (this month / last month / this year / custom).
3. No category breakdown totals/labels for net profit wording inconsistency (`Net Profit / Loss` vs net income).
4. No monthly comparison beyond the single-year bar chart; no CSV export of filtered/summary data.
5. Sidebar icons are emoji; plan prefers restrained built-in symbol set or simple Canvas icons.

### P2 — observations

1. `categories` table is global (not per-user) — acceptable for default seed categories; revisit when user-defined categories are added.
2. Edit dialog allows switching type, which silently changes category compatibility — validation should guard.
3. `main.py` error box mentions editing password in `config.py` — will need updating after credential move.
4. No `.gitignore` existed; `__pycache__/` dirs were committed in the archive snapshot.

## 4. Baseline behavior record

- DB state at audit: 2 users, 2 test transactions (both amount `123.00`, user 2), 13 seeded categories, all on `sakani_db`.
- Existing users/transactions were NOT touched during audit.

## 5. Baseline checklist (manual smoke-test checklist before changes)

- [ ] Register new account.
- [ ] Log in / log out.
- [ ] Add income + expense transaction.
- [ ] Dashboard totals, chart, recent list update.
- [ ] History search / filters / edit / delete / export.
- [ ] Summary yearly totals, charts, monthly table.
- [ ] Empty states render.
- [ ] Window resize to minimum (900x600).

## 6. Baseline backup

- No Git repository was present in the supplied archive. A new Git repo was initialized in the working directory and an initial commit (`fa780aa`) was created **before any source edits**.
- Live MySQL data was only read, never modified.

## 7. Recommended first changes (Phase 1)

1. Move DB credentials out of source (`config.py`) → env vars / ignored local config + `.env.example`.
2. Parameterize the `LIMIT` clause; keep user scoping everywhere.
3. Switch financial aggregates to `Decimal`.
4. Add finite/positive-amount and date validation.
5. Add focused unit tests for auth helpers and validators (stdlib `unittest`, no new deps).
