import discord
from discord.ext import commands
from discord import app_commands

class main_commands(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    #TODO: add exception handling for connecting, improve exception handling for fetch_voice()
    @commands.hybrid_command(name="join", description="I will join your current channel")
    async def join(self,ctx: commands.Context):
        member = ctx.author
        try:
            invoice = await member.fetch_voice()
            channel = invoice.channel
        except:
            await ctx.send(f"{member}, you're not in a channel!")

        await channel.connect()
        await ctx.send("はい!いきます！")
    
    #TODO: add exception handling
    @commands.hybrid_command(name="leave", description="I will leave my current channel")
    async def leave(self,ctx):
        voice = ctx.voice_client
        await voice.disconnect()
        await ctx.send("またね！")

async def setup(bot: commands.Bot):
    await bot.add_cog(main_commands(bot))
