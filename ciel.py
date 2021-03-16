import discord
from discord.ext import tasks

import datetime, asyncio, os

alive = True

weekdays = {
    "Monday":    0,
    "Tuesday":   1,
    "Wednesday": 2,
    "Thursday":  3,
    "Friday":    4,
    "Saturday":  5,
    "Sunday":    6
}


class Client(discord.Client):
    def __init__(self):
        super().__init__()
        self.campaigns = {}

    async def on_ready(self):
        print("Logged on as", self.user)

        update_campaigns.start(self)
        scheduler.start(self)

    
    def update_campaigns(self):
        self.campaigns = {}

        for channel in self.get_guild(593863078488178688).channels:
            try:
                metadata = channel.topic.split("\n")
                campaign_flag = metadata[-1]
    
                if campaign_flag[0:8] == "Campaign":
                    self.campaigns[channel.name] = Campaign(channel, metadata)

            except AttributeError:
                continue


    async def on_message(self, message: discord.Message):
        from_admin = (message.author.id == 447533152567689226)
        
        if message.author == self.user:  # Make sure Ciel doesn't react to herself
            return

        if message.content == "!ping":
            await message.channel.send("pong")

        if message.content == "!goodnight" and from_admin:
            await message.channel.send("ZZZzzz")
            await self.close()

            global alive
            alive = False
            return

        try:  # Commands for only D&D campaigns
            self.campaigns[message.channel.name]
        except KeyError:
            return
        
        if message.content == "!time":
            chan_name = message.channel.name
            dnd_time = self.campaigns[chan_name].datetime
            await message.channel.send(dnd_time)

        if message.content == "!link":
            chan_name = message.channel.name
            link = self.campaigns[chan_name].link
            await message.channel.send(link)

        if message.content == "!cancel" and from_admin:
            await message.channel.send("Sorry, D&D has been cancelled for this week.")


    # Check if everyone reacts to the RSVP message
    async def on_reaction_add(self, reaction: discord.Reaction ,user: discord.Member):
        msg = reaction.message

        if msg.author == self.user and msg.content[0:9] == "Scheduler":
            print(len(msg.channel.members))
            print(reaction.emoji)
            print(reaction.count)

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

        self.name     = metadata[0]
        self.datetime = metadata[1]
        self.weekday  = metadata[1].split(" ")[0]
        self.link     = metadata[2]


    async def check_rsvp(self):    
        if self.is_correct_time():
            await self.channel.send(
                "Scheduler:  :thumbsup: if you can make it, :thumbsdown: if you can't\n",
                "RSVP by 4 PM, please and thank you\n",
                "@everyone")

    # Check if it's 8 AM the day of the session
    def is_correct_time(self):
        current_day = datetime.date.today().weekday()
        current_time = datetime.datetime.now().time()

        # Debugging function
        if self.weekday == "Test":
            return True

        if current_day != (weekdays[self.weekday] - 1) % 7:
            return
        elif current_time.hour != 20:
            return
        elif current_time.minute != 0:
            return
        
        return True


# Check if any campaigns are in need of a scheduling notification
@tasks.loop(seconds=60)
async def scheduler(client: Client):
    for campaign in client.campaigns.values():
        await campaign.check_rsvp()


# Update the campaigns list every hour
@tasks.loop(seconds=3600)
async def update_campaigns(client: Client):
    client.update_campaigns()

    if len(client.campaigns) > 0:
        print("\nCampaign List:")
        
        for campaign in client.campaigns:
            print("\t", campaign)


# Start Ciel up
token = os.getenv("DISCORD_TOK")
Client().run(token)
