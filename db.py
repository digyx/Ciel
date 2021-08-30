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
    return cur.execute("SELECT name, chan_id, weekday, time, on_weeks, off_weeks FROM campaigns").fetchall()


def full_update(name, chan_id, weekday, time, on_weeks, off_weeks):
    res = cur.execute("SELECT name FROM campaigns WHERE name=:name", (name,))

    if res.fetchone() is None:
        cur.execute("""
            INSERT INTO campaigns
            VALUES (
                :name, :chan_id,
                :weekday, :time,
                :on_weeks, :off_weeks,
                0, 0, 0)
            """, (name, chan_id, weekday, time, on_weeks, off_weeks))
    else:
        cur.execute("""
            UPDATE campaigns
            SET weekday=:weekday, time=:time, on_weeks=:on_weeks, off_weeks=:off_weeks
            WHERE name=:name
        """, (name, weekday, time, on_weeks, off_weeks))

    conn.commit()


def is_on_week(name):
    on_weeks, on_count, off_weeks, off_count, cancelled = cur.execute("""
        SELECT on_weeks, on_count, off_weeks, off_count, cancelled
        FROM campaigns
        WHERE name=:name
    """, (name,)).fetchone()

    if on_count != on_weeks:
        on_off = "on_count"
    elif off_count != off_weeks:
        on_off = "off_count"
    else:
        on_off = "on_count"
        cur.execute("UPDATE campaigns SET on_count=0, off_count=0 WHERE name=:name", (name,))

    cur.execute("""
        UPDATE campaigns
        SET {0} = {0} + 1
        WHERE name=:name""".format(on_off), (name,))

    if cancelled == 1:
        cur.execute("UPDATE campaigns SET cancelled=0 WHERE name=:name", (name,))
        conn.commit()
        return False

    conn.commit()

    return on_off == "on_count"


def cancel(name):
    cur.execute("UPDATE campaigns SET cancelled=1 WHERE name=:name", (name,))
    conn.commit()


def reset_off_weeks(name):
    cur.execute("UPDATE campaigns SET skipped_weeks=0 WHERE name=:name", (name,))
    conn.commit()
