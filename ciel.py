import discord
from discord.ext import tasks

import datetime, os
import db


weekdays = {
    "Monday":    6,
    "Tuesday":   0,
    "Wednesday": 1,
    "Thursday":  2,
    "Friday":    3,
    "Saturday":  4,
    "Sunday":    5
}


class Client(discord.Client):
    def __init__(self):
        intents = discord.Intents().default()
        intents.members = True

        super().__init__(intents=intents)
        self.campaigns = {}

    async def on_ready(self):
        print("Logged on as", self.user)

        self.sync_with_db()
        print("Synced with DB.")

        scheduler.start(self)
        print("Schedular started.")


    def sync_with_db(self):
        for campaign in db.get_campaigns():
            name = campaign[0]

            metadata = campaign[1:]
            chan_id = metadata[0]

            self.campaigns[name] = Campaign(name, chan_id, metadata)


    async def on_message(self, message: discord.Message):
        from_admin = (message.author.id == 447533152567689226)

        if message.author == self.user:  # Make sure Ciel doesn't react to herself
            return

        # ========== Commands ==========
        if message.content == "!ping":
            await message.channel.send("pong")

        if message.content == "!goodnight" and from_admin:
            await message.channel.send("ZZZzzz")
            await self.close()

            return

        if message.content == "!count":
            count = len(message.channel.members)
            await message.channel.send(count)

        if message.content.split(" ")[0] == "!init":
            name = message.channel.name
            chan_id = message.channel.id
            metadata = message.content.split(" ")

            if len(metadata) != 5:
                await message.channel.send("Usage: !init (weekday) (time)(on days) (off days)")

            campaign = Campaign.init(name, chan_id, metadata)
            self.campaigns[name] = campaign

        try:  # Commands for only D&D campaigns
            self.campaigns[message.channel.name]
        except KeyError:
            return

        campaign: Campaign = self.campaigns[message.channel.name]

        if message.content == "!next":  # NOT SENSITIVE TO ON-OFF WEEKS
            session_time = campaign.next_session().strftime("%A, %B %d at %I:%M%p")
            await message.channel.send(session_time)

        if message.content == "!link":
            await message.channel.send("https://api.vorona.gg/join")

        if message.content == "!reset_skips" and from_admin:
            campaign.reset_skips()
            await message.channel.send("Next session will be on {}".format(
                campaign.next_session().strftime("%A, %B %d at %I:%M%p")
            ))

        if message.content == "!rsvp" and from_admin:
            channel = self.get_channel(int(campaign.chan_id))
            await campaign.send_rsvp(channel)

        if message.content == "!cancel" and from_admin:
            db.cancel(message.channel.name)

            await message.channel.send("{}\n{} {}".format(
                "Sorry, the next D&D session has been cancelled.",
                "Next session will be on",
                campaign.next_session().strftime("%A, %B %d at %I:%M%p")))


    # Check if everyone reacts to the RSVP message
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        msg = reaction.message

        if msg.author == self.user and msg.content[0:9] == "Scheduler":
            if reaction.count == (len(msg.channel.members) - 2) and reaction.emoji == "👍":
                await msg.channel.send("Thank you, see you soon!")

            if reaction.emoji == "👎":
                raw_users = await reaction.users().flatten()
                users = ", ".join([user.name for user in raw_users])

                dm = "Sorry, {} in {} can't make it.".format(users, msg.channel.name)
                user = await self.fetch_user(447533152567689226)
                await user.send(dm)


class Campaign:
    @classmethod
    def init(cls, name, chan_id, metadata):
        self = Campaign(name, chan_id, metadata)
        self.update_db()

        return self


    def __init__(self, name, chan_id, metadata):
        self.name      = name
        self.chan_id   = chan_id
        self.weekday   = metadata[1]
        self.time      = metadata[2]
        self.on_weeks  = int(metadata[3]) + 1
        self.off_weeks = int(metadata[4]) + 1


    def update_db(self):
        db.full_update(
            self.name,
            self.chan_id,
            self.weekday,
            self.time,
            self.on_weeks,
            self.off_weeks)


    def reset_skips(self):
        db.reset_off_weeks(self.name)


    async def send_rsvp(self, channel):
        if self.is_correct_time():
            await channel.send("{}\n{}\n{}".format(
                "Scheduler:  React :thumbsup: if you can make it, :thumbsdown: if you can't",
                "RSVP by 4 PM tomorrow, please and thank you",
                "@everyone"))


    # Check if it's 8 PM UTC the day before the session
    def is_correct_time(self):
        current_day = datetime.date.today().weekday()
        current_time = datetime.datetime.now().time()

        # Debugging function
        if self.weekday == "Test":
            return True

        if current_day != weekdays[self.weekday]:
            return False
        elif current_time.hour != 20:
            return False
        elif current_time.minute != 0:
            return False

        return True


    def next_session(self):
        now = datetime.datetime.now()

        if self.weekday == "Test":
            return now

        wkday = weekdays[self.weekday] + 1

        # Change Date
        delta = datetime.timedelta((wkday - now.weekday()) % 7)
        session = now + delta

        # Change Time
        session = session.replace(hour=self.time.strip("PM").split(":")[0])
        session = session.replace(minute=self.time.strip("PM").split(":")[1])
        session = session.replace(second=0)
        session = session.replace(microsecond=0)

        return session


# Check if any campaigns are in need of a scheduling notification
@tasks.loop(seconds=60)
async def scheduler(client: Client):
    for campaign in client.campaigns.values():
        if db.is_on_week(campaign.name):
            channel = client.get_channel(int(campaign.chan_id))
            await campaign.send_rsvp(channel)


# Start Ciel up
token = os.getenv("DISCORD_TOK")
Client().run(token)
