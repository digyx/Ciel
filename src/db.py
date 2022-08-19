import sqlite3


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class Database:
    def __init__(self, db_path="test.db"):
        self.conn = sqlite3.connect(db_path)
        self.cur = self.conn.cursor()

        self.cur.execute(
            """
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
            """
        )

        self.conn.commit()

    def get_campaigns(self):
        return self.cur.execute("SELECT name FROM campaigns").fetchall()
