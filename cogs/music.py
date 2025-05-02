import discord
import asyncio
from discord.ext import commands
from discord import app_commands
import yt_dlp
from yt_dlp import YoutubeDL

class music(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

        self.music_queue =[]
        self.YDL_OPTIONS = {'format' : 'bestaudio/best', 'noplaylist': 'True'}
        self.ytdl = yt_dlp.YoutubeDL(self.YDL_OPTIONS)
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -attempt_recovery true -recover_any_error true'}
        self.vc = None
    
    @commands.hybrid_command(name="play", description="I'll play the video from the url provided")
    async def play(self,ctx: commands.Context, url: str):
        voice = ctx.voice_client
        try:
            loop = asyncio.get_event_loop()

            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=False))
            
            song = data['url']
            player = discord.FFmpegOpusAudio(song, **self.FFMPEG_OPTIONS)

            voice.play(player)
            await ctx.send(f"Now playing: {url} ")
            self.is_playing = True

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
    
    @commands.hybrid_command(name="stop", description="I'll stop playing")
    async def resume(self,ctx: commands.Context):
        voice = ctx.voice_client
        try:
            if(voice.is_playing):
                voice.stop()
                await ctx.send("Ok! Stopping.")
            else:
                await ctx.send("I'm not playing anything right now")
        except Exception as e:
            print(e)

async def setup(bot: commands.Bot):
    await bot.add_cog(music(bot))
