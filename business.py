"""Database operations for the single business configured in Version 1."""

from pathlib import Path
from database import DEFAULT_DATABASE_PATH, connect, initialize_database


def _validated_name(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Business name cannot be empty.")
    return name.strip()


def get_business(database_path: str | Path = DEFAULT_DATABASE_PATH) -> dict | None:
    """Return the configured business, or None before first-run setup."""
    initialize_database(database_path)
    with connect(database_path) as connection:
        row = connection.execute("SELECT id, name FROM business ORDER BY id LIMIT 1").fetchone()
    return dict(row) if row else None


def set_business(name: str, database_path: str | Path = DEFAULT_DATABASE_PATH) -> dict:
    """Create the business if absent, otherwise update its name."""
    clean_name = _validated_name(name)
    initialize_database(database_path)
    with connect(database_path) as connection:
        row = connection.execute("SELECT id FROM business ORDER BY id LIMIT 1").fetchone()
        if row:
            connection.execute("UPDATE business SET name = ? WHERE id = ?", (clean_name, row["id"]))
            business_id = row["id"]
        else:
            cursor = connection.execute("INSERT INTO business (name) VALUES (?)", (clean_name,))
            business_id = cursor.lastrowid
        result = connection.execute(
            "SELECT id, name FROM business WHERE id = ?", (business_id,)
        ).fetchone()
    return dict(result)


def configure_business(
    name: str,
    services: list[str],
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> dict:
    """Save first-run business setup and its initial services atomically."""
    clean_name = _validated_name(name)
    clean_services = [service.strip() for service in services if isinstance(service, str) and service.strip()]
    if not clean_services:
        raise ValueError("Add at least one service.")
    normalized = [service.casefold() for service in clean_services]
    if len(set(normalized)) != len(normalized):
        raise ValueError("Service names must be unique.")

    initialize_database(database_path)
    with connect(database_path) as connection:
        if connection.execute("SELECT 1 FROM business LIMIT 1").fetchone():
            raise ValueError("Business setup has already been completed.")
        cursor = connection.execute("INSERT INTO business (name) VALUES (?)", (clean_name,))
        business_id = cursor.lastrowid
        connection.executemany(
            "INSERT INTO services (business_id, name) VALUES (?, ?)",
            [(business_id, service) for service in clean_services],
        )
        row = connection.execute(
            "SELECT id, name FROM business WHERE id = ?", (business_id,)
        ).fetchone()
    return dict(row)
