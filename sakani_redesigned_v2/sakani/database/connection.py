"""MySQL connection helper and first-run database initialisation."""

import os
import re

import mysql.connector
from mysql.connector import Error

from config import DB_CONFIG

CATEGORY_SEED = [
    ("Crop Sales", "income"),
    ("Livestock Sales", "income"),
    ("Harvest Income", "income"),
    ("Other Income", "income"),
    ("Seeds", "expense"),
    ("Fertilizer", "expense"),
    ("Pesticide", "expense"),
    ("Labor", "expense"),
    ("Equipment", "expense"),
    ("Fuel", "expense"),
    ("Transport", "expense"),
    ("Irrigation", "expense"),
    ("Other Expense", "expense"),
]


def get_connection():
    """Return a new connection to the sakani_db database."""
    if not str(DB_CONFIG.get("password") or "").strip():
        raise mysql.connector.Error(
            "Database password is not configured. "
            "Set the SAKANI_DB_PASSWORD environment variable."
        )
    return mysql.connector.connect(**DB_CONFIG)


def _schema_path():
    """Return the absolute path to schema.sql."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def _read_statements():
    """Read schema.sql and split it into individual SQL statements."""
    with open(_schema_path(), "r", encoding="utf-8") as handle:
        raw = handle.read()
    lines = [line for line in raw.splitlines() if not line.strip().startswith("--")]
    sql = "\n".join(lines)
    # Split on semicolon but keep trigger bodies together
    statements = []
    current = ""
    in_trigger = False
    for line in sql.split("\n"):
        stripped = line.strip()
        if stripped.upper().startswith("CREATE TRIGGER"):
            in_trigger = True
        current += line + "\n"
        if in_trigger and stripped.upper() == "END":
            in_trigger = False
            statements.append(current.strip())
            current = ""
        elif not in_trigger and stripped.endswith(";") and stripped != ";":
            statements.append(current.strip())
            current = ""
    if current.strip():
        statements.append(current.strip())
    return statements


def _safe_db_name(name):
    """Validate the configured database name to avoid SQL injection."""
    if not re.match(r"^[A-Za-z0-9_]+$", name):
        raise ValueError("Invalid database name in config.py")
    return name


def init_database():
    """Create the database, tables and seed categories if needed.

    Returns a (success, message) tuple. The caller decides how to show errors.
    """
    connection = None
    cursor = None
    try:
        server_config = {k: v for k, v in DB_CONFIG.items() if k != "database"}
        if not str(server_config.get("password") or "").strip():
            return False, (
                "Database password is not configured. "
                "Set the SAKANI_DB_PASSWORD environment variable."
            )
        connection = mysql.connector.connect(**server_config)
        cursor = connection.cursor()

        db_name = _safe_db_name(DB_CONFIG["database"])
        cursor.execute(
            "CREATE DATABASE IF NOT EXISTS `" + db_name + "` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cursor.execute("USE `" + db_name + "`")

        for statement in _read_statements():
            if "production_cycle_id" in statement and "ALTER TABLE" in statement:
                # Idempotent guarded migrations for the production-cycle upgrade.
                cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'transactions' "
                    "AND COLUMN_NAME = 'production_cycle_id'",
                    (db_name,),
                )
                if cursor.fetchone()[0] == 0:
                    cursor.execute(
                        "ALTER TABLE transactions "
                        "ADD COLUMN production_cycle_id INT NULL AFTER category_id"
                    )
                cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS "
                    "WHERE CONSTRAINT_SCHEMA = %s AND CONSTRAINT_NAME = 'fk_transactions_cycle'",
                    (db_name,),
                )
                if cursor.fetchone()[0] == 0:
                    try:
                        cursor.execute(
                            "ALTER TABLE transactions "
                            "ADD CONSTRAINT fk_transactions_cycle "
                            "FOREIGN KEY (production_cycle_id) "
                            "REFERENCES production_cycles (id) ON DELETE SET NULL"
                        )
                    except Error:
                        pass
                continue
            cursor.execute(statement)

        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO categories (name, type) VALUES (%s, %s)",
                CATEGORY_SEED,
            )

        connection.commit()
        return True, "Database ready."
    except (Error, OSError, ValueError) as exc:
        return False, str(exc)
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Error:
                pass
        if connection is not None and connection.is_connected():
            connection.close()
