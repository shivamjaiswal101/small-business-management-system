# Business Manager

A local, generic business management desktop app for a small business. Business
names and service catalogs are stored in SQLite as data; the application has no
industry-specific defaults.

## Run

Requires Python 3.10 or newer. It uses the Python standard library only
(Tkinter is included with most desktop Python installations).

```powershell
python main.py
```

On first launch, enter a business name and add at least one service. Then the
app opens the dashboard. Its SQLite database is created next to `main.py` as
`business_manager.sqlite3`.

Configuration commands update the database:

```powershell
python main.py business
python main.py business set "ABC Salon"
python main.py service add "Haircut"
python main.py service list
python main.py service edit 1 "Premium Haircut"
python main.py service remove 1
python main.py service activate 1
```

`service remove` deactivates the service. It does not delete it or its history.

Run the core logic tests with:

```powershell
python -m unittest discover -s tests -v
```

## Version 2 updates

- Refined desktop interface with a dark navigation rail, workspace profile, KPI
  cards, and consistent page layouts.
- Click the date fields directly to open a calendar; choose a month or year, or
  pick a day. Overview totals and transactions filter to the chosen day.
- Formatted Excel `.xlsx` report export with readable column widths, formatted
  revenue cells, frozen headings, and a service breakdown. CSV export remains
  available for data exchange; CSV itself cannot save column widths or styles.

## Features

- First-run business setup and business name settings.
- Service add, edit, deactivate, and activate operations.
- Transactions with an active service, positive amount, fixed Cash/Online
  payment type, generated ID, and automatic timestamp. The service field can
  use the dropdown or a custom name, which is saved to the catalog.
- Dashboard with today's transactions and a search across transaction ID,
  service, payment type, and date. Use the calendar control to view any day's
  transactions and totals in the same dashboard.
- Date-range totals, cash/online revenue, service breakdown, and CSV/XLSX export.
- CLI commands for business name and service configuration.

## Structure

- `database.py` — SQLite schema, foreign-key enforcement, connection handling.
- `business.py` — first-run setup and business name read/update.
- `services.py` — business-scoped service operations and soft deactivation.
- `transactions.py` — amount validation, transaction IDs, timestamps, history.
- `reports.py` — date-filtered SQL aggregation and CSV/XLSX export.
- `cli.py` — configuration command parser and handlers.
- `ui.py` — Tkinter setup and the dashboard, service, report, and settings screens.
- `main.py` — application and CLI entry point.
- `tests/` — standard-library unit tests for core data operations.

## Data and implementation decisions

SQLite foreign keys are enabled for every connection, queries use SQL
parameters, and referenced records cannot be deleted. A transaction stores
both the service foreign key and a service-name snapshot, so renaming a service
does not alter history. Services are soft-deactivated.

Amounts are stored as integer hundredths to avoid floating-point rounding.
Timestamps are stored in UTC and report date ranges use the computer's local
calendar. Payments are constrained to Cash and Online. SQL handles the report
aggregations directly; Pandas would add a dependency without helping this small
reporting workload.

The UI uses Tkinter to keep the local desktop app dependency-free. The database
records carry a business ID, while Version 1 presents a single business setup.
