import os
import sqlite3
from datetime import datetime

DB_NAME = "production_harness.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS harness_stack (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            build_number TEXT NOT NULL,
            project_name TEXT NOT NULL,
            tester_name TEXT NOT NULL,
            section_code TEXT NOT NULL,
            cabinet_code TEXT NOT NULL,
            barcode_payload TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'IN_STACK'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            harness_id INTEGER,
            operator_name TEXT NOT NULL,
            scanned_at TEXT NOT NULL,
            match_status TEXT NOT NULL,
            FOREIGN KEY (harness_id) REFERENCES harness_stack (id)
        )
    ''')
    conn.commit()
    conn.close()

def get_next_build_number() -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM harness_stack")
    row = cursor.fetchone()
    conn.close()
    
    max_id = row[0] if row and row[0] is not None else 0
    return f"{max_id + 1:04d}"

def add_harness_batch(project_name: str, tester_name: str, section_code: str, cabinet_type: str, cells: list) -> tuple:
    build_num = get_next_build_number()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now().strftime("%y%m%d")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    records = []
    for cell in cells:
        payload = f"{build_num}{cell}{cabinet_type}{date_str}"
        cursor.execute('''
            INSERT INTO harness_stack (build_number, project_name, tester_name, section_code, cabinet_code, barcode_payload, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'IN_STACK')
        ''', (build_num, project_name, tester_name, section_code, cabinet_type, payload, created_at))
        record_id = cursor.lastrowid
        records.append({
            "id": record_id,
            "cell": cell,
            "payload": payload
        })
        
    conn.commit()
    conn.close()
    return build_num, records