import discord
import asyncio
from discord.ext import commands
from discord import app_commands
import yt_dlp
from yt_dlp import YoutubeDL

class music(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        
        
        self.is_playing = False
        self.is_paused = False

        self.music_queue =[]
        self.YDL_OPTIONS = {'format' : 'bestaudio/best', 'noplaylist': 'True'}
        self.ytdl = yt_dlp.YoutubeDL(self.YDL_OPTIONS)
        self.FFMPEG_OPTIONS = {'options': '-vn'}
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

        except Exception as e:
            print(e)


async def setup(bot: commands.Bot):
    await bot.add_cog(music(bot))
