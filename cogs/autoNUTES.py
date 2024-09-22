import nextcord, datetime, time, json, os, random
from nextcord.ext import commands, tasks
#autoNutes Cog
class autoNUTES(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.guild_id = 1262968696956256286
        self.lastSwitch = {'last' : None}
        self.alertMsg = "Congratulations, you have been selected as one of the next two people to have unfettered access to NUTES for four days! \n \nHave fun shitposting!"

    @commands.Cog.listener()
    async def on_ready(self):
        #Read the pre-existing activity JSON  
        lastSwitch = self.loadJson()
        if lastSwitch != None:
            self.lastSwitch = lastSwitch
        await self.nutesAssignment.start()

    # Checking every hour
    @tasks.loop(hours=1)
    async def nutesAssignment(self):
        server = self.client.get_guild(self.guild_id)
        members = server.members
        role = nextcord.utils.get(server.roles, name='NUTES')
        nutesmembers = []
        for member in server.members:
            if member.get_role(role.id):
                nutesmembers.append(member)
        if self.lastSwitch.get('last') == None:
            print("No NUTES data found, assuming this is first launch of system.")
        elif len(nutesmembers) == 0:
            print("No members with the NUTES role found, assuming reset or first launch of system.")
        else:
            ms = datetime.datetime.now()
            timems = (time.mktime(ms.timetuple()) * 1000)
            if timems - self.lastSwitch.get('last') < 345600000:
                return
            for member in nutesmembers:
                await member.remove_roles(role)
                members.remove(member)
        # Iterate through a copy of the members list just to make sure we don't get an angry list loop
        for member in members.copy():
            if member.id == 1262971867099168899 or member.id == 337756913469095937 or member.id == 397573639785938945:
                members.remove(member)
        choice1 = members.pop(random.randrange(0, len(members)))
        choice2 = members.pop(random.randrange(0, len(members)))
        await choice1.add_roles(role)
        await choice2.add_roles(role)
        await choice1.send(self.alertMsg)
        await choice2.send(self.alertMsg)
        self.lastSwitch.update({'last' : time.mktime(datetime.datetime.now().timetuple()) * 1000})
        self.saveJson()

        pickle = server.get_member(267469338557153300)
        await pickle.send(f"The current NUTES-assigned people are: {choice1.mention} and {choice2.mention}.")
    
    def loadJson(self):
        if os.path.exists('nutes.json'):
            with open('nutes.json') as json_file:
                return json.load(json_file)
    def saveJson(self):
        with open('nutes.json', 'w') as f:
            json.dump(self.lastSwitch, f)

def setup(client):
    client.add_cog(autoNUTES(client))
