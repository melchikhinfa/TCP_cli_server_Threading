import sqlite3
import os

path_to_db = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/data/quota"


def create_quota_table():
    with sqlite3.connect(path_to_db) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS quota 
                         (username text, used_bytes integer)''')
        conn.commit()


def get_quota(username):
    with sqlite3.connect(path_to_db) as conn:
        c = conn.cursor()
        c.execute("SELECT used_bytes FROM quota WHERE username=?", (username,))
        result = c.fetchone()
        if result is None:
            return 0
        return result[0]


def increase_quota(username, size_bytes):
    used = get_quota(username)
    with sqlite3.connect(path_to_db) as conn:
        c = conn.cursor()
        if used == 0:
            c.execute("INSERT INTO quota VALUES (?,?)", (username, size_bytes))
        else:
            c.execute("UPDATE quota SET used_bytes=? WHERE username=?", (used + size_bytes, username))
        conn.commit()


def decrease_quota(username, size_bytes):
    used = get_quota(username)
    with sqlite3.connect(path_to_db) as conn:
        c = conn.cursor()
        c.execute("UPDATE quota SET used_bytes=? WHERE username=?", (max(used - size_bytes, 0), username))
        conn.commit()
