# This file is part of motionEye.
#
# motionEye is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sqlite3
import time
import os
import logging
from motioneye import settings

# --- Database Setup ---
DB_PATH = os.path.join(settings.CONF_PATH, 'motioneye.db')
_DB_CONN = None

def get_db_connection():
    """Gets a connection to the SQLite database."""
    global _DB_CONN
    if _DB_CONN is None:
        try:
            _DB_CONN = sqlite3.connect(DB_PATH)
            _DB_CONN.row_factory = sqlite3.Row
            logging.info(f"Successfully connected to database at {DB_PATH}")
        except sqlite3.Error as e:
            logging.error(f"Database connection failed: {e}")
            raise
    return _DB_CONN

def optimize_database():
    """Add indexes to improve query performance"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Add indexes for common queries
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_events_camera_id ON events(camera_id)',
            'CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_events_camera_timestamp ON events(camera_id, timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_media_camera_id ON media_files(camera_id)',
            'CREATE INDEX IF NOT EXISTS idx_media_timestamp ON media_files(timestamp)',
        ]

        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except sqlite3.OperationalError as e:
                # This can happen if the tables (events, media_files) don't exist yet, which is fine.
                logging.warning(f"Could not create index, this may be normal on first run: {e}")


        conn.commit()
        logging.info("Database indexes created successfully")

    except Exception as e:
        logging.error(f"Failed to optimize database: {e}")


def init_db():
    """Initializes the database and creates tables if they don't exist."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create login_attempts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        ''')
        conn.commit()
        logging.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logging.error(f"Database initialization failed: {e}")
        raise

    # Apply database optimizations
    optimize_database()

# --- Rate Limiting ---
_RATE_LIMIT_WINDOW = 300  # 5 minutes
_MAX_ATTEMPTS = 5

def check_rate_limit(username: str):
    """
    Checks if a user has exceeded the login rate limit.
    Raises an exception if the limit is exceeded.
    """
    now = time.time()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Delete attempts older than the rate limit window
        # Using parameterized queries to prevent SQL injection
        cursor.execute(
            "DELETE FROM login_attempts WHERE timestamp < ?",
            (now - _RATE_LIMIT_WINDOW,)
        )

        # Get the number of recent attempts for the user
        cursor.execute(
            "SELECT timestamp FROM login_attempts WHERE username = ? ORDER BY timestamp ASC",
            (username,)
        )
        attempts = cursor.fetchall()

        if len(attempts) >= _MAX_ATTEMPTS:
            first_attempt_time = attempts[0]['timestamp']
            wait_time = _RATE_LIMIT_WINDOW - (now - first_attempt_time)
            # Return a clear error message, but avoid leaking too much info
            raise Exception(f'Too many login attempts. Please try again in {int(wait_time)} seconds.')

        # Record the new login attempt
        cursor.execute(
            "INSERT INTO login_attempts (username, timestamp) VALUES (?, ?)",
            (username, now)
        )

        conn.commit()

    except sqlite3.Error as e:
        logging.error(f"Rate limit check failed due to a database error: {e}")
        # In case of DB error, fail open to not lock out users, but log it.
        # Depending on security posture, one might choose to fail closed.
    except Exception:
        # Re-raise the "Too many login attempts" exception
        raise