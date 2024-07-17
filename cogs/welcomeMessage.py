import nextcord
from nextcord.ext import commands

#welcomeMessage Cog
class WelcomeMessage(commands.Cog):
    
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        global welcomemessagechannel
        channel = nextcord.utils.get(member.guild.text_channels, name="lobby")
        server = member.guild
        await channel.send(f"Yo. {member.mention}")

def setup(client):
    client.add_cog(WelcomeMessage(client))