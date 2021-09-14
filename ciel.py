import os

import discord
from discord.ext import tasks

import db
from logger import Logger
from campaign import Campaign


class Client(discord.Client):
    def __init__(self):
        self.logger = Logger("client")
        intents = discord.Intents().default()
        intents.members = True

        super().__init__(intents=intents)

    async def on_ready(self):
        self.logger.info({
            "msg": "Logged on as {}".format(self.user)
        })

        scheduler.start(self)
        self.logger.info({"msg": "Schedular started."})


    async def on_message(self, message: discord.Message):
        from_admin = (message.author.id == 447533152567689226)

        # Make sure Ciel doesn't react to herself
        if message.author == self.user:
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
            name: str     = message.channel.name
            chan_id: int  = message.channel.id
            metadata: str = message.content.split(" ")

            if len(metadata) != 5:
                await message.channel.send("Usage: !init (weekday) (time)(on days) (off days)")

            Campaign.new(name, chan_id, metadata)

        try:  # Commands for only D&D campaigns
          campaign = Campaign(message.channel.name)
        except KeyError:
            return

        if message.content == "!next":
            session_time = campaign.next_session().strftime("%A, %B %d at %I:%M%p")
            await message.channel.send(session_time)

        if message.content == "!link":
            await message.channel.send("https://api.vorona.gg/join")

        if message.content == "!reset_count" and from_admin:
            campaign.reset_off_weeks()
            await message.channel.send("Next session will be on {}".format(
                campaign.next_session().strftime("%A, %B %d at %I:%M%p")
            ))

        if message.content == "!rsvp" and from_admin:
            await self.send_rsvp(campaign.get_chan_id())

        if message.content == "!cancel" and from_admin:
            campaign.cancel()

            await message.channel.send("{}\n{} {}".format(
                "Sorry, the next D&D session has been cancelled.",
                "Next session will be on",
                campaign.next_session().strftime("%A, %B %d at %I:%M%p")))

    async def send_rsvp(self, channel_id: int):
        channel = self.get_channel(int(channel_id))
        await channel.send("{}\n{}\n{}".format(
            "Scheduler:  React :thumbsup: if you can make it, :thumbsdown: if you can't",
            "RSVP by 4 PM tomorrow, please and thank you",
            "@everyone"))



    # Check if everyone reacts to the RSVP message
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        msg = reaction.message

        if msg.author == self.user and msg.content[0:9] == "Scheduler":
            if reaction.count == (len(msg.channel.members) - 3) and reaction.emoji == "👍":
                await msg.channel.send("Thank you, see you soon!")

            if reaction.emoji == "👎":
                raw_users = await reaction.users().flatten()
                users = ", ".join([user.name for user in raw_users])

                dm = "Sorry, {} in {} can't make it.".format(users, msg.channel.name)
                user = await self.fetch_user(447533152567689226)
                await user.send(dm)


# Check if any campaigns are in need of a scheduling notification
@tasks.loop(seconds=60)
async def scheduler(client: Client):
    campaigns = [Campaign(name[0]) for name in db.get_campaigns()]
    for campaign in campaigns:
        if campaign.is_on_week() and campaign.is_correct_time():
            await client.send_rsvp(campaign.get_chan_id())


# Start Ciel up
token = os.getenv("DISCORD_TOK")
Client().run(token)

