import discord
from discord.ext import commands
from discord import app_commands

class music(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    # @commands.command()
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


async def setup(bot: commands.Bot):
    await bot.add_cog(music(bot))
