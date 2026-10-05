"""Database operations for business services."""

from pathlib import Path

from database import DEFAULT_DATABASE_PATH, connect, initialize_database


def _validated_name(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Service name cannot be empty.")
    return name.strip()


def _require_business(connection, business_id: int) -> None:
    if not connection.execute("SELECT 1 FROM business WHERE id = ?", (business_id,)).fetchone():
        raise ValueError(f"Business {business_id} does not exist.")


def add_service(
    business_id: int, name: str, database_path: str | Path = DEFAULT_DATABASE_PATH
) -> dict:
    clean_name = _validated_name(name)
    initialize_database(database_path)
    with connect(database_path) as connection:
        _require_business(connection, business_id)
        duplicate = connection.execute(
            "SELECT 1 FROM services WHERE business_id = ? AND name = ? COLLATE NOCASE",
            (business_id, clean_name),
        ).fetchone()
        if duplicate:
            raise ValueError(f"Service '{clean_name}' already exists.")
        cursor = connection.execute(
            "INSERT INTO services (business_id, name) VALUES (?, ?)", (business_id, clean_name)
        )
        row = connection.execute(
            "SELECT id, business_id, name, active FROM services WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return dict(row)


def list_services(
    business_id: int,
    include_inactive: bool = False,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> list[dict]:
    initialize_database(database_path)
    with connect(database_path) as connection:
        _require_business(connection, business_id)
        query = "SELECT id, business_id, name, active FROM services WHERE business_id = ?"
        if not include_inactive:
            query += " AND active = 1"
        query += " ORDER BY name COLLATE NOCASE, id"
        rows = connection.execute(query, (business_id,)).fetchall()
    return [dict(row) for row in rows]


def edit_service(
    business_id: int,
    service_id: int,
    name: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> dict:
    clean_name = _validated_name(name)
    initialize_database(database_path)
    with connect(database_path) as connection:
        _require_business(connection, business_id)
        exists = connection.execute(
            "SELECT 1 FROM services WHERE id = ? AND business_id = ?", (service_id, business_id)
        ).fetchone()
        if not exists:
            raise ValueError(f"Service {service_id} does not exist for business {business_id}.")
        duplicate = connection.execute(
            "SELECT 1 FROM services WHERE business_id = ? AND name = ? COLLATE NOCASE AND id <> ?",
            (business_id, clean_name, service_id),
        ).fetchone()
        if duplicate:
            raise ValueError(f"Service '{clean_name}' already exists.")
        connection.execute(
            "UPDATE services SET name = ? WHERE id = ? AND business_id = ?",
            (clean_name, service_id, business_id),
        )
        row = connection.execute(
            "SELECT id, business_id, name, active FROM services WHERE id = ?", (service_id,)
        ).fetchone()
    return dict(row)


def set_service_active(
    business_id: int,
    service_id: int,
    active: bool,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> dict:
    """Activate or deactivate a service without deleting its historical references."""
    initialize_database(database_path)
    with connect(database_path) as connection:
        _require_business(connection, business_id)
        cursor = connection.execute(
            "UPDATE services SET active = ? WHERE id = ? AND business_id = ?",
            (int(active), service_id, business_id),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Service {service_id} does not exist for business {business_id}.")
        row = connection.execute(
            "SELECT id, business_id, name, active FROM services WHERE id = ?", (service_id,)
        ).fetchone()
    return dict(row)


def deactivate_service(business_id: int, service_id: int, database_path=DEFAULT_DATABASE_PATH) -> dict:
    return set_service_active(business_id, service_id, False, database_path)


def activate_service(business_id: int, service_id: int, database_path=DEFAULT_DATABASE_PATH) -> dict:
    return set_service_active(business_id, service_id, True, database_path)
