from __future__ import annotations
import json
import sqlite3                                                                              # To view DB
from datetime import datetime
from typing import Dict, List

DB_PATH = "ioc_table.db"                                                                    # Can be changed to something else down the line, maybe even select a DB of our choice...

def _conn() -> sqlite3.Connection:                                                          # Connector helper
    return sqlite3.connect(DB_PATH)

def init_db() -> None:                                                                      # From SQL docs, pretty much a DB creation steps
    conn = _conn()

    try: 
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS seen (
                key TEXT PRIMARY KEY,
                first_seen TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
    finally:
        conn.close()

def make_key(ioc: Dict) -> str:                                                             # First time working with keys, might revisit this in terms of security? - Unique key for an IOC record.
    t = (ioc.get("type") or "").strip().lower()
    ind = (ioc.get("indicator") or "").strip().lower()
    return f"{t}:{ind}"

def filter_new(iocs: List[Dict]) -> List[Dict]:                                             # Filerization of IoCs into the DataTable. Ideally returns a smaller DB, not necessarily (think of why not necessarily xd)

    if not iocs:                                                                            # If is a false entry, then return an empty list as well
        return []
    
    conn = _conn()

    try: 
        cur = conn.cursor()                                                                 # Cursor creation (from docs)
        new_recs: List[Dict] = []                                                           # Container for new IoCs

        for rec in iocs:
            key = make_key(rec)                                                             # New key...
            cur.execute("SELECT 1 FROM seen WHERE key = ?", (key,))
            """
            Parameterized query (avoids SQL injection); asks "does a row with this key exist?" If so, returns just 1. Common existence check optimization (according to docs)
            """
            if cur.fetchone() is None:                                                      # Returns NONE if no row found matches
                new_recs.append(rec)                                                        # Adds new ones (AKA unseens ones)
        return new_recs                                                                     # Returns new ones...
    finally:
        conn.close()                                                                        # Here is crucial to close it to prevent leakage and/or future SQL injection. Ideally you always close the connection when done.

def save_new(iocs: List[Dict]) -> int:                                                      # New IoCs addition

    if not iocs:                                                                            # Just to make sure, we always check if its a proper IoC, if not, returns 0 (ignore)
        return 0
    
    conn = _conn()                                                                          # Ya know what it is

    try:
        cur = conn.cursor()
        count = 0                                                                           # This keeps tracks of new rows/entries added, AKA new IoCs

        for rec in iocs:                                                                    # For each IoC, make a unique key!
            key = make_key(rec)
            try:
                cur.execute(                                                                # datetime is un UTC
                    "INSERT INTO seen(key, first_seen) VALUES (?, datetime('now'))",
                    (key,),
                )
                count += 1
            except sqlite3.IntegrityError:                                                  # EXCEPTION! If seen, then goes to "pass", AKA ignores it
                pass
        conn.commit()
        return count
    finally:
        conn.close()