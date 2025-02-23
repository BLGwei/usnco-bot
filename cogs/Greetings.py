import discord
from discord.ext import commands
from discord import app_commands

class Greetings(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    

    @commands.Cog.listener()
    async def on_member_join(self, user:discord.Member, *, message=None):
        message = "Welcome to the Server for Chemistry Olympiad!"
        embed = discord.Embed(title=message, description="The server and bot development is currently under construction...")
        embed.set_thumbnail(url="https://media.tenor.com/hzFLnSmfw38AAAAi/bugcat-capoo.gif")
        await user.send(embed=embed)

    
async def setup(bot : commands.Bot):
    await bot.add_cog(Greetings(bot))
