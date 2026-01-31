"""Database setup and utilities for SQLite persistence."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, date
from pathlib import Path
from typing import Generator, Optional, List

# Database path
DB_PATH = Path(__file__).parent / "data" / "impact_coach.db"


def get_db_path() -> Path:
    """Get the database path, ensuring the directory exists."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DB_PATH


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections."""
    conn = sqlite3.connect(get_db_path(), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database() -> None:
    """Initialize the database with required tables."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Action logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS action_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                category TEXT NOT NULL,
                item TEXT NOT NULL,
                amount REAL NOT NULL,
                subcategory TEXT,
                time_of_day TEXT DEFAULT 'standard',
                location TEXT,
                notes TEXT,
                co2e_kg REAL NOT NULL DEFAULT 0,
                water_l REAL NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Index for efficient date queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_action_logs_date
            ON action_logs(date)
        """)

        # User preferences table (for future use)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()


def insert_action_log(
    date_val: date,
    category: str,
    item: str,
    amount: float,
    co2e_kg: float,
    water_l: float,
    subcategory: Optional[str] = None,
    time_of_day: str = "standard",
    location: Optional[str] = None,
    notes: Optional[str] = None
) -> int:
    """Insert a new action log and return its ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO action_logs
            (date, category, item, amount, subcategory, time_of_day, location, notes, co2e_kg, water_l)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (date_val, category, item, amount, subcategory, time_of_day, location, notes, co2e_kg, water_l))
        conn.commit()
        return cursor.lastrowid


def get_actions_by_date(target_date: date) -> List[dict]:
    """Get all actions for a specific date."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM action_logs
            WHERE date = ?
            ORDER BY created_at DESC
        """, (target_date,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_actions_date_range(start_date: date, end_date: date) -> List[dict]:
    """Get all actions within a date range."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM action_logs
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC, created_at DESC
        """, (start_date, end_date))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_daily_totals(target_date: date) -> dict:
    """Get aggregated totals for a specific date."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                category,
                SUM(co2e_kg) as total_co2e,
                SUM(water_l) as total_water,
                COUNT(*) as action_count
            FROM action_logs
            WHERE date = ?
            GROUP BY category
        """, (target_date,))
        rows = cursor.fetchall()
        return {row['category']: dict(row) for row in rows}


def get_weekly_totals(end_date: date) -> List[dict]:
    """Get daily totals for the past 7 days."""
    from datetime import timedelta
    start_date = end_date - timedelta(days=6)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                date,
                SUM(co2e_kg) as total_co2e,
                SUM(water_l) as total_water,
                COUNT(*) as action_count
            FROM action_logs
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date ASC
        """, (start_date, end_date))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_top_contributors(target_date: date, limit: int = 3) -> List[dict]:
    """Get top impact contributors for a specific date."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                category,
                item,
                amount,
                co2e_kg,
                water_l
            FROM action_logs
            WHERE date = ?
            ORDER BY co2e_kg DESC
            LIMIT ?
        """, (target_date, limit))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_streak_days() -> int:
    """Get the number of consecutive days with logged actions."""
    from datetime import timedelta

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT date
            FROM action_logs
            ORDER BY date DESC
        """)
        dates = [row['date'] for row in cursor.fetchall()]

        if not dates:
            return 0

        # Convert string dates to date objects if needed
        if isinstance(dates[0], str):
            dates = [datetime.strptime(d, '%Y-%m-%d').date() for d in dates]

        streak = 0
        today = date.today()
        expected_date = today

        for d in dates:
            if d == expected_date:
                streak += 1
                expected_date -= timedelta(days=1)
            elif d < expected_date:
                break

        return streak


def delete_action_log(action_id: int) -> bool:
    """Delete an action log by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM action_logs WHERE id = ?", (action_id,))
        conn.commit()
        return cursor.rowcount > 0


def clear_all_actions() -> int:
    """Clear all action logs. Returns the number of deleted rows."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM action_logs")
        conn.commit()
        return cursor.rowcount
