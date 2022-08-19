from __future__ import annotations
import datetime

from logger import Logger
from db import conn, cur


weekdays = {
    "Monday": 6,
    "Tuesday": 0,
    "Wednesday": 1,
    "Thursday": 2,
    "Friday": 3,
    "Saturday": 4,
    "Sunday": 5,
}


class Campaign:
    def __init__(self, name: str):
        self.logger = Logger(name)

        res = cur.execute(
            """
            SELECT chan_id, weekday, time, on_weeks, off_weeks, on_count, off_count, cancelled
            FROM campaigns
            WHERE name=?
            """,
            (name,),
        ).fetchone()

        if res is None:
            self.logger.error({"campaign": name, "msg": "Campaign not found."})

            raise NameError("campaign not found.")

        self.name = name
        self.chan_id = res[0]
        self.weekday = res[1]
        self.time = res[2]
        self.on_weeks = res[3]
        self.off_weeks = res[4]
        self.on_count = res[5]
        self.off_count = res[6]
        self.cancelled = res[7]

    @staticmethod
    def new(name: str, chan_id: int, metadata: list[str]) -> Campaign:
        weekday = metadata[0]
        time = metadata[1]
        on_weeks = int(metadata[2])
        off_weeks = int(metadata[3])

        cur.execute(
            """
            INSERT INTO campaigns
            VALUES (
                :name, :chan_id,
                :weekday, :time,
                :on_weeks, :off_weeks,
                0, 0, 0)
            """,
            (name, chan_id, weekday, time, on_weeks, off_weeks),
        )
        conn.commit()

        Logger(name).info({"campaign": name, "event": "created"})

        return Campaign(name)

    def get_chan_id(self) -> int:
        return int(self.chan_id)

    def save(self):
        logger = Logger(self.name)
        res = cur.execute("SELECT name FROM campaigns WHERE name=:name", (self.name,))

        if res.fetchone() is None:
            logger.error({"campaign": self.name, "msg": "Campaign not found."})

            raise NameError("campaign not found.")

        cur.execute(
            """
            UPDATE campaigns
            SET weekday=?, time=?,
            on_weeks=?, off_weeks=?,
            on_count=?, off_count=?,
            cancelled=?
            WHERE name=?
            """,
            (
                self.weekday,
                self.time,
                self.on_weeks,
                self.off_weeks,
                self.on_count,
                self.off_count,
                self.cancelled,
                self.name,
            ),
        )
        conn.commit()

    def cancel(self):
        self.cancelled = 1
        self.save()

    def reset_off_weeks(self):
        self.on_count = 0
        self.off_count = 0
        self.save()

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

    def is_on_week(self) -> bool:
        if self.weekday == "Debug":
            on = True

        if self.on_count != self.on_weeks:
            on = True
            self.on_count += 1
        elif self.off_count != self.off_weeks:
            on = False
            self.off_count += 1
        else:
            on = True
            self.on_count = 1
            self.off_count = 0

        if self.cancelled == 1:
            self.cancelled = 0
            on = False

        self.save()

        return on

    def next_session(self) -> datetime.datetime:
        now = datetime.datetime.now()
        wkday = weekdays[self.weekday] + 1

        # Change Date
        delta = datetime.timedelta((wkday - now.weekday()) % 7)
        session = now + delta

        # Adjust Date for Off Weeks
        week_delta = datetime.timedelta(days=7)
        if self.on_count != self.on_weeks and self.cancelled == 1:
            session += week_delta
        elif self.on_count == self.on_weeks:
            session += week_delta * (self.off_weeks - self.off_count)
            session += week_delta * self.cancelled

        # Adjust Date for Cancellings

        # Change Time
        session = session.replace(hour=int(self.time.strip("PM").split(":")[0]))
        session = session.replace(minute=int(self.time.strip("PM").split(":")[1]))
        session = session.replace(second=0)
        session = session.replace(microsecond=0)

        return session
