import discord
from discord.ext import commands
import logging

import discord.voice_state

handler = logging.FileHandler(filename='discord.log',encoding='utf-8',mode='w')

discord.Permissions(permissions=274881103872)
discord.utils.oauth_url(1367576586324414554)

intents = discord.Intents.default()
intents.message_content= True
intents.voice_states= True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged on as {bot.user}!')

@bot.command()
async def join(ctx):
    member = ctx.author
    try:
        invoice = await member.fetch_voice()
        channel = invoice.channel
    except:
        await ctx.send(f"{member}, you're not in a channel!")

    await channel.connect()

@bot.command()
async def leave(ctx):
    voice = ctx.voice_client
    await voice.disconnect()

bot.run('MTM2NzU3NjU4NjMyNDQxNDU1NA.GAzwl6.7bU5y3KTZU6B7JYn2oaH7nHy5JyFclDL2sj3b0',log_handler=handler,log_level=logging.DEBUG)

        
        

