import discord
import asyncio
from discord.ext import commands
from discord import app_commands
import yt_dlp
from yt_dlp import YoutubeDL

#TODO: make commands execute per server instead of globally
#TODO: add folder for ffmpeg and path variable

class queueView(discord.ui.View):
    current_page: int = 1
    sep: int = 5

    async def send(self, ctx):
        self.message = await ctx.send(view=self)
        await self.update_message(self.data[:self.sep])
    
    #TODO: fix queue number display somehow
    def create_embed(self,data):
        embed = discord.Embed(title="Queue")
        for index in range(len(data)):
            for key, val in data[index].items():
                embed.add_field(name=f"{index + 1}. {key}", value=val, inline=False)
        return embed
    
    async def update_message(self,data):
        await self.message.edit(embed=self.create_embed(data), view=self)
    
    @discord.ui.button(label="<",
                       style=discord.ButtonStyle.primary)
    async def back_button(self, interaction:discord.Interaction,item):
        await interaction.response.defer()
        self.current_page -= 1
        until_item = self.current_page * self.sep
        from_item = until_item - self.sep
        await self.update_message(self.data[from_item:until_item])
   
    @discord.ui.button(label=">",
                       style=discord.ButtonStyle.primary)
    async def next_button(self, interaction:discord.Interaction,item):
        await interaction.response.defer()
        self.current_page += 1
        until_item = self.current_page * self.sep
        from_item = until_item - self.sep
        await self.update_message(self.data[from_item:until_item])

class music(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

        self.now_playing = ""
        self.music_queue = []

        self.YDL_OPTIONS = {'format' : 'bestaudio/best', 'noplaylist': 'True'}
        self.ytdl = yt_dlp.YoutubeDL(self.YDL_OPTIONS)
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -attempt_recovery true -recover_any_error true'}
        self.vc = None
    
    # async def runAutoplay(self, ctx, on: bool):
    #     while on and self.music_queue:
    #         if


    @commands.hybrid_command(name="play", description="I'll play the video from the url provided")
    async def play(self,ctx: commands.Context, url: str):
        
        
        await ctx.interaction.response.defer(thinking=True)
        try:
            voice = ctx.voice_client

            if(voice == None):
                member = ctx.author
                invoice = await member.fetch_voice()
                channel = invoice.channel
                await channel.connect()

        except Exception:
            await ctx.interaction.response.followup(f"{member}, you're not in a channel!")            
            
        try:
            voice = ctx.voice_client
            if not voice.is_playing:

                loop = asyncio.get_event_loop()

                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=False))

                song = data['url']
                title = data['title']
                player = discord.FFmpegOpusAudio(song, **self.FFMPEG_OPTIONS)

                voice.play(player)
                await ctx.interaction.followup.send(f"Now playing: {title} ")
                self.now_playing = url
            else:
                await self.queue_add(ctx,song)

        except Exception as e:
            print(e)

    @commands.hybrid_command(name="pause", description="I'll pause what's currently playing")
    async def pause(self,ctx: commands.Context):
        voice = ctx.voice_client
        try:

            if(voice.is_playing):
                voice.pause()
                await ctx.send("Ok! Paused.")
            else:
                await ctx.send("I'm not playing anything right now")

        except Exception as e:
            print(e)
    
    @commands.hybrid_command(name="resume", description="I'll resume what's currently playing")
    async def resume(self,ctx: commands.Context):
        voice = ctx.voice_client
        try:

            if(voice.is_playing):
                voice.resume()
                await ctx.send("Ok! Resuming!")
            else: 
                await ctx.send("I'm not playing anything right now")

        except Exception as e:
            print(e)
    
    @commands.hybrid_command(name="stop", description="I'll stop playing the current song")
    async def stop(self,ctx: commands.Context):
        voice = ctx.voice_client
        try:

            if(voice.is_playing):
                self.music_queue.pop(0)
                voice.stop()
                await ctx.send("Ok! Stopping.")
            else:
                await ctx.send("I'm not playing anything right now")

        except Exception as e:
            print(e)

    @commands.hybrid_command(name="now-playing", description="I'll show what's playing right now")
    async def now_playing(self,ctx: commands.Context):
        voice = ctx.voice_client
        try:

            if(voice.is_playing):
                await ctx.send(f"Playing now: {self.now_playing}")
            else:
                await ctx.send("I'm not playing anything right now")

        except Exception as e:
            print(e)

    @commands.hybrid_command(name="add-to-queue", description="I'll add your song to the queue")
    async def queue_add(self,ctx: commands.Context, url: str):
        voice = ctx.voice_client
        try:
            await ctx.interaction.response.defer(thinking=True)
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=False))
            qitem = {"title": data['title'], "url": url}
            self.music_queue.append(qitem)
            
            await ctx.interaction.followup.send(f"Ok! I added \"{data['title']}\" to the queue!")

        except Exception as e:
            print(e)

    @commands.hybrid_command(name="play-next",description="I'll play the next song in queue")
    async def play_next(self, ctx: commands.Context):
        try:

            url = self.music_queue[0]['url']
            await self.play(ctx,url)
            self.music_queue.pop(0)

        except Exception as e:
            print(e)

    @commands.hybrid_command(name="queue",description="I'll show what's queued up")
    async def show_queue(self, ctx: commands.Context):
        try:

            queue = queueView()
            queue.data= self.music_queue
            await queue.send(ctx)

        except Exception as e:
            print(e)

    @commands.hybrid_command(name="remove-from-queue",description="I'll remove this song from queue")
    async def queue_remove(self, ctx: commands.Context,queue_number: int ):
        try:
            self.music_queue.pop(queue_number - 1)
            await ctx.send(f"Ok! I removed #{queue_number} from queue.")
        except Exception as e:
            print(e)

async def setup(bot: commands.Bot):
    await bot.add_cog(music(bot))
