import discord
from discord.ext import tasks

import datetime, asyncio
from threading import Timer, Thread


class Client(discord.Client):
    async def on_ready(self):
        print("Logged on as", self.user)
        campaigns = []

        for channel in self.get_guild(593863078488178688).channels:
            try:
                metadata = channel.topic.split("\n")[1]
                if metadata[0:8] != "Campaign":
                    continue
            except:
                continue

            campaigns.append(Campaign(channel, metadata))

        if len(campaigns) > 0:
            scheduler.start(campaigns)


    async def on_message(self, message: discord.Message):
        from_admin = (message.author.id == 447533152567689226)
        
        if message.author == self.user:
            return

        if message.content == "!ping":
            await message.channel.send("pong")

        if message.content == "!goodnight" and from_admin:
            await message.channel.send("ZZZzzz")
            await self.close()

            global alive
            alive = False
            return

        if message.content == "!cancel" and from_admin:
            await message.channel.send("Sorry, D&D has been cancelled for this week.")


    async def on_reaction_add(self, reaction: discord.Reaction ,user: discord.Member):
        msg = reaction.message

        if msg.author == self.user and msg.content[0:9] == "Scheduler":
            if reaction.count == (len(msg.channel.members) - 1) and reaction.emoji == "👍":
                await msg.channel.send("Thank you!  See you soon!")

            if reaction.emoji == "👎":
                raw_users = await reaction.users().flatten()
                users = ", ".join([user.name for user in raw_users])
                
                dm = "Sorry, {} in {} can't make it.".format(users, msg.channel.name)
                user = await self.fetch_user(447533152567689226)
                await user.send(dm)


class Campaign:
    def __init__(self, channel, metadata):
        self.channel = channel

        # Python starts on Monday = 0
        # Discord starts on Sunday = 0
        self.weekday = (int(metadata.split(" ")[1]) - 1) % 7

    async def check_rsvp(self):
        current_day = datetime.date.today().weekday()
        # current_time = datetime.datetime.now().time()
    
        # if current_day == self.weekday and current_time.hour == 16 and current_time.minute == 5:
        if current_day == self.weekday:
            await self.channel.send("Scheduler:  :thumbsup: if you can make it, :thumbsdown: if you can't")


@tasks.loop(seconds=60)
async def scheduler(campaigns: Campaign):
    for campaign in campaigns:
        await campaign.check_rsvp()


alive = True
token = "ODAyNzMzNTczNDk2NjM1NDYz.YAzh5Q.sQzAm7mdyaoOZj-TtgDIpfpLs5s"
Client().run(token)
