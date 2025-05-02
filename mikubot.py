import discord
from discord.ext import commands
from discord import app_commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()
handler = logging.FileHandler(filename='discord.log',encoding='utf-8',mode='w')

GUILD_ID = discord.Object(id=1367580756267765851)
discord.Permissions(permissions=274881103872)
discord.utils.oauth_url(1367576586324414554)

intents = discord.Intents.default()
intents.message_content= True
intents.voice_states= True

bot = commands.Bot(command_prefix='&', intents=intents)


@bot.tree.command(name="load", description="load a cog",guild=GUILD_ID)
async def load_cog(interaction: discord.Interaction, extension: str):
    await bot.load_extension(f"cogs.{extension}")
    await interaction.response.send_message(f"Cog '{extension} loaded.")
    print(f"Cog '{extension}' has been loaded.")

@bot.event
async def on_ready():
    print(f'Logged on as {bot.user}!')
    await bot.load_extension(f"cogs.maincommands")



# @bot.command()
# async def play(ctx):
#     voice = ctx.voice_client
#     try:
#         await voice.play()
#     except Exception as e:
#         if(e == "ClientException"):
#             if(not voice.is_connected()):
#                 await ctx.send("I'm not in a voice channel")
#             else:
#                 await ctx.send("I'm busy right now")
#         else:
#             await ctx.send("Sorry, I can't do that")

bot.run('MTM2NzU3NjU4NjMyNDQxNDU1NA.GAzwl6.7bU5y3KTZU6B7JYn2oaH7nHy5JyFclDL2sj3b0',log_handler=handler,log_level=logging.DEBUG)

        
        

