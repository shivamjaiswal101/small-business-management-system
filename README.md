# Business Management System

A Python-based desktop application for managing business services, transactions, revenue, and reports through a local SQLite database.

The system provides a complete workflow for setting up a business, managing its service catalog, recording transactions, analyzing revenue, and exporting reports in CSV and Excel formats.

## Overview

This project was built as a practical business management system rather than a simple CRUD application.

It focuses on:

- Structured SQLite database design
- Transaction and service management
- Revenue and payment analysis
- Date-based reporting
- CSV and Excel report generation
- Data validation and historical consistency
- A dependency-free desktop interface using Tkinter
- Automated unit testing for core business logic

## Key Features

### Business Setup
- First-run business configuration
- Business name management
- Business-specific service catalog

### Service Management
- Add new services
- Edit existing services
- Activate or deactivate services
- Preserve historical transaction data when services are renamed
- Store custom services directly from the transaction workflow

### Transaction Management
- Record transactions with:
  - Service
  - Amount
  - Payment method
  - Transaction ID
  - Timestamp
- Supports Cash and Online payments
- Validates transaction amounts
- Automatically generates transaction IDs
- Maintains transaction history

### Dashboard & Search
- View daily transactions
- Search transactions by:
  - Transaction ID
  - Service
  - Payment method
  - Date
- Select a specific date using the calendar interface
- View revenue totals for the selected date

### Reporting & Analytics
- Date-range revenue analysis
- Cash vs Online revenue
- Service-wise revenue breakdown
- CSV export
- Formatted Excel `.xlsx` export
- Frozen Excel headings
- Readable column widths
- Formatted revenue values

## Screenshots

> Screenshots will be added here.

<!--
Example:

![Dashboard](screenshots/dashboard.png)

![Reports](screenshots/reports.png)

![Service Management](screenshots/services.png)
-->

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Tkinter | Desktop user interface |
| SQLite | Local database |
| SQL | Data storage and reporting queries |
| CSV | Data export |
| Excel (.xlsx) | Formatted report export |
| unittest | Automated testing |

The application uses Python's standard library and does not require external packages for its core functionality.

## Project Architecture

```text
Business Management System
│
├── main.py
│   └── Application and CLI entry point
│
├── ui.py
│   └── Tkinter interface and application screens
│
├── database.py
│   └── SQLite connection, schema and database handling
│
├── business.py
│   └── Business setup and configuration
│
├── services.py
│   └── Service catalog operations
│
├── transactions.py
│   └── Transaction creation and validation
│
├── reports.py
│   └── Revenue analysis and report exports
│
├── cli.py
│   └── Command-line configuration interface
│
├── tests/
│   └── Unit tests for core business logic
│
├── .gitignore
│   └── Files excluded from version control
│
└── README.md
    └── Project documentation
