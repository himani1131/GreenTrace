"""
database.py - SQLite storage (Python's built-in sqlite3 module, no install needed).

Tables
  analyses : one row per analysis (history, dashboard totals, reports)
  rules    : the optimization rules and how often each was applied
Always pass values with ? placeholders (never build SQL with f-strings) so user
input can never change the meaning of a query (SQL injection).
"""
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "greentrace.db")


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(rules):
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            language TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            original_code TEXT NOT NULL,
            optimized_code TEXT NOT NULL,
            energy_saved_wh REAL NOT NULL DEFAULT 0,
            co2_saved_g REAL NOT NULL DEFAULT 0,
            result_json TEXT NOT NULL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS rules (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            severity TEXT NOT NULL,
            times_applied INTEGER NOT NULL DEFAULT 0)""")
        for rule_id, info in rules.items():
            db.execute("INSERT OR IGNORE INTO rules (id, title, description, severity) VALUES (?, ?, ?, ?)",
                       (rule_id, info["title"], info["why"], info["severity"]))


def save_analysis(result):
    """Stores one finished analysis and returns its id."""
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    comparison = result["comparison"]
    with connect() as db:
        cursor = db.execute(
            """INSERT INTO analyses (created_at, language, title, status, original_code, optimized_code,
                                     energy_saved_wh, co2_saved_g, result_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (created_at, result["language"], result["title"], result["status"],
             result["original"]["code"], result["optimized"]["code"],
             comparison["energy_saved_wh"] or 0, comparison["co2_saved_g"] or 0, "{}"))
        analysis_id = cursor.lastrowid
        result["id"] = analysis_id
        result["created_at"] = created_at
        db.execute("UPDATE analyses SET result_json = ? WHERE id = ?", (json.dumps(result), analysis_id))
        for rule in result["applied"]:
            db.execute("UPDATE rules SET times_applied = times_applied + 1 WHERE id = ?", (rule["rule_id"],))
    return analysis_id


def get_analysis(analysis_id):
    with connect() as db:
        row = db.execute("SELECT result_json FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
    return json.loads(row["result_json"]) if row else None


def list_history(limit=50):
    with connect() as db:
        rows = db.execute("""SELECT id, created_at, language, title, status
                             FROM analyses ORDER BY id DESC LIMIT ?""", (limit,)).fetchall()
    return [dict(r) for r in rows]


def list_rules():
    with connect() as db:
        rows = db.execute("SELECT id, title, description, severity, times_applied FROM rules").fetchall()
    return [dict(r) for r in rows]


def stats():
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(timespec="seconds")
    with connect() as db:
        total = db.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
        this_week = db.execute("SELECT COUNT(*) FROM analyses WHERE created_at >= ?", (week_ago,)).fetchone()[0]
        optimized = db.execute("SELECT COUNT(*) FROM analyses WHERE status = 'Optimized'").fetchone()[0]
        rejected = db.execute("SELECT COUNT(*) FROM analyses WHERE status = 'Rejected'").fetchone()[0]
        energy, co2 = db.execute("""SELECT COALESCE(SUM(energy_saved_wh), 0), COALESCE(SUM(co2_saved_g), 0)
                                    FROM analyses WHERE status = 'Optimized'""").fetchone()
    attempted = optimized + rejected
    return {"analyses": total, "this_week": this_week, "optimizations": optimized,
            "success_rate": round(optimized / attempted * 100) if attempted else None,
            "energy_saved_wh": energy, "co2_saved_g": co2}
