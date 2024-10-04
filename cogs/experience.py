import disnake
from disnake.ext import commands

from bot import GUILD, PREFIX

import sqlite3

class Experience(commands.Cog):
    def __init(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.id != self.bot.id:
