# Sakani — Manual QA Checklist

Version: Post Phase 5 (Budgeting & Break-even)  
Date: 2026-10-29

This checklist verifies core functionality after the upgrade. Run each step and mark ✅ or ❌.

---

## Prerequisites

- MySQL Server running on port 3306 (or set `SAKANI_DB_PORT`)
- Environment variables set (or `.env` file):
  - `SAKANI_DB_HOST=127.0.0.1`
  - `SAKANI_DB_PORT=3306`
  - `SAKANI_DB_USER=sakani_user`
  - `SAKANI_DB_PASSWORD=<your mysql password>`
  - `SAKANI_DB_NAME=sakani_db`
- Dependencies installed: `pip install -r requirements.txt`

Run the app:
```bash
python main.py
```

---

## 1. Authentication

| Step | Expected |
|------|----------|
| 1.1 Launch app → login screen shows | ✅ |
| 1.2 Click "Sign Up" → sign-up screen shows | ✅ |
| 1.3 Register with valid name, email, password (≥8 chars), confirm | ✅ Account created, redirects to login |
| 1.4 Register with same email again | ❌ "This email is already registered" |
| 1.5 Register with password < 8 chars | ❌ "Password must be at least 8 characters" |
| 1.6 Register with mismatched passwords | ❌ "Passwords do not match" |
| 1.7 Register with invalid email format | ❌ "Please enter a valid email address" |
| 1.8 Log in with correct credentials | ✅ Dashboard loads, sidebar shows user name |
| 1.9 Log in with wrong password | ❌ "Incorrect email or password" |
| 1.10 Log in with non-existent email | ❌ "Incorrect email or password" |
| 1.11 Click "Log Out" in sidebar → confirm | ✅ Returns to login screen |
| 1.12 After logout, try to access app via browser back (not applicable for desktop) — just verify session cleared | ✅ |

---

## 2. Transaction CRUD (History / Add pages)

### 2.1 Add Transaction
| Step | Expected |
|------|----------|
| 2.1.1 Navigate to "Add Transaction" | ✅ Form loads with Income/Expense radios |
| 2.1.2 Select Income → category dropdown shows income categories | ✅ |
| 2.1.3 Select Expense → category dropdown shows expense categories | ✅ |
| 2.1.4 Enter valid amount (e.g., `123.45`), today's date, description | ✅ |
| 2.1.5 Click "Save Transaction" | ✅ Success toast, form clears, date resets to today |
| 2.1.6 Enter amount `0` or negative | ❌ "Amount must be greater than zero" |
| 2.1.7 Enter non-numeric amount | ❌ "Please enter a valid amount" |
| 2.1.8 Enter invalid date format | ❌ "Please use a valid date in YYYY-MM-DD format" |
| 2.1.9 Enter description > 255 chars | ❌ "Description is too long" |
| 2.1.10 Submit with no category selected | ❌ "Please choose a category" |

### 2.2 History — View, Search, Filter
| Step | Expected |
|------|----------|
| 2.2.1 Navigate to "History Transactions" | ✅ Table shows all user's transactions |
| 2.2.2 Type filter: Income only | ✅ Only income rows shown |
| 2.2.3 Type filter: Expense only | ✅ Only expense rows shown |
| 2.2.4 Type filter: All | ✅ All rows shown |
| 2.2.5 Search by category name (partial) | ✅ Matching rows shown |
| 2.2.6 Search by description (partial) | ✅ Matching rows shown |
| 2.2.7 Date From: valid YYYY-MM-DD | ✅ Filters correctly |
| 2.2.8 Date To: valid YYYY-MM-DD | ✅ Filters correctly |
| 2.2.9 Invalid date format in filter | ❌ Warning "Please enter dates in YYYY-MM-DD format" |
| 2.2.10 Click "Reset" | ✅ All filters cleared, full list shown |
| 2.2.11 Empty result set | ✅ "No transactions found" label shown |

### 2.3 Edit Transaction
| Step | Expected |
|------|----------|
| 2.3.1 Select a row → "Edit Selected" | ✅ Modal opens with current values |
| 2.3.2 Change amount, date, category, description | ✅ |
| 2.3.3 Change type (Income ↔ Expense) → category dropdown updates | ✅ |
| 2.3.4 Click "Save Changes" | ✅ Success toast, table refreshes |
| 2.3.5 Edit with invalid amount/date | ❌ Inline error, dialog stays open |
| 2.3.6 Double-click row → opens edit dialog | ✅ |

### 2.4 Delete Transaction
| Step | Expected |
|------|----------|
| 2.4.1 Select a row → "Delete" | ✅ Confirmation dialog shows details |
| 2.4.2 Confirm delete | ✅ Row removed, table refreshes |
| 2.4.3 Cancel delete | ✅ Row remains |

### 2.5 Transaction–Cycle Linking
| Step | Expected |
|------|----------|
| 2.5.1 Create a production cycle (see §3) | ✅ |
| 2.5.2 Edit a transaction → "Production cycle" dropdown shows cycle | ✅ |
| 2.5.3 Select cycle → save | ✅ Transaction linked |
| 2.5.4 Verify cycle page shows transaction in totals | ✅ |
| 2.5.5 Edit transaction → set cycle to blank → save | ✅ Transaction unlinked |
| 2.5.6 Verify cycle totals update | ✅ |

---

## 3. Production Cycles

| Step | Expected |
|------|----------|
| 3.1 Navigate to "Crop Cycles" | ✅ List shows user's cycles (empty if none) |
| 3.2 Click "Add Cycle" | ✅ Modal opens |
| 3.3 Enter crop name (required), variety, plot, start date, expected harvest, status, notes | ✅ |
| 3.4 Submit with missing crop name | ❌ "Please enter a crop name" |
| 3.5 Submit with invalid start date | ❌ "Please use a valid date in YYYY-MM-DD format" |
| 3.6 Submit valid cycle | ✅ Cycle appears in list with "planned" status |
| 3.7 Edit cycle → change status: planned → active | ✅ |
| 3.8 Edit cycle → change status: active → harvested | ✅ |
| 3.9 Edit cycle → change status: harvested → archived | ✅ |
| 3.10 Edit cycle → try planned → harvested (skip active) | ❌ "Status cannot move from planned to harvested" |
| 3.11 Edit cycle → try archived → active | ❌ "Status cannot move from archived to active" |
| 3.12 Delete cycle → confirm | ✅ Cycle removed, linked transactions unassigned |
| 3.13 Cycle totals: income / expense / net / count shown | ✅ Match linked transactions |

---

## 4. Dashboard Period Filters

| Step | Expected |
|------|----------|
| 4.1 Dashboard loads → period selector defaults to "All time" | ✅ |
| 4.2 Select "This month" → cards, chart, recent list update | ✅ Period label shows "YYYY-MM-DD to YYYY-MM-DD" |
| 4.3 Select "Last month" → updates correctly | ✅ |
| 4.4 Select "This year" → updates correctly | ✅ |
| 4.5 Select "Custom" → start/end date fields appear | ✅ |
| 4.6 Enter valid custom range → updates correctly | ✅ |
| 4.7 Enter invalid custom date → shows "All time" data (graceful) | ✅ |
| 4.8 Switch between periods rapidly → no duplicate rows/charts | ✅ |
| 4.9 Net income card: green when positive, red when negative | ✅ |

---

## 5. Financial Summary

| Step | Expected |
|------|----------|
| 5.1 Navigate to "Financial Summary" | ✅ Year selector defaults to current year |
| 5.2 Year selector shows available years + current year | ✅ |
| 5.3 Change year → cards, charts, monthly table update | ✅ |
| 5.4 Monthly table: 12 rows, correct income/expense/net | ✅ Net green/red |
| 5.5 Pie charts: Expenses by Category, Income by Category | ✅ Render or "No data yet" |
| 5.6 Totals match dashboard "All time" for same year | ✅ |

---

## 6. CSV Exports

### 6.1 History — Filtered Export
| Step | Expected |
|------|----------|
| 6.1.1 Apply filters (type, search, date range) | ✅ |
| 6.1.2 Click "Export CSV" | ✅ File dialog opens |
| 6.1.3 Save file → open in spreadsheet | ✅ |
| 6.1.4 Verify CSV headers: Date, Type, Category, Description, Amount | ✅ |
| 6.1.5 Verify rows match filtered table exactly (same count, same data) | ✅ |
| 6.1.6 Verify amounts use `.` decimal separator, 2 decimals | ✅ |
| 6.1.7 Verify UTF-8 encoding (special chars in description) | ✅ |
| 6.1.8 Cancel file dialog → no file created, no error | ✅ |
| 6.1.9 Export with no results → "There are no transactions to export" | ✅ |

### 6.2 Summary — Year Export
| Step | Expected |
|------|----------|
| 6.2.1 Select a year on Financial Summary | ✅ |
| 6.2.2 Click "Export Summary" | ✅ File dialog opens with `sakani_summary_YYYY.csv` |
| 6.2.3 Save file → open in spreadsheet | ✅ |
| 6.2.4 Verify sections: Monthly Totals, Expenses by Category, Income by Category | ✅ |
| 6.2.5 Verify monthly totals include TOTAL row matching UI cards | ✅ |
| 6.2.6 Verify category breakdowns match pie chart data | ✅ |
| 6.2.7 Export year with no data → "There is no data to export for this year" | ✅ |
| 6.2.8 Cancel file dialog → no file created, no error | ✅ |

### 6.3 Export Security
| Step | Expected |
|------|----------|
| 6.3.1 Export as User A → verify only User A's data in CSV | ✅ |
| 6.3.2 Log in as User B → export → verify only User B's data | ✅ |
| 6.3.3 No passwords, salts, or internal IDs in any export | ✅ |

---

## 7. Keyboard Navigation & Accessibility

| Step | Expected |
|------|----------|
| 7.1 Tab through login form: email → password → checkbox → button | ✅ |
| 7.2 Tab through Add Transaction form: all fields reachable | ✅ |
| 7.3 Tab through History filters: all fields reachable | ✅ |
| 7.4 Arrow keys in treeviews: up/down selects rows | ✅ |
| 7.5 Enter key in form fields → triggers save/search | ✅ |
| 7.6 Escape key closes dialogs (edit, cycle, etc.) | ✅ |
| 7.7 Focus visible on all interactive elements | ✅ |
| 7.8 Screen reader labels (check `tk.Label` text) | ✅ |

---

## 8. Window Resizing & Layout

| Step | Expected |
|------|----------|
| 8.1 Resize to minimum (900×600) → no clipping, scrollbars appear if needed | ✅ |
| 8.2 Maximize → content expands, tables fill space | ✅ |
| 8.3 Restore → layout recovers | ✅ |
| 8.4 Sidebar stays fixed width, content scrolls | ✅ |
| 8.5 Dashboard cards wrap or stay in row at min width | ✅ |
| 8.6 Charts resize with canvas | ✅ |

---

## 9. Error Handling & Edge Cases

| Step | Expected |
|------|----------|
| 9.1 Stop MySQL → launch app → "Database connection failed" dialog | ✅ |
| 9.2 Wrong password in env → launch app → clear error message | ✅ |
| 9.3 Wrong host/port → launch app → clear error message | ✅ |
| 9.4 Submit form during DB outage → "Database Error" with details | ✅ |
| 9.5 Duplicate email on signup → inline error, no crash | ✅ |
| 9.6 Very large amount (exceeds DECIMAL(12,2)) → validation error | ✅ |
| 9.7 NaN / Infinity amount → validation error | ✅ |
| 9.8 Empty database (new user) → dashboard shows zeros, "No data yet" on charts | ✅ |

---

## 10. Data Integrity

| Step | Expected |
|------|----------|
| 10.1 Create User A, add transactions → log out → log in as User B → verify User A's data not visible | ✅ |
| 10.2 Edit transaction → verify `updated_at` not required (no such column) but data persists | ✅ |
| 10.3 Delete user → verify their transactions cascade deleted (FK ON DELETE CASCADE) | ✅ |
| 10.4 Delete cycle → linked transactions have `production_cycle_id` set to NULL | ✅ |
| 10.5 All amounts stored as DECIMAL(12,2) → no floating-point drift | ✅ |

## 6. CSV Exports

### 6.1 History — Filtered Export
| Step | Expected |
|------|----------|
| 6.1.1 Apply filters (type, search, date range) | ✅ |
| 6.1.2 Click "Export CSV" | ✅ File dialog opens |
| 6.1.3 Save file → open in spreadsheet | ✅ |
| 6.1.4 Verify CSV headers: Date, Type, Category, Description, Amount | ✅ |
| 6.1.5 Verify rows match filtered table exactly (same count, same data) | ✅ |
| 6.1.6 Verify amounts use `.` decimal separator, 2 decimals | ✅ |
| 6.1.7 Verify UTF-8 encoding (special chars in description) | ✅ |
| 6.1.8 Cancel file dialog → no file created, no error | ✅ |
| 6.1.9 Export with no results → "There are no transactions to export" | ✅ |

### 6.2 Summary — Year Export
| Step | Expected |
|------|----------|
| 6.2.1 Select a year on Financial Summary | ✅ |
| 6.2.2 Click "Export Summary" | ✅ File dialog opens with `sakani_summary_YYYY.csv` |
| 6.2.3 Save file → open in spreadsheet | ✅ |
| 6.2.4 Verify sections: Monthly Totals, Expenses by Category, Income by Category | ✅ |
| 6.2.5 Verify monthly totals include TOTAL row matching UI cards | ✅ |
| 6.2.6 Verify category breakdowns match pie chart data | ✅ |
| 6.2.7 Export year with no data → "There is no data to export for this year" | ✅ |
| 6.2.8 Cancel file dialog → no file created, no error | ✅ |

### 6.3 Summary — Custom Date Range Export
| Step | Expected |
|------|----------|
| 6.3.1 Click "Export Custom Range" on Financial Summary | ✅ Dialog opens with start/end date fields |
| 6.3.2 Enter invalid start date | ❌ "Please use a valid date in YYYY-MM-DD format" |
| 6.3.3 Enter start date after end date | ❌ "Start date must not be after end date" |
| 6.3.4 Enter valid custom range | ✅ File dialog opens with `sakani_summary_YYYY-MM-DD_to_YYYY-MM-DD.csv` |
| 6.3.5 Save file → verify Monthly Totals, Expenses by Category, Income by Category | ✅ |
| 6.3.6 Verify totals match dashboard for same range | ✅ |
| 6.3.7 Cancel file dialog → no file created, no error | ✅ |

### 6.4 Budget Report Export
| Step | Expected |
|------|----------|
| 6.4.1 Click "Export Report" on Budget page | ✅ File dialog opens |
| 6.4.2 Save file → open in spreadsheet | ✅ |
| 6.4.3 Verify headers: Budget Name, Category, Period Type, Start Date, End Date, Budgeted, Actual, Remaining, % Used, Over Budget | ✅ |
| 6.4.4 Cancel file dialog → no file created, no error | ✅ |

### 6.5 Break-even Analysis Export
| Step | Expected |
|------|----------|
| 6.5.1 Click "Break-even" on a cycle → enter price and optional quantity → "Calculate" | ✅ Results show |
| 6.5.2 Click "Export to CSV" in results | ✅ File dialog opens |
| 6.5.3 Save file → verify cycle details, break-even quantity, break-even revenue, expected revenue, estimated net | ✅ |
| 6.5.4 Verify assumptions disclaimer included | ✅ |

### 6.5 Export Security
| Step | Expected |
|------|----------|
| 6.5.1 Export as User A → verify only User A's data in CSV | ✅ |
| 6.5.2 Log in as User B → export → verify only User B's data | ✅ |
| 6.5.3 No passwords, salts, or internal IDs in any export | ✅ |

---

## 7. Budget Management

| Step | Expected |
|------|----------|
| 7.1 Navigate to "Budgets" from sidebar | ✅ List shows user's budgets (empty if none) |
| 7.2 Click "Add Budget" | ✅ Modal opens |
| 7.3 Enter budget name (required), select category, amount, period type, start/end dates, notes | ✅ |
| 7.4 Submit with missing name | ❌ "Please enter a budget name" |
| 7.5 Submit with invalid amount (zero, negative, non-numeric) | ❌ "Amount must be greater than zero" / "Please enter a valid amount" |
| 7.6 Submit with start date after end date | ❌ "Start date must not be after end date" |
| 7.7 Submit with invalid period type | ❌ "Please choose a valid budget period" |
| 7.8 Submit valid budget | ✅ Budget appears in list |
| 7.9 Edit budget → change amount, dates, category | ✅ Updates reflected |
| 7.10 Delete budget → confirm | ✅ Budget removed, transactions unaffected |
| 7.11 Budget card shows: Budgeted, Actual, Remaining, % Used, Over Budget status | ✅ |
| 7.12 Progress bar color: green (on track), amber (≥80%), red (over budget) | ✅ |

---

## 8. Budget vs Actual & Dashboard Integration

| Step | Expected |
|------|----------|
| 8.1 Add expense transactions in a budgeted category and date range | ✅ |
| 8.2 Refresh Budget page → Actual spending updates | ✅ |
| 8.3 Dashboard "Remaining Budget" card shows total remaining across all budgets | ✅ Green if positive, red if negative |
| 8.4 Dashboard "Over Budget" card shows count of over-budget items | ✅ Red if > 0 |
| 8.5 Dashboard "Latest Cycle Net" shows net result of most recent active/planned cycle | ✅ Green if positive, red if negative |
| 8.6 Dashboard "Active Cycles" shows count of planned+active cycles | ✅ |
| 8.7 Dashboard insight cards update when period filter changes | ✅ |

---

## 9. Break-even Analysis

| Step | Expected |
|------|----------|
| 9.1 Create a production cycle with linked expense transactions | ✅ |
| 9.2 Navigate to "Crop Cycles" → click "Break-even" on that cycle | ✅ Dialog opens with cycle summary |
| 9.3 Enter selling price per unit (required) | ✅ |
| 9.4 Enter expected quantity (optional) | ✅ |
| 9.5 Click "Calculate" | ✅ Results show: Cycle expenses, Break-even quantity, Break-even revenue |
| 9.6 If quantity entered: also shows Expected Revenue and Estimated Net | ✅ |
| 9.7 Enter price = 0 → error "Selling price must be greater than zero" | ❌ |
| 9.8 Enter negative price → error | ❌ |
| 9.9 Cycle with no expenses → error "This cycle has no recorded expenses to analyze" | ❌ |
| 9.10 Click "Export to CSV" → verify cycle details, break-even, assumptions | ✅ |
| 9.11 Assumptions disclaimer visible in results and export | ✅ |

---

## 10. Financial Summary (Updated)

### 10.1 Custom Date Range Export
| Step | Expected |
|------|----------|
| 10.1 Click "Export Custom Range" on Financial Summary | ✅ Dialog opens |
| 10.2 Enter invalid date → error | ❌ |
| 10.3 Enter start > end → error | ❌ |
| 10.4 Valid range → file dialog opens with correct filename | ✅ |
| 10.5 Export content matches custom range (not full year) | ✅ |

---

## 11. Keyboard Navigation & Accessibility

| Step | Expected |
|------|----------|
| 11.1 Tab through Budget form: all fields reachable | ✅ |
| 11.2 Tab through Break-even dialog: all fields reachable | ✅ |
| 11.3 Enter key in Budget/Break-even forms → triggers action | ✅ |
| 11.4 Escape key closes Budget/Break-even dialogs | ✅ |
| 11.5 Focus visible on all new interactive elements | ✅ |

---

## 12. Window Resizing & Layout

| Step | Expected |
|------|----------|
| 12.1 Dashboard with 4 insight cards: resize to minimum (900×600) → no clipping | ✅ |
| 12.2 Budget cards with progress bars: resize → progress bar scales | ✅ |
| 12.3 Break-even dialog: responsive at different widths | ✅ |

---

## 13. Error Handling & Edge Cases

| Step | Expected |
|------|----------|
| 13.1 Budget with category that has no transactions → Actual = 0, % Used = 0 | ✅ |
| 13.2 Budget category changed → actual recalculates for new category | ✅ |
| 13.3 Break-even with price that doesn't divide evenly → quantity rounded | ✅ |
| 13.4 Very large numbers in break-even → no overflow, Decimal precision maintained | ✅ |

---

## 14. Automated Test Suite

```bash
python -m unittest discover -s tests -v
```
Expected: 46 tests pass (auth, validation, cycle status transitions, budget validation, break-even calculations).

---

## Known Limitations (Not Blocking)

- No automated browser/UI regression tests (headless Xvfb render only)
- Summary custom-range export requires manual date entry (no date picker widget)
- Break-even uses recorded expenses only; fixed/variable cost split not supported
- Emoji icons in sidebar (may not render on all Linux fonts)
- No print/PDF export
- Overlapping budgets for same category/period are allowed; comparison uses sum of budgets

---

## Sign-off

Tester: ________________________  
Date: ________________________  
All critical paths ✅: ☐ Yes  ☐ No (see notes)

Notes:
________________________________________________________________________
________________________________________________________________________