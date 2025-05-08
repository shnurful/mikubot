import discord
import asyncio
import json
import validators
import requests
from discord.ext import commands
from discord import app_commands
import yt_dlp
from yt_dlp import YoutubeDL
from dotenv import load_dotenv
import os

#TODO: make commands execute per server instead of globally
#TODO: add folder for ffmpeg and path variable

load_dotenv()

class SongSelect(discord.ui.Select):
    def __init__(self, songMap):
        #options can be an array that we can hardcode, but we pass in the map
        #placeholder is just what shows up before selecting an option
        super().__init__(placeholder="Select a result", max_values=1, min_values=1, options = songMap)

    async def callback(self, interaction: discord.Interaction):
        #get key
        title = self.values[0]

        #build url
        urlBase = "https://www.youtube.com/watch?v="
        songId = self.view.songMap[title]
        fullUrl = urlBase + songId

        self.view.value = fullUrl
        self.view.stop()
        await interaction.response.defer()

class SongSelectView(discord.ui.View):
    def __init__(self, songMap):
        #respond within 60 seconds
        super().__init__(timeout=60)
        self.songMap = songMap 
        self.value = None
        options = [
            #add option per result
            discord.SelectOption(label=title) for title, url in songMap.items()
        ]
        self.add_item(SongSelect(options))

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

        self.loop_on = False
        self.music_queue = []
        self.now_playing_url = ""
        self.now_playing_title = ""

        self.YDL_OPTIONS = {'format' : 'bestaudio/best', 'noplaylist': 'True'}
        self.ytdl = yt_dlp.YoutubeDL(self.YDL_OPTIONS)
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -attempt_recovery true -recover_any_error true'}
        self.vc = None
    

    @commands.hybrid_command(name="play", description="enter a url or search for a song")
    async def play(self,ctx: commands.Context, query_or_url: str):

        await ctx.interaction.response.defer(thinking=True)

        if not validators.url(query_or_url):
            #get api key fron env
            youtube_URL = 'https://www.googleapis.com/youtube/v3/search'

            #build params dict
            paramMap = {
                'key': os.getenv('YOUTUBE_API_KEY'),
                'part' : 'snippet',
                'type': 'video',
                'q' : query_or_url
            }

            #send api request for query
            apiResponse = requests.get(youtube_URL, paramMap)

            responseJSONObject = apiResponse.json()

            #place 
            resultMap = {}
            for apiresult in responseJSONObject['items']:
                if apiresult['id']['kind'] != "youtube#channel":
                    url = apiresult['id']['videoId']
                    title = apiresult['snippet']['title']
                    resultMap[title] = url

                

            for key, value in resultMap.items():
                print(key, value)

            view = SongSelectView(resultMap)
            await ctx.interaction.followup.send("Search results:", view=view)
            #start waiting for user to select something
            await view.wait()

            if view.value:
                query_or_url = view.value #should be the url of the selected title
            else:
                await ctx.interaction.followup.send("Selection timed out :(")

        try:
            voice = ctx.voice_client

            if(voice == None):
                member = ctx.author
                invoice = await member.fetch_voice()
                channel = invoice.channel
                await channel.connect()

        except Exception:
            await ctx.interaction.followup.send(f"{member}, you're not in a channel!")            
            
        try:
            vc = ctx.voice_client

            if(vc.is_playing()):
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(query_or_url, download=False))
                qitem = {"title": data['title'], "url": query_or_url}
                self.music_queue.append(qitem)
                await ctx.interaction.followup.send(f"Ok! I added \"{data['title']}\" to the queue!")
                return


            loop = asyncio.get_event_loop()

            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(query_or_url, download=False))

            song = data['url']
            title = data['title']
            player = discord.FFmpegOpusAudio(song, **self.FFMPEG_OPTIONS)

            vc.play(player, after= lambda e: asyncio.run_coroutine_threadsafe(self.do_autoplay(ctx),loop))

            await ctx.interaction.followup.send(f"Now playing: {title} ")
            self.now_playing = query_or_url

        except Exception as e:
            print(e)


    @commands.hybrid_command(name="pause", description="I'll pause what's currently playing")
    async def pause(self,ctx: commands.Context):
        voice = ctx.voice_client
        try:
            if (voice == None):
                await ctx.send("I'm not in a channel right now")

            else:

                if(voice.is_playing()):
                    voice.pause()
                    await ctx.send("Ok! Paused.")
                elif(voice.is_paused()):
                    await ctx.send("It's already paused!")
                else:
                    await ctx.send("I'm not playing anything right now")

        except Exception as e:
            print(e)
    
    @commands.hybrid_command(name="resume", description="I'll resume what's currently playing")
    async def resume(self,ctx: commands.Context):
        voice = ctx.voice_client
        try:
            if (voice == None):
                await ctx.send("I'm not in a channel right now")
            else:
                if(voice.is_paused()):
                    voice.resume()
                    await ctx.send("Ok! Resuming!")
                elif(voice.is_playing()):
                    await ctx.send("It's already playing!")
                else: 
                    await ctx.send("I'm not playing anything right now")

        except Exception as e:
            print(e)
    
    @commands.hybrid_command(name="stop", description="I'll stop playing the current song")
    async def stop(self,ctx: commands.Context):
        voice = ctx.voice_client
        try:

            if(voice.is_playing()):
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

            if(voice.is_playing()):
                await ctx.send(f"Playing now: {self.now_playing_title}")
            else:
                await ctx.send("I'm not playing anything right now")

        except Exception as e:
            print(e)

    @commands.hybrid_command(name="play-next",description="I'll play the next song in queue")
    async def play_next(self, ctx: commands.Context):
        try:
            if self.music_queue:
                url = self.music_queue[0]['url']
                await self.play(ctx,url)
                self.music_queue.pop(0)
            else:
                await ctx.send("There's nothing in queue!")
        except Exception as e:
            print(e)

    @commands.hybrid_command(name="queue",description="I'll show what's queued up")
    async def show_queue(self, ctx: commands.Context):
        try:
            if self.music_queue:
                queue = queueView()
                queue.data= self.music_queue
                await queue.send(ctx)
            else:
                await ctx.send("There's nothing in queue!")

        except Exception as e:
            print(e)

    @commands.hybrid_command(name="remove-from-queue",description="I'll remove this song from queue")
    async def queue_remove(self, ctx: commands.Context,queue_number: int ):
        try:
            if self.music_queue:
                self.music_queue.pop(queue_number - 1)
                await ctx.send(f"Ok! I removed #{queue_number} from queue.")
            else:
                await ctx.send("There's nothing in queue!")

        except Exception as e:
            print(e)
    
    @commands.hybrid_command(name="repeat",description="I'll enable reapeat mode")
    async def loop_song(self,ctx):
        
        if self.loop_on:
            self.loop_on = False
            await ctx.send("Ok! Looping disabled.")
        else:
            self.loop_on = True
            await ctx.send("Ok! Looping enabled.")


async def setup(bot: commands.Bot):
    await bot.add_cog(music(bot))
