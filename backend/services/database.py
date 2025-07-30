import sqlite3
import os
from backend.services.config_loader import load_config
import matplotlib.pyplot as plt
from datetime import datetime

config = load_config()

# Get the absolute path to the backend directory
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BACKEND_DIR, config['database_name'])

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

def generate_table():
    cur.execute("""
    CREATE TABLE IF NOT EXISTS experimental_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT NOT NULL,
        temperature FLOAT NOT NULL,
        co2 FLOAT NOT NULL,
        o2 FLOAT NOT NULL,
        thermal FLOAT NOT NULL
        );
                """)
    conn.commit()


def insert_data(time,temp,co2,o2,thermal):
    cur.execute("""
        INSERT INTO experimental_data
        (time, temperature, co2, o2, thermal)
        VALUES (?, ?, ?, ?, ?)""",
        (time, temp, co2, o2, thermal))
    conn.commit()
 

def delete_db():
    cur.close()
    conn.close()
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
