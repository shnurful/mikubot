import discord
from discord.ext import commands
from discord import app_commands

class misc_commands(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    @commands.hybrid_command(name="avatar", description="shows the avatar of a user")
    async def avatar(self, ctx: commands.Context, user: discord.Member):
        avatar = user.display_avatar.url
        embed = discord.Embed(title=f"{user.name}")
        embed.set_image(url=avatar)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(misc_commands(bot))