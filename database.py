"""SQLite database setup and connection helpers for Business Manager."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent / "business_manager.sqlite3"


SCHEMA = """
CREATE TABLE IF NOT EXISTS business (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0)
);

CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY,
    business_id INTEGER NOT NULL,
    name TEXT NOT NULL COLLATE NOCASE CHECK (length(trim(name)) > 0),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    FOREIGN KEY (business_id) REFERENCES business(id) ON DELETE RESTRICT,
    UNIQUE (business_id, name),
    UNIQUE (id, business_id)
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    transaction_id TEXT NOT NULL UNIQUE,
    business_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    service_name TEXT NOT NULL,
    amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),
    payment_type TEXT NOT NULL CHECK (payment_type IN ('Cash', 'Online')),
    created_at TEXT NOT NULL,
    FOREIGN KEY (business_id) REFERENCES business(id) ON DELETE RESTRICT,
    FOREIGN KEY (service_id, business_id)
        REFERENCES services(id, business_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_transactions_business_created
    ON transactions (business_id, created_at);
CREATE INDEX IF NOT EXISTS idx_transactions_service
    ON transactions (service_id);
"""


@contextmanager
def connect(database_path: str | Path = DEFAULT_DATABASE_PATH) -> Iterator[sqlite3.Connection]:
    """Open a SQLite connection with foreign keys enabled and close it reliably."""
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(database_path: str | Path = DEFAULT_DATABASE_PATH) -> None:
    """Create the initial schema if it does not already exist."""
    with connect(database_path) as connection:
        connection.executescript(SCHEMA)
