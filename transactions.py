"""Validated transaction creation and history queries."""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
import secrets
import sqlite3

from database import DEFAULT_DATABASE_PATH, connect, initialize_database


PAYMENT_TYPES = ("Cash", "Online")


def amount_to_minor_units(amount: str | int | float | Decimal) -> int:
    """Convert a positive decimal amount to hundredths without float arithmetic."""
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError):
        raise ValueError("Enter a valid amount.") from None
    if not value.is_finite() or value <= 0:
        raise ValueError("Amount must be greater than zero.")
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if rounded != value:
        raise ValueError("Amount can have at most two decimal places.")
    return int(rounded * 100)


def _save_transaction(connection, business_id, service, amount_minor, payment_type):
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    while True:
        transaction_id = f"TXN-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
        try:
            cursor = connection.execute(
                """INSERT INTO transactions
                (transaction_id, business_id, service_id, service_name,
                 amount_minor, payment_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (transaction_id, business_id, service["id"], service["name"], amount_minor,
                 payment_type, created_at),
            )
            row = connection.execute(
                "SELECT * FROM transactions WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            return dict(row)
        except sqlite3.IntegrityError as error:
            if "transactions.transaction_id" in str(error):
                continue
            raise


def create_transaction(
    business_id: int,
    service_id: int,
    amount: str | int | float | Decimal,
    payment_type: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> dict:
    amount_minor = amount_to_minor_units(amount)
    if payment_type not in PAYMENT_TYPES:
        raise ValueError("Payment type must be Cash or Online.")
    initialize_database(database_path)
    with connect(database_path) as connection:
        service = connection.execute(
            "SELECT id, name FROM services WHERE id = ? AND business_id = ? AND active = 1",
            (service_id, business_id),
        ).fetchone()
        if not service:
            raise ValueError("Choose an active service belonging to this business.")
        return _save_transaction(connection, business_id, service, amount_minor, payment_type)


def create_transaction_for_service_name(
    business_id: int,
    service_name: str,
    amount: str | int | float | Decimal,
    payment_type: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> dict:
    """Create a transaction by service name, adding new custom services atomically."""
    name = service_name.strip() if isinstance(service_name, str) else ""
    if not name:
        raise ValueError("Enter or choose a service.")
    amount_minor = amount_to_minor_units(amount)
    if payment_type not in PAYMENT_TYPES:
        raise ValueError("Payment type must be Cash or Online.")
    initialize_database(database_path)
    with connect(database_path) as connection:
        service = connection.execute(
            "SELECT id, name, active FROM services WHERE business_id = ? AND name = ? COLLATE NOCASE",
            (business_id, name),
        ).fetchone()
        if service and not service["active"]:
            raise ValueError("That service is inactive. Activate it in Services before using it.")
        if not service:
            if not connection.execute("SELECT 1 FROM business WHERE id = ?", (business_id,)).fetchone():
                raise ValueError("The configured business could not be found.")
            cursor = connection.execute(
                "INSERT INTO services (business_id, name) VALUES (?, ?)", (business_id, name)
            )
            service = {"id": cursor.lastrowid, "name": name}
        return _save_transaction(connection, business_id, service, amount_minor, payment_type)


def list_transactions(
    business_id: int,
    search: str = "",
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = 500,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> list[dict]:
    """List matching transactions newest first. Search covers id, service, payment, and date."""
    initialize_database(database_path)
    clauses = ["business_id = ?"]
    parameters: list = [business_id]
    if search.strip():
        pattern = f"%{search.strip()}%"
        clauses.append(
            "(transaction_id LIKE ? OR service_name LIKE ? OR payment_type LIKE ? OR created_at LIKE ?)"
        )
        parameters.extend([pattern] * 4)
    if start_date:
        start_bound = datetime.combine(date.fromisoformat(start_date), time.min).astimezone(timezone.utc)
        clauses.append("created_at >= ?")
        parameters.append(start_bound.isoformat(timespec="seconds"))
    if end_date:
        end_bound = datetime.combine(date.fromisoformat(end_date) + timedelta(days=1), time.min).astimezone(timezone.utc)
        clauses.append("created_at < ?")
        parameters.append(end_bound.isoformat(timespec="seconds"))
    query = "SELECT * FROM transactions WHERE " + " AND ".join(clauses)
    query += " ORDER BY created_at DESC, id DESC"
    if limit is not None:
        query += " LIMIT ?"
        parameters.append(limit)
    with connect(database_path) as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [dict(row) for row in rows]
