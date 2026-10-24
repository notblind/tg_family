import sqlite3
from config import settings


def enable_wal_mode():
    conn = sqlite3.connect(settings.database_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.close()
