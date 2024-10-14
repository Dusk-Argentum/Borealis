from cogs.functions import EmbedBuilder

import disnake
from disnake.ext import commands

import sqlite3
from sqlite3 import OperationalError


class Aurora(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        aurora = disnake.utils.get(ctx.guild.roles, name="Aurora")
        if aurora not in ctx.author.roles:
            return
        return aurora in ctx.author.roles

    @staticmethod
    async def character_limit(self, ctx, inter, character_limit, source):
        src = None
        if source == "slash":
            src = inter
        elif source == "message":
            src = ctx
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description="Please wait.", fields=None,
                                         footer_text="Ideally, you should never see this.", status="waiting")
        response = await src.send(embed=EmbedBuilder.embed)
        if source == "slash":
            response = inter
            src.edit = inter.edit_original_response
        if character_limit > 10:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Character limit is too high!", fields=None,
                                             footer_text="""This bot can support a maximum of 10 characters per player \
per server.""", status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        try:
            con = sqlite3.connect("server_config.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        cur = con.cursor()
        cur.execute("UPDATE server_config SET character_limit = ? WHERE guild_id = ?",
                    [character_limit, src.guild.id])
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"""Updated character limit to \
{character_limit}.""", fields=None, footer_text="""This bot can support a maximum of 10 characters per player \
per server.""", status="success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)


    @commands.slash_command(name="character_limit", description="a", dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(0)
    async def character_limit_slash(self, inter, character_limit: int):
        await self. character_limit(self, ctx=None, inter=inter, character_limit=character_limit, source="slash")

    @commands.group(aliases=["limit"], brief="Set character limit.", help="Sets the server-wide character limit.",
                    name="character_limit", usage="character_limit <#>")
    @commands.guild_only()
    async def character_limit_message(self, ctx, character_limit: int):
        await self.character_limit(self, ctx=ctx, inter=None, character_limit=character_limit, source="slash")


def setup(bot):
    bot.add_cog(Aurora(bot))
