import discord
from discord.ext import commands
from discord import app_commands
import logging
from dotenv import load_dotenv
import os
import markov
load_dotenv()
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")

GUILD_ID = discord.Object(id=1367580756267765851)
discord.Permissions(permissions=274881103872)
discord.utils.oauth_url(1367576586324414554)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="&", intents=intents)


@bot.hybrid_command(name="reload-cog", description="reload specified cog")
async def reload(ctx: commands.Context, arg: str):
    await bot.reload_extension(f"cogs.{arg}")
    await ctx.send(f"I reloaded {arg}!")
    await bot.tree.sync()


@bot.event
async def on_ready():
    print(f"Logged on as {bot.user}!")
    await bot.load_extension("cogs.maincommands")
    await bot.load_extension("cogs.music")
    await bot.load_extension("cogs.misccommands")
    await bot.tree.sync()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if bot.user in message.mentions:
        await message.channel.send(markov.generate_markov_text())
 

bot.run(os.getenv("DISCORD_TOKEN"), log_handler=handler, log_level=logging.DEBUG)
