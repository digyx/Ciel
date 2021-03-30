import discord
from discord.ext import tasks

import datetime, os

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

        update_campaigns.start(self)
        print("Campaign updater started.")

        scheduler.start(self)
        print("Schedular started.")


    async def update_campaigns(self):
        self.campaigns = {}

        for channel in self.get_guild(593863078488178688).channels:
            try:
                metadata = channel.topic.split("\n")
                campaign_flag = metadata[-1]

                if campaign_flag[0:8] == "Campaign":
                    self.campaigns[channel.name] = await Campaign.init(channel, metadata)

            except AttributeError:
                continue


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
            chan_id = message.channel.id
            count = len(self.get_channel(chan_id).members)
            await message.channel.send(count)

        try:  # Commands for only D&D campaigns
            self.campaigns[message.channel.name]
        except KeyError:
            return

        campaign = self.campaigns[message.channel.name]

        if message.content == "!next":
            session_time = campaign.next.strftime("%A, %B %d at %I:%M%p")
            await message.channel.send(session_time)

        if message.content == "!link":
            link = campaign.link
            await message.channel.send(link)

        if message.content == "!reset_date":
            await campaign.calculate_next_session()
            await message.channel.send("Next session will be on {}".format(
                campaign.next.strftime("%A, %B %d at %I:%M%p")
            ))

        if message.content == "!cancel" and from_admin:
            session = campaign.next + datetime.timedelta(7)
            await campaign.update_next_session(session)
            await message.channel.send("{}\n{}{}".format(
                "Sorry, the next D&D session has been cancelled.",
                "Next session will be on",
                campaign.next.strftime("%A, %B %d at %I:%M%p")))


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
    async def init(cls, channel, metadata):
        self = Campaign(channel, metadata)

        try:
            self.next = datetime.datetime.strptime(
                self.metadata[3], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            await self.calculate_next_session()

        return self


    def __init__(self, channel, metadata):
        self.channel = channel
        self.metadata = metadata

        self.name     = metadata[0]
        self.weekday  = metadata[1].split(" ")[0]
        self.link     = metadata[2]

        campaign_time = metadata[1].split(" ")[2]
        self.hour     = int(campaign_time.split(":")[0])
        self.minute   = int(campaign_time.split(":")[1])

        self.next     = datetime.datetime.now()


    async def check_rsvp(self):
        if self.is_correct_time():
            await self.channel.send("{}\n{}\n{}".format(
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

    async def calculate_next_session(self):
        now = datetime.datetime.now()
        wkday = weekdays[self.weekday] + 1

        # Change Date
        delta = datetime.timedelta((wkday - now.weekday()) % 7)
        session = now + delta

        # Change Time
        session = session.replace(hour=self.hour)
        session = session.replace(minute=self.minute)
        session = session.replace(second=0)
        session = session.replace(microsecond=0)

        await self.update_next_session(session)

    async def update_next_session(self, session):
        self.next = session
        self.metadata[3] = str(self.next)
        await self.channel.edit(topic="\n".join(self.metadata))


# Check if any campaigns are in need of a scheduling notification
@tasks.loop(seconds=60)
async def scheduler(client: Client):
    for campaign in client.campaigns.values():
        await campaign.check_rsvp()


# Update the campaigns list every hour
@tasks.loop(seconds=3600)
async def update_campaigns(client: Client):
    await client.update_campaigns()

    if len(client.campaigns) > 0:
        print("\nCampaign List:")

        for campaign in client.campaigns:
            print("\t", campaign)


# Start Ciel up
token = os.getenv("DISCORD_TOK")
Client().run(token)
