import datetime
from __future__ import annotations

from logger import Logger
from db import conn, cur


weekdays = {
    "Monday":    6,
    "Tuesday":   0,
    "Wednesday": 1,
    "Thursday":  2,
    "Friday":    3,
    "Saturday":  4,
    "Sunday":    5
}


class Campaign:
    def __init__(self, name: str):
        self.logger = Logger(name)

        res = cur.execute("""
            SELECT chan_id, weekday, time, on_weeks, off_weeks, on_count, off_count, cancelled
            FROM campaigns
            WHERE name=:name
        """, (name,)).fetchone()

        if res is None:
            self.logger.error({
                "campaign": name,
                "msg": "Campaign not found."
            })

            raise NameError("campaign not found.")

        self.name      = name
        self.chan_id   = res[0]
        self.weekday   = res[1]
        self.time      = res[2]
        self.on_weeks  = res[3]
        self.off_weeks = res[4]
        self.on_count  = res[5]
        self.off_count = res[6]
        self.cancelled = res[7]

    @staticmethod
    def new(name: str, chan_id: int, metadata: str) -> Campaign:
        weekday   = metadata[1]
        time      = metadata[2]
        on_weeks  = int(metadata[3]) + 1
        off_weeks = int(metadata[4]) + 1

        cur.execute("""
            INSERT INTO campaigns
            VALUES (
                :name, :chan_id,
                :weekday, :time,
                :on_weeks, :off_weeks,
                0, 0, 0)
            """, (name, chan_id, weekday, time, on_weeks, off_weeks))

        return Campaign(name)


    def get_chan_id(self) -> int:
        return int(self.chan_id)


    def save(self):
        logger = Logger(self.name)
        res = cur.execute("SELECT name FROM campaigns WHERE name=:name", (self.name,))

        if res.fetchone() is None:
            logger.error({
                "campaign": self.name,
                "msg": "Campaign not found."
            })

            raise NameError("campaign not found.")

        cur.execute("""
            UPDATE campaigns
            SET weekday=:weekday, time=:time, on_weeks=:on_weeks, off_weeks=:off_weeks, on_count=0, off_count=0
            WHERE name=:name
        """, (self.weekday, self.time, self.on_weeks, self.off_weeks, self.name))

        conn.commit()


    def cancel(self):
        cur.execute("UPDATE campaigns SET cancelled=1 WHERE name=:name", (self.name,))
        conn.commit()


    def reset_off_weeks(self):
        cur.execute("UPDATE campaigns SET on_count=0, off_count=0 WHERE name=:name", (self.name,))
        conn.commit()


    # Check if it's 8 PM UTC the day before the session
    def is_correct_time(self):
        current_day = datetime.date.today().weekday()
        current_time = datetime.datetime.now().time()

        # Debug only
        if self.weekday == "Debug":
            return True

        if current_day != weekdays[self.weekday]:
            return False
        elif current_time.hour != 20:
            return False
        elif current_time.minute != 0:
            return False

        return True


    def is_on_week(self):
        on_weeks, on_count, off_weeks, off_count, cancelled = cur.execute("""
            SELECT on_weeks, on_count, off_weeks, off_count, cancelled
            FROM campaigns
            WHERE name=:name
        """, (self.name,)).fetchone()

        if on_count != on_weeks:
            on_off = "on_count"
        elif off_count != off_weeks:
            on_off = "off_count"
        else:
            on_off = "on_count"
            cur.execute("UPDATE campaigns SET on_count=0, off_count=0 WHERE name=:name", (self.name,))

        cur.execute("""
            UPDATE campaigns
            SET {0} = {0} + 1
            WHERE name=:name""".format(on_off), (self.name,))

        if cancelled == 1:
            cur.execute("UPDATE campaigns SET cancelled=0 WHERE name=:name", (self.name,))
            conn.commit()
            return False

        conn.commit()

        return on_off == "on_count"


    def next_session(self):
        now = datetime.datetime.now()
        wkday = weekdays[self.weekday] + 1

        # Change Date
        delta = datetime.timedelta((wkday - now.weekday()) % 7)
        session = now + delta

        # Change Time
        session = session.replace(hour=int(self.time.strip("PM").split(":")[0]))
        session = session.replace(minute=int(self.time.strip("PM").split(":")[1]))
        session = session.replace(second=0)
        session = session.replace(microsecond=0)

        return session

