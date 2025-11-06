import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import threading

DB_NAME = "jobs_tracker.db"
_local = threading.local()


def get_connection():
    """Get thread-local database connection"""
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
    return _local.conn


def init_database():
    """Initialize database tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            job_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, date)
        )
    """)
    
    # Tracker data table (stores state for each tracker)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trackers (
            name TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            total_tracked INTEGER DEFAULT 0,
            last_run TIMESTAMP,
            data TEXT
        )
    """)
    
    # Activity logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracker_name TEXT NOT NULL,
            log_type TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Job statistics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            total_jobs INTEGER,
            avg_salary INTEGER,
            locations TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, date)
        )
    """)
    
    conn.commit()


# Jobs operations
def write_jobs(category: str, date: str, jobs: List[Dict]):
    """Store jobs data for a category and date"""
    conn = get_connection()
    cursor = conn.cursor()
    
    job_data = json.dumps(jobs)
    cursor.execute("""
        INSERT OR REPLACE INTO jobs (category, date, job_data)
        VALUES (?, ?, ?)
    """, (category, date, job_data))
    
    conn.commit()


def read_jobs(category: str, date: str) -> Optional[List[Dict]]:
    """Read jobs data for a category and date"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT job_data FROM jobs
        WHERE category = ? AND date = ?
    """, (category, date))
    
    row = cursor.fetchone()
    if row:
        return json.loads(row[0])
    return None


# Tracker operations
def write_tracker_data(name: str, category: str, total_tracked: int, data: Dict):
    """Update tracker state"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO trackers (name, category, total_tracked, last_run, data)
        VALUES (?, ?, ?, ?, ?)
    """, (name, category, total_tracked, datetime.now(), json.dumps(data)))
    
    conn.commit()


def read_tracker_data(name: str) -> Optional[Dict]:
    """Read tracker state"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT category, total_tracked, last_run, data FROM trackers
        WHERE name = ?
    """, (name,))
    
    row = cursor.fetchone()
    if row:
        return {
            "category": row[0],
            "total_tracked": row[1],
            "last_run": row[2],
            "data": json.loads(row[3]) if row[3] else {}
        }
    return None


# Logging operations
def write_log(tracker_name: str, log_type: str, message: str):
    """Write a log entry"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO logs (tracker_name, log_type, message)
        VALUES (?, ?, ?)
    """, (tracker_name, log_type, message))
    
    conn.commit()


def read_logs(tracker_name: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """Read log entries"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if tracker_name:
        cursor.execute("""
            SELECT tracker_name, log_type, message, timestamp FROM logs
            WHERE tracker_name = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (tracker_name, limit))
    else:
        cursor.execute("""
            SELECT tracker_name, log_type, message, timestamp FROM logs
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
    
    return [dict(row) for row in cursor.fetchall()]


# Statistics operations
def write_job_stats(category: str, date: str, total_jobs: int, avg_salary: int, locations: List[Dict]):
    """Store job statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO job_stats (category, date, total_jobs, avg_salary, locations)
        VALUES (?, ?, ?, ?, ?)
    """, (category, date, total_jobs, avg_salary, json.dumps(locations)))
    
    conn.commit()


def read_job_stats(category: str, days: int = 7) -> List[Dict]:
    """Read job statistics for past N days"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT date, total_jobs, avg_salary, locations FROM job_stats
        WHERE category = ?
        ORDER BY date DESC
        LIMIT ?
    """, (category, days))
    
    return [dict(row) for row in cursor.fetchall()]


def get_all_stats_today() -> List[Dict]:
    """Get today's stats for all categories"""
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().date().strftime("%Y-%m-%d")
    
    cursor.execute("""
        SELECT category, total_jobs, avg_salary, locations FROM job_stats
        WHERE date = ?
    """, (today,))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "category": row[0],
            "total_jobs": row[1],
            "avg_salary": row[2],
            "locations": json.loads(row[3]) if row[3] else []
        })
    
    return results


# Initialize database on import
init_database()