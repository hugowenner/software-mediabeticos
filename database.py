# database.py

import sqlite3
from constants import DB_FILE

class Database:
    def __init__(self, db_path: str = DB_FILE):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
              date TEXT NOT NULL,
              meal TEXT NOT NULL,
              carbs REAL,
              glicemia REAL,
              lispro REAL,
              bolus REAL,
              PRIMARY KEY (date, meal)
            )
            """
        )
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON entries (date);")

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS glargina_doses (
              date TEXT PRIMARY KEY NOT NULL,
              dose REAL
            )
            """
        )
        self.conn.commit()

    def upsert_entry(self, date: str, meal: str, values: dict):
        self.conn.execute(
            """
            INSERT INTO entries (date, meal, carbs, glicemia, lispro, bolus)
            VALUES (:date, :meal, :carbs, :glicemia, :lispro, :bolus)
            ON CONFLICT(date, meal) DO UPDATE SET
              carbs=excluded.carbs,
              glicemia=excluded.glicemia,
              lispro=excluded.lispro,
              bolus=excluded.bolus
            """,
            {"date": date, "meal": meal, **values},
        )
        self.conn.commit()

    def upsert_glargina_dose(self, date: str, dose: float):
        self.conn.execute(
            """
            INSERT INTO glargina_doses (date, dose)
            VALUES (?, ?)
            ON CONFLICT(date) DO UPDATE SET
              dose=excluded.dose
            """,
            (date, dose),
        )
        self.conn.commit()

    def fetch_entry(self, date: str, meal: str):
        cur = self.conn.execute(
            """
            SELECT carbs, glicemia, lispro, bolus
            FROM entries
            WHERE date = ? AND meal = ?
            """,
            (date, meal),
        )
        return cur.fetchone()

    def fetch_glargina_dose(self, date: str):
        cur = self.conn.execute(
            """
            SELECT dose FROM glargina_doses WHERE date = ?
            """,
            (date,),
        )
        result = cur.fetchone()
        return result[0] if result else None

    def fetch_range(self, start: str, end: str):
        cur = self.conn.execute(
            """
            SELECT date, meal, carbs, glicemia, lispro, bolus
            FROM entries
            WHERE date BETWEEN ? AND ?
            ORDER BY date, meal
            """,
            (start, end),
        )
        return cur.fetchall()

    def fetch_glargina_range(self, start: str, end: str):
        cur = self.conn.execute(
            """
            SELECT date, dose
            FROM glargina_doses
            WHERE date BETWEEN ? AND ?
            ORDER BY date
            """,
            (start, end),
        )
        return cur.fetchall()

    def close(self):
        self.conn.close()