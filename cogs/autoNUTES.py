import nextcord, datetime, time, json, os, random
from nextcord.ext import commands, tasks
#gifFilter Cog
class autoNUTES(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.guild_id = 1262968696956256286
        self.lastSwitch = {'last' : None}
        self.alertMsg = "Congratulations, you have been selected as one of the next two people to have unfettered access to NUTES for two weeks! \n \nHave fun shitposting!"

    @commands.Cog.listener()
    async def on_ready(self):
        #Read the pre-existing activity JSON
        self.lastSwitch = self.loadJson()
        await self.nutesAssignment.start()

    # Checking every hour
    @tasks.loop(hours=1)
    async def nutesAssignment(self):
        server = await self.client.fetch_guild(self.guild_id)
        members = server.members
        role = nextcord.utils.get(server.roles, name='NUTES')
        nutesmembers = []
        for member in server.members:
            if 'NUTES' in member.roles:
                nutesmembers.append(member)
        if self.lastSwitch['last'] == None:
            print("No NUTES data found, assuming this is first launch of system.")
        elif len(nutesmembers) == 0:
            print("No members with the NUTES role found, assuming reset or first launch of system.")
        else:
            ms = datetime.datetime.now()
            timems = (time.mktime(ms.timetuple()) * 1000)
            if timems - self.lastSwitch['last'] < 1209600000:
                return
            for member in nutesmembers:
                await member.remove_roles(role)
        choice1 = members.pop(random.randrange(0, len(members)))
        choice2 = members.pop(random.randrange(0, len(members)))
        await choice1.add_roles(role)
        await choice2.add_roles(role)
        await choice1.send(self.alertMsg)
        await choice2.send(self.alertMsg)
        self.saveJson()

        pickle = server.get_member(397573639785938945)
        pickle.send(f"The current NUTES-assigned people are: {choice1.mention} and {choice2.mention}.")
    
    def loadJson(self):
        if os.path.exists('nutes.json'):
            with open('nutes.json') as json_file:
                return json.load(json_file)
    def saveJson(self):
        with open('nutes.json', 'w') as f:
            json.dump(self.lastSwitch, f)

def setup(client):
    client.add_cog(autoNUTES(client))
