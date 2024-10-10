import nextcord, datetime, time, json, os, random
from nextcord.ext import commands, tasks
#autoNutes Cog
class autoNUTES(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.cycleApproved = False
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
            # Return if it has not been four days yet - As well, we check if two days have elapsed or
            # that this "cycle" of members has been approved
            if timems - self.lastSwitch.get('last') < 345600000 and (timems - self.lastSwitch.get('last') < 172800000 or self.cycleApproved):
                return
            # If it has two days, and this cycle has not been approved yet, we'll check if the selected members
            # have been active enough
            if timems - self.lastSwitch.get('last') > 172800000 and timems - self.lastSwitch.get('last') < 345600000:
                await self.checkMemberActivity(nutesmembers)
                if self.cycleApproved: return
            for member in nutesmembers:
                await member.remove_roles(role)
                members.remove(member)
        
        await self.selectNewMembers(members, role, server)

    # Only one of the members needs to have been active for the cycle to be approved
    # That means four posts between the two of them within the last 48 hours in NUTES
    async def checkMemberActivity(self, nutesmembers):
        postCount = 0
        channel = await self.client.fetch_channel(1262971002703446046)

        # Messages since 48 hours ago, this number is lower as it's measured in seconds rather than milliseconds
        async for msg in channel.history(after=datetime.datetime.fromtimestamp(time.time() - 172800)):
            for member in nutesmembers:
                if msg.author.id == member.id: postCount += 1

        # If the designated posters have posted more than 4 times collectively in the last 48 hours,
        # they get to keep their roles
        if postCount > 3:
            self.cycleApproved = True

    async def selectNewMembers(self, members, role, server):
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
        self.cycleApproved = False
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
