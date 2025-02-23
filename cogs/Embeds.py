import discord
from discord.ext import commands
from discord import app_commands


class TestMenuButton(discord.ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)
    @discord.ui.button(label="Test", style=discord.ButtonStyle.blurple)
    async def test(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await interaction.channel.send(content="Clicked!")


class Embeds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()
        print(f"{__name__} loaded successfully!")

    @app_commands.command(name = "atkins", description = "sends atkins textbook")
    async def atkins(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Chemical Principles: The Quest for Insight", url="https://drive.google.com/open?id=11TN45Y-q-TY6Y8NkhjnNHGSMAZyvAtg0&usp=drive_copy", description="5th Edition", color=0xf93208)
        embed.set_author(name="Peter Atkins, Loretta Jones")
        embed.set_thumbnail(url="https://www1.alibris-static.com/chemical-principles-the-quest-for-insight/isbn/9781429219556_l.jpg")
        await interaction.response.send_message(embed=embed,view=TestMenuButton())


    @app_commands.command(name = "zumdahl", description = "sends zumdahl textbook")
    async def zumdahl(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Zumdahl Chemistry", url="https://drive.google.com/open?id=1Cms33xuuGzBKlJG4SvjFU57A55F7uuvJ&usp=drive_copy", description="10th Edition", color=0x00ff8f)
        embed.set_author(name="Steven Zumdahl, Susan Zumdahl, Donald Decoste")
        embed.set_thumbnail(url="https://m.media-amazon.com/images/I/81bSYRvl+CL._AC_UF1000,1000_QL80_.jpg")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name = "klein", description = "sends klein textbook")
    async def klein(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Organic Chemistry", url="https://drive.google.com/open?id=1DZR8XxwszTyMkB-nUoeRVc5qdM5xWqY2&usp=drive_copy", description="3rd Edition", color=0xffffff)
        embed.set_author(name="David R. Klein")
        embed.set_thumbnail(url="https://m.media-amazon.com/images/I/81D1OjTz79L._UF1000,1000_QL80_.jpg")
        await interaction.response.send_message(embed=embed)



async def setup(bot):
    await bot.add_cog(Embeds(bot))


