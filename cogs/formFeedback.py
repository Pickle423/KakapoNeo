import nextcord, requests, time, os, json
from nextcord.ext import commands
from nextcord.ui import Button, View

#formFeedback Cog
class FormFeedBack(commands.Cog):
    
    def __init__(self, client):
        self.client = client

    feedBackDataBase = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.autoSlot = self.client.get_cog("autoSlot")

        if os.path.exists('feedBack.json'):
            with open('feedBack.json', 'r') as json_file:
                self.feedBackDatabase = json.load(json_file)

    #@nextcord.slash_command(name="form")
    #async def form(self, interaction, operationid=None):
        #await interaction.response.send_modal(FeedbackModal(operationId))

    @nextcord.slash_command(name='fixform',description="Reset a channel's form submission.")
    @commands.has_permissions(administrator=True)
    async def setMessage(self, ctx, message_id: str):
        message = await ctx.channel.fetch_message(int(message_id))

        #Create the button to spawn the form.
        view = View(timeout=None)
        async def formButtonBackend(interaction):
            await self.serveForm(interaction, self.autoSlot.findOperationByName(interaction.channel.name.removesuffix(" Feedback")))
        formButton = Button(label="Feedback", style=nextcord.ButtonStyle.success)
        formButton.callback = formButtonBackend

        #async def compButtonBackend(interaction):
            #await self.serveCompForm(interaction, self.autoSlot.findOperationByName(interaction.channel.name.removesuffix(" Feedback")))
        #compButton = Button(label="Concern", style=nextcord.ButtonStyle.danger)
        #compButton.callback = compButtonBackend
        view.add_item(formButton)
        #view.add_item(compButton)

        await message.edit(view = view)
        return await ctx.response.send_message("Form fixed!", ephemeral=True)
    
    def saveDataBase(self):
        # Dumps data to autoSlot.json
        with open('feedBack.json', 'w') as f:
            json.dump(self.feedBackDataBase, f)
    
    async def listOfOperatives(self, operationId, ctx):
        operativesR = []
        for op in self.feedBackDataBase.get(operationId):
            operativesR.append(ctx.guild.get_member(op))
        return operativesR
    
    async def deleteOp(self, operationId):
        try:
            FormFeedBack.feedBackDataBase.pop(operationId)
        except:
            print("Error removing operation in formFeedBack encountered.")
        self.saveDataBase

    async def serveForm(self, interaction, operationId):
        if operationId == None:
            await interaction.response.send_message("Operation not found, submissions have most likely closed.", delete_after=10)
            return
        await interaction.response.send_modal(FeedbackModal(operationId, self.autoSlot))
    '''
    async def serveCompForm(self, interaction, operationId):
        if operationId == None:
            await interaction.user.send("Operation not found, submissions have most likely closed. \nPlease contact an admin directly about your concern.")
            return
        await interaction.response.send_modal(ComplianceModal(self.client, operationId, self.autoSlot))
    '''

class FeedbackModal(nextcord.ui.Modal):
    def __init__(self, operationId=None, autoSlot=None):
        super().__init__(
            "Operation Feedback",
        )

        self.operationId = operationId
        
        self.autoSlot = autoSlot

        self.webHook = "None"

        # Currently select options are not supported in modals.
        #self.emEnjRating = nextcord.ui.StringSelect(placeholder = "Your overall enjoyment rating", min_values=1, max_values=1)
        #for i in range(1, 11):
        #    self.emEnjRating.add_option(label=i, value=i)
        self.emEnjRating =  nextcord.ui.TextInput(label = "Your overall enjoyment Rating", min_length=1, max_length=3, required=True, placeholder="Enter your rating from 1-10 here!")
        self.emEnjFeedback = nextcord.ui.TextInput(label = "Your overall enjoyment feedback", style=nextcord.TextInputStyle.paragraph, min_length=1, max_length=1024, required=False, placeholder="How did you generally enjoy the operation?")
        self.emDesignRating =  nextcord.ui.TextInput(label = "Your operation design Rating", min_length=1, max_length=3, required=False, placeholder="Enter your rating from 1-10 here!")
        self.emDesignFeedback = nextcord.ui.TextInput(label = "Your operation design feedback", style=nextcord.TextInputStyle.paragraph, min_length=1, max_length=1024, required=False, placeholder="What do you think of the operation's design?")
        self.emLeadershipFeedback = nextcord.ui.TextInput(label = "Your leadership feedback", style=nextcord.TextInputStyle.paragraph, min_length=1, max_length=1024, required=False, placeholder="What do you think of the leadership?")
       
        self.add_item(self.emEnjRating)
        self.add_item(self.emEnjFeedback)
        self.add_item(self.emDesignRating)
        self.add_item(self.emDesignFeedback)
        self.add_item(self.emLeadershipFeedback)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        await interaction.response.defer()

        em = nextcord.Embed(title=str(interaction.channel.name.removesuffix(" Feedback")), description=f"Feedback submitted for {interaction.channel.name.removesuffix(' Feedback')}!")
        em.set_author(name=str(interaction.user).removesuffix('#0'), icon_url=interaction.user.avatar)

        host = interaction.guild.get_member(self.autoSlot.database['operations'][self.operationId]['author']).name

        payload = {"operation date" : self.autoSlot.database['operations'][self.operationId]['operation_timestamp'], "submission date" : time.time(), 
                "operation name" : interaction.channel.name.removesuffix(" Feedback"),
                "host" : host, "author" : interaction.user.name,
                "enjoyment rating" : self.emEnjRating.value, "enjoyment feedback" : self.emEnjFeedback.value, "design rating" : self.emDesignRating.value, 
                "design feedback" : self.emDesignFeedback.value, "leadership feedback" : self.emLeadershipFeedback.value}

        # DO NOT POST TO OLD SPREADSHEET, ACQUIRE NEW SPREADSHEET
        #response = requests.request("POST", self.webHook, data=payload)

        operativeList = FormFeedBack.feedBackDataBase.get(self.operationId)

        # I hate doing nested if statements but doing this with boolean algebra isn't as easy as this.
        if operativeList:
            if not interaction.user.id in operativeList:
                FormFeedBack.feedBackDataBase[self.operationId].append(interaction.user.id)
        else:
            FormFeedBack.feedBackDataBase.update({self.operationId : [interaction.user.id]})

        
        FormFeedBack.saveDataBase

        return await interaction.followup.send(embed=em)

        '''
        em = nextcord.Embed(title=f"{str(interaction.user).removesuffix('#0')}\'s feedback", description="Operation Name")
        em.add_field(name=f"Overall Enjoyment: {self.emEnjRating.value}/10", value=self.emEnjFeedback.value)
        if self.emDesignRating.value != "" or self.emDesignFeedback.value != "":
            em.add_field(name=f"Operation Design: {self.emDesignRating.value}/10", value=self.emDesignFeedback.value, inline=False)
        if self.emLeadershipFeedback.value != "":
            em.add_field(name="Leadership:", value=self.emLeadershipFeedback.value, inline=False)
        return await interaction.response.send_message(embed=em)
        '''
# No need for a compliance modal at the moment.
'''
class ComplianceModal(nextcord.ui.Modal):
    def __init__(self, client, operationId=None, autoSlot=None):
        super().__init__(
            "Compliance Concern",
        )
        self.client = client

        self.operationId = operationId
        
        self.autoSlot = autoSlot

        # Currently the sample sheet webhook
        self.webHook = "None"

        # Currently select options are not supported in modals.
        #self.emEnjRating = nextcord.ui.StringSelect(placeholder = "Your overall enjoyment rating", min_values=1, max_values=1)
        #for i in range(1, 11):
        #    self.emEnjRating.add_option(label=i, value=i)
        self.emSituation =  nextcord.ui.TextInput(label = "Situation", style=nextcord.TextInputStyle.paragraph, min_length=1, max_length=1024, required=True, placeholder="What happened that caused this compliance concern?")
        self.emWitnesses = nextcord.ui.TextInput(label = "Witnesses", style=nextcord.TextInputStyle.paragraph, min_length=1, max_length=1024, required=True, placeholder="Who can attest to witnessing this situation? Mention even those you mentioned previously.")
        self.emAddNotes = nextcord.ui.TextInput(label = "Additional Notes", style=nextcord.TextInputStyle.paragraph, min_length=1, max_length=1024, required=True, placeholder="Any other notes you would like to mention?")
        self.add_item(self.emSituation)
        self.add_item(self.emWitnesses)
        self.add_item(self.emAddNotes)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        notifChannel = nextcord.utils.get(self.client.get_all_channels(), name=f"cxo-notifications")

        em = nextcord.Embed(title=str(interaction.channel.name.removesuffix(" Feedback")), description=f"Thank you for submitting your Compliance Concern. Your submission will be reviewed by the CHRO, and they will reach out to you soon. Below is a copy of your submission:")
        em.add_field(name="Situation:", value=self.emSituation.value)
        em.add_field(name="Witnesses:", value=self.emWitnesses.value)
        em.add_field(name="Additional Notes:", value=self.emAddNotes.value)
        em.set_author(name=str(interaction.user).removesuffix('#0'))

        host = interaction.guild.get_member(self.autoSlot.database['operations'][self.operationId]['author']).name

        payload = {"operation date" : self.autoSlot.database['operations'][self.operationId]['operation_timestamp'], "submission date" : time.time(), 
                "operation name" : interaction.channel.name.removesuffix(" Feedback"),
                "host" : host, "author" : interaction.user.name,
                "situation" : self.emSituation.value, "witnesses" : self.emWitnesses.value, "notes" : self.emAddNotes.value}

        response = requests.request("POST", self.webHook, data=payload)

        await interaction.user.send(embed=em)

        notifEm = nextcord.Embed(title=str(interaction.channel.name.removesuffix(" Feedback")), description=f"Compliance Concern submitted for {str(interaction.channel.name.removesuffix(' Feedback'))}.")
        
        await notifChannel.send(embed=notifEm)

        return await interaction.followup.send("Concern submitted", delete_after=5, ephemeral=True)
'''

def setup(client):
    client.add_cog(FormFeedBack(client))