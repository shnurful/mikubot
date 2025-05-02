import discord
from discord.ext import commands
from discord import app_commands

class music(commands.Cog):
    def __init__(self,bot):
        self.bot = bot



async def setup(bot: commands.Bot):
    await bot.add_cog(music(bot))
