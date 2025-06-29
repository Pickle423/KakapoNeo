# type: ignore
"""
This cog was largely copied from the Pomice library's github page and modified to Kakapo/Statera standards by Pickle423.
Credit for the original cog goes to the maintainer(s) of Pomice.
"""
import math
from contextlib import suppress

import nextcord
from nextcord.ext import commands

import pomice


class Player(pomice.Player):
    """Custom pomice Player class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.queue = pomice.Queue()
        self.controller: nextcord.Message = None
        # Set context here so we can send a now playing embed
        self.context: commands.Context = None
        self.dj: nextcord.Member = None

        self.pause_votes = set()
        self.resume_votes = set()
        self.skip_votes = set()
        self.shuffle_votes = set()
        self.stop_votes = set()

    async def do_next(self) -> None:
        # Clear the votes for a new song
        self.pause_votes.clear()
        self.resume_votes.clear()
        self.skip_votes.clear()
        self.shuffle_votes.clear()
        self.stop_votes.clear()

        # Check if theres a controller still active and deletes it
        if self.controller:
            with suppress(nextcord.HTTPException):
                await self.controller.delete()

        # Queue up the next track, else teardown the player
        try:
            track: pomice.Track = self.queue.get()
        except pomice.QueueEmpty:
            return await self.teardown()

        await self.play(track)

        # Call the controller (a.k.a: The "Now Playing" embed) and check if one exists

        if track.is_stream:
            embed = nextcord.Embed(
                title="Now playing",
                description=f":red_circle: **LIVE** [{track.title}]({track.uri}) [{track.requester.mention}]",
            )
            self.controller = await self.context.send(embed=embed)
        else:
            embed = nextcord.Embed(
                title=f"Now playing",
                description=f"[{track.title}]({track.uri}) [{track.requester.mention}]",
            )
            self.controller = await self.context.send(embed=embed)

    async def teardown(self):
        """Clear internal states, remove player controller and disconnect."""
        with suppress((nextcord.HTTPException), (KeyError)):
            await self.destroy()
            if self.controller:
                await self.controller.delete()

    async def set_context(self, ctx):
        """Set context for the player"""
        self.context = ctx
        self.dj = ctx.user


class Music(commands.Cog):
    def __init__(self, client) -> None:
        self.client = client

        # In order to initialize a node, or really do anything in this library,
        # you need to make a node pool
        self.pomice = pomice.NodePool()

        # Start the node
        client.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        # Waiting for the client to get ready before connecting to nodes.
        await self.client.wait_until_ready()

        # You can pass in Spotify credentials to enable Spotify querying.
        # If you do not pass in valid Spotify credentials, Spotify querying will not work
        await self.pomice.create_node(
            bot=self.client,
            host="127.0.0.1",
            port=2333,
            password="yoyoyo, it's me! mario!",
            identifier="MAIN",
        )
        print(f"Node is ready!")

    def required(self, ctx):
        """Method which returns required votes based on amount of members in a channel."""
        player: Player = ctx.guild.voice_client
        channel = self.client.get_channel(int(player.channel.id))
        required = math.ceil((len(channel.members) - 1) / 2.5)

        if ctx.command.name == "stop":
            if len(channel.members) == 3:
                required = 2

        return required

    def is_privileged(self, ctx):
        """Check whether the user is an Admin or DJ."""
        player: Player = ctx.guild.voice_client

        return player.dj == ctx.user or ctx.user.guild_permissions.kick_members

    # The following are events from pomice.events
    # We are using these so that if the track either stops or errors,
    # we can just skip to the next track

    # Of course, you can modify this to do whatever you like

    @commands.Cog.listener()
    async def on_pomice_track_end(self, player: Player, track, _):
        await player.do_next()

    @commands.Cog.listener()
    async def on_pomice_track_stuck(self, player: Player, track, _):
        await player.do_next()

    @commands.Cog.listener()
    async def on_pomice_track_exception(self, player: Player, track, _):
        await player.do_next()

    @nextcord.slash_command(name='join',description="Join a voice channel")
    async def join(self, ctx, channel: nextcord.VoiceChannel = None) -> None:
        if not channel:
            channel = getattr(ctx.user.voice, "channel", None)
            if not channel:
                return await ctx.response.send_message(
                    "You must be in a voice channel in order to use this command!",
                )
        await ctx.response.defer()
        # custom voice protocol (Player class) is passed to nextcord as the player context.
        await ctx.user.voice.channel.connect(cls=Player)
        player: Player = ctx.guild.voice_client

        # Set the player context so we can use it so send messages
        await player.set_context(ctx=ctx)
        await ctx.followup.send(f"Joined the voice channel `{channel.name}`")

    @nextcord.slash_command(name='leave',description="Leave a voice channel")
    async def leave(self, ctx):
        if not (player := ctx.guild.voice_client):
            return await ctx.response.send_message(
                "You must have the client in a channel in order to use this command",
                delete_after=7,
            )

        await player.destroy()
        await ctx.response.send("Player has left the channel.")

    @nextcord.slash_command(name='play',description="Play a song")
    async def play(self, ctx, search: str = None) -> None:
        await ctx.response.defer()
        # Checks if the player is in the channel before we play anything
        if not (player := ctx.guild.voice_client):
            await ctx.user.voice.channel.connect(cls=Player)
            player: Player = ctx.guild.voice_client
            await player.set_context(ctx=ctx)

        # If you search a keyword, Lavalink will automatically search the result using YouTube
        # You can pass in "search_type=" as an argument to change the search type
        # i.e: player.get_tracks("query", search_type=SearchType.ytmsearch)
        # will search up any keyword results on YouTube Music

        # This is silly, but Pomice expects a traditional command context so our slash command context won't work.
        # Upon further examination of the library, the only actual reference to that context is for the author, so we instantiate a custom class with the author.
        class TrackRQ:
            def __init__(self, author):
                self.author = author
        results = await player.get_tracks(search, ctx=TrackRQ(ctx.user))

        if not results:
            return await ctx.followup.send("No results were found for that search term", delete_after=7)

        if isinstance(results, pomice.Playlist):
            for track in results.tracks:
                player.queue.put(track)
            await ctx.followup.send(f'**Added playlist to queue**', ephemeral=False)
        else:
            track = results[0]
            player.queue.put(track)
            await ctx.followup.send(f'**Added to Queue:** `{track.title}`', ephemeral=False)

        if not player.is_playing:
            await player.do_next()

    @nextcord.slash_command(name='pause',description="Pause the current music")
    async def pause(self, ctx):
        """Pause the currently playing song."""
        if not (player := ctx.guild.voice_client):
            return await ctx.response.send_message(
                "You must have the client in a channel in order to use this command",
                delete_after=7,
            )

        if player.is_paused or not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.response.send_message("An admin or DJ has paused the player.", delete_after=10)
            player.pause_votes.clear()

            return await player.set_pause(True)

        required = self.required(ctx)
        player.pause_votes.add(ctx.user)

        if len(player.pause_votes) >= required:
            await ctx.response.end_message("Vote to pause passed. Pausing player.", delete_after=10)
            player.pause_votes.clear()
            await player.set_pause(True)
        else:
            await ctx.response.send_message(
                f"{ctx.user.mention} has voted to pause the player. Votes: {len(player.pause_votes)}/{required}",
                delete_after=15,
            )

    @nextcord.slash_command(name='resume',description="Resume the current song")
    async def resume(self, ctx):
        """Resume a currently paused player."""
        if not (player := ctx.guild.voice_client):
            return await ctx.response.send_message(
                "You must have the client in a channel in order to use this command",
                delete_after=7,
            )

        if not player.is_paused or not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.response.send_message("An admin or DJ has resumed the player.", delete_after=10)
            player.resume_votes.clear()

            return await player.set_pause(False)

        required = self.required(ctx)
        player.resume_votes.add(ctx.user)

        if len(player.resume_votes) >= required:
            await ctx.response.send_message("Vote to resume passed. Resuming player.", delete_after=10)
            player.resume_votes.clear()
            await player.set_pause(False)
        else:
            await ctx.response.send_message(
                f"{ctx.user.mention} has voted to resume the player. Votes: {len(player.resume_votes)}/{required}",
                delete_after=15,
            )

    @nextcord.slash_command(name='skip',description="Skip to the next song")
    async def skip(self, ctx):
        """Skip the currently playing song."""
        if not (player := ctx.guild.voice_client):
            return await ctx.response.send_message(
                "You must have the client in a channel in order to use this command",
                delete_after=7,
            )

        if not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.response.send_message("An admin or DJ has skipped the song.", delete_after=10)
            player.skip_votes.clear()

            return await player.stop()

        if ctx.user == player.current.requester:
            await ctx.response.send_message("The song requester has skipped the song.", delete_after=10)
            player.skip_votes.clear()

            return await player.stop()

        required = self.required(ctx)
        player.skip_votes.add(ctx.user)

        if len(player.skip_votes) >= required:
            await ctx.response.send_message("Vote to skip passed. Skipping song.", delete_after=10)
            player.skip_votes.clear()
            await player.stop()
        else:
            await ctx.response.send_message(
                f"{ctx.user.mention} has voted to skip the song. Votes: {len(player.skip_votes)}/{required} ",
                delete_after=15,
            )

    @nextcord.slash_command(name='stop',description="Stop the player and clear queue")
    async def stop(self, ctx):
        """Stop the player and clear all internal states."""
        if not (player := ctx.guild.voice_client):
            return await ctx.response.send_message(
                "You must have the client in a channel in order to use this command",
                delete_after=7,
            )

        if not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.response.send_message("An admin or DJ has stopped the player.", delete_after=10)
            return await player.teardown()

        required = self.required(ctx)
        player.stop_votes.add(ctx.user)

        if len(player.stop_votes) >= required:
            await ctx.response.send_message("Vote to stop passed. Stopping the player.", delete_after=10)
            await player.teardown()
        else:
            await ctx.response.send_message(
                f"{ctx.user.mention} has voted to stop the player. Votes: {len(player.stop_votes)}/{required}",
                delete_after=15,
            )

    @nextcord.slash_command(name='shuffle',description="Shuffle the queue")
    async def shuffle(self, ctx):
        """Shuffle the players queue."""
        if not (player := ctx.guild.voice_client):
            return await ctx.response.send_message(
                "You must have the client in a channel in order to use this command",
                delete_after=7,
            )

        if not player.is_connected:
            return

        if player.queue.qsize() < 3:
            return await ctx.response.send_message(
                "The queue is empty. Add some songs to shuffle the queue.",
                delete_after=15,
            )

        if self.is_privileged(ctx):
            await ctx.response.send_message("An admin or DJ has shuffled the queue.", delete_after=10)
            player.shuffle_votes.clear()
            return player.queue.shuffle()

        required = self.required(ctx)
        player.shuffle_votes.add(ctx.user)

        if len(player.shuffle_votes) >= required:
            await ctx.response.send_message("Vote to shuffle passed. Shuffling the queue.", delete_after=10)
            player.shuffle_votes.clear()
            player.queue.shuffle()
        else:
            await ctx.response.send_message(
                f"{ctx.user.mention} has voted to shuffle the queue. Votes: {len(player.shuffle_votes)}/{required}",
                delete_after=15,
            )

    @nextcord.slash_command(name='volume',description="Adjust the volume")
    async def volume(self, ctx, vol: int):
        """Change the players volume, between 1 and 100."""
        if not (player := ctx.guild.voice_client):
            return await ctx.response.send_message(
                "You must have the client in a channel in order to use this command",
                delete_after=7,
            )

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.response.send_message("Only the DJ or admins may change the volume.")

        if not 0 < vol < 101:
            return await ctx.response.send_message("Please enter a value between 1 and 100.")

        await player.set_volume(vol)
        await ctx.response.send_message(f"Set the volume to **{vol}**%", delete_after=7)

    @nextcord.slash_command(name='queue',description="Displays the current queue")
    async def queue(self, ctx):
        if not (player := ctx.guild.voice_client):
            return await ctx.response.send_message(
                "You must have the client in a channel in order to use this command",
                delete_after=7,
            )
        '''
        Fix this and implement it later
        if player.queue.is_empty:
            await ctx.response.send_message("Nothing is queued!")
            return
        '''
        await ctx.response.defer()
        queuetitle = []
        queueurl = []
        # Don't ask, I wouldn't do this in an enterprise-level project but this is done in free time
        for track in player.queue.__iter__():
            tracktitle = track.title
            queuetitle.append(tracktitle)
            queueurl.append(track.uri)
        i = 0
        queue = f"0) [{queuetitle[0]}]({queueurl[0]})"
        for song in queuetitle:
            if i > 10:
                queue = (queue + f"\n**Queue has {len(queuetitle) - 10} more tracks in queue.**")
                break
            if i > 0 and i < 11:
                queue = (queue + f"\n{i}) [{song}]({queueurl[i]})")
            i = i + 1
        ListEmbed = nextcord.Embed(title=f"Queue for {ctx.guild.name}", description=queue, color=nextcord.Color.green())
        ListEmbed.set_footer(text="Music Functionality written by Pickle423#0408")
        await ctx.followup.send(embed=ListEmbed)


def setup(client):
    client.add_cog(Music(client))
