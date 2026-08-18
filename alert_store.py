import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


DATABASE_PATH = Path(__file__).with_name("alerts.db")


def get_connection():
    """Open a connection to the local alert database."""

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    """Create the alert-history table if it does not exist."""

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER,
                iaq_status TEXT NOT NULL,
                co2 REAL NOT NULL,
                pm25 REAL NOT NULL,
                alert_title TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                sent_at TEXT NOT NULL
            )
            """
        )


def get_last_alert():
    """Return the most recently recorded email alert."""

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM alerts
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()


def should_send_alert(iaq_status, cooldown_minutes):
    """Decide whether a new email may be sent."""

    last_alert = get_last_alert()

    if last_alert is None:
        return True

    if last_alert["iaq_status"] != iaq_status:
        return True

    last_sent = datetime.fromisoformat(
        last_alert["sent_at"]
    )

    cooldown_ends = last_sent + timedelta(
        minutes=cooldown_minutes
    )

    return datetime.now(timezone.utc) >= cooldown_ends


def record_alert(readings, assessment):
    """Save a successfully sent alert."""

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO alerts (
                entry_id,
                iaq_status,
                co2,
                pm25,
                alert_title,
                recommendation,
                sent_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                readings.get("entry_id"),
                assessment["iaq_status"],
                readings["co2"],
                readings["pm25"],
                assessment["alert_title"],
                assessment["recommendation"],
                datetime.now(timezone.utc).isoformat(),
            ),
        )