import disnake
from disnake.ext import commands


class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["a"], brief="b", help="c", name="test", usage="e")
    @commands.guild_only()
    async def test(self, ctx):
        print("test")


def setup(bot):
    bot.add_cog(Dev(bot))
