import nextcord, datetime, time
from nextcord.ext import commands
#gifFilter Cog
class gifFilter(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.quarantined = {}
        self.spamEvents = {}

    # Called everytime a message happens
    @commands.Cog.listener()
    async def on_message(self, message):
        await self.expireAudit()

        exception_channels = [nextcord.utils.get(message.guild.text_channels, name="voice-chat"),nextcord.utils.get(message.guild.text_channels, name="nsfw-memes-no-porn"),nextcord.utils.get(message.guild.text_channels, name="bot-commands")]

        if message.channel.id in self.quarantined.keys() and message.channel not in exception_channels:
            await self.filterChannel(message)

        if message.channel not in exception_channels:
            await self.audit(message)

    # Check if this channel is being spammed, if it is then append it to the dictionary of quarantined channels.
    async def audit(self, message):
        not_allow = message.content
        currentTime = self.unixTime()
        if "https://tenor.com" in not_allow or "https://media.tenor.co" in not_allow or "https://c.tenor.com" in not_allow:
            self.spamEvents[currentTime] = message.channel.id

        eventCount = 0

        for event in self.spamEvents.keys().copy():
            # Clean up spamEvents, so we don't have a list that gets ever larger
            if (currentTime - event) > 30000:
                self.spamEvents.pop(event, None)
                continue
            if (self.spamEvents.get(event) == message.channel.id) and (currentTime - event) <= 30000:
                eventCount = eventCount + 1
        
        if eventCount > 10:
            self.quarantined[message.channel.id] = currentTime
    
    # See if any channels have exceeded an hour since the filter went into effect.
    async def expireAudit(self):
        for channel in self.quarantined.keys():
            if (self.unixTime() - self.quarantined.get(channel)) > 3600000:
                self.quarantined.pop(channel)

    # Actual filtering of the channel.
    async def filterChannel(self, message):
        try:
            not_allow = message.content
            if "https://tenor.com" in not_allow or "https://media.tenor.co" in not_allow or "https://c.tenor.com" in not_allow:
                await message.delete()
        except:
            pass

    def unixTime(self):
        return (time.mktime(datetime.datetime.now().timetuple()) * 1000)

def setup(client):
    client.add_cog(gifFilter(client))
