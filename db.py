import sqlite3

conn = sqlite3.connect('data/ciel.db')
cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS campaigns (
    name      TEXT    NOT NULL UNIQUE,
    chan_id   TEXT    NOT NULL UNIQUE,
    weekday   TEXT    NOT NULL,
    time      TEXT    NOT NULL,
    on_weeks  INTEGER NOT NULL,
    off_weeks INTEGER NOT NULL,
    on_count  INTEGER NOT NULL,
    off_count INTEGER NOT NULL,
    cancelled INTEGER NOT NULL)
''')

conn.commit()


def get_campaigns():
    return cur.execute("SELECT name FROM campaigns").fetchall()

