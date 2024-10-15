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
        elif ctx.message.author.guild_permissions.administrator is False:
            return
        return aurora in ctx.author.roles or ctx.message.author.guild_permissions.administrator is True

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

    @staticmethod
    async def minimum_length(self, ctx, inter, minimum_length, source):
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
        if minimum_length > 2000:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Minimum length is too high!", fields=None,
                                             footer_text="""Please select a minimum length that is less than the \
(non-Nitro) maximum number of characters permitted per message.""", status="alert")
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
        cur.execute("UPDATE server_config SET minimum_length = ? WHERE guild_id = ?",
                    [minimum_length, src.guild.id])
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"""Updated minimum length to \
{minimum_length}.""", fields=None, footer_text="The maximum that a minimum length can be is 2000.", status="success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @staticmethod
    async def ooc_end(self, ctx, inter, ooc_end, source):
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
        if len(ooc_end) > 3:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Too long!", fields=None,
                                             footer_text="""For optimal play, please choose a string that is less than \
or equal to 3 characters long, including spaces.""", status="alert")
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
        cur.execute("UPDATE server_config SET ooc_end = ? WHERE guild_id = ?",
                    [ooc_end, src.guild.id])
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"""Updated the end of OOC messages to be \
denoted as {ooc_end}.""", fields=None, footer_text="""Please note that this feature only works if both ooc_start \
AND ooc_end are set.""", status="success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @staticmethod
    async def ooc_start(self, ctx, inter, ooc_start, source):
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
        if len(ooc_start) > 3:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Too long!", fields=None,
                                             footer_text="""For optimal play, please choose a string that is less than \
or equal to 3 characters long, including spaces.""", status="alert")
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
        cur.execute("UPDATE server_config SET ooc_start = ? WHERE guild_id = ?",
                    [ooc_start, src.guild.id])
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"""Updated the start of OOC messages to be \
denoted as {ooc_start}.""", fields=None, footer_text="""Please note that this feature only works if both ooc_start \
AND ooc_end are set.""", status="success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @staticmethod  # TODO: Add descriptions to Slash Command arguments.
    # @discord.app_commands.describe(date = "Date in YYYY-MM-DD format")
    async def time_between(self, ctx, inter, time_between, source):
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
        if time_between > 3600:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Time between is too high!", fields=None,
                                             footer_text="""The maximum supported length between experience-rewarding \
messages is 3600 seconds (1 hour).""", status="alert")
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
        cur.execute("UPDATE server_config SET time_between = ? WHERE guild_id = ?",
                    [time_between, src.guild.id])
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"""The time between experience-rewarding \
messages to {time_between} seconds.""", fields=None, footer_text="""The maximum length of time between \
experience-rewarding messages is 3600 seconds (1 hour).""", status="success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @commands.slash_command(name="character_limit", description="Sets the server-wide character limit.",
                            dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_server=True)
    async def character_limit_slash(self, inter, character_limit: int):
        await self.character_limit(self, ctx=None, inter=inter, character_limit=character_limit, source="slash")

    @commands.group(aliases=["limit"], brief="Set character limit.", help="Sets the server-wide character limit.",
                    name="character_limit", usage="character_limit <#>")
    @commands.guild_only()
    async def character_limit_message(self, ctx, character_limit: int):
        await self.character_limit(self, ctx=ctx, inter=None, character_limit=character_limit, source="message")

    @commands.slash_command(name="minimum_length",
                            description="Sets the minimum length a message must be to gain experience.",
                            dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_server=True)
    async def minimum_length_slash(self, inter, minimum_length: int):
        await self.minimum_length(self, ctx=None, inter=inter, minimum_length=minimum_length, source="slash")

    @commands.group(aliases=["min"], brief="Set minimum length.",
                    help="Sets the minimum length a message must be to gain experience.", name="minimum_length",
                    usage="minimum_length <#>")
    @commands.guild_only()
    async def minimum_length_message(self, ctx, minimum_length: int):
        await self.minimum_length(self, ctx=ctx, inter=None, minimum_length=minimum_length, source="message")

    @commands.slash_command(name="ooc_end", description="Denotes the end of OOC messages.", dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_server=True)
    async def ooc_start_slash(self, inter, ooc_end: str):
        await self.ooc_end(self, ctx=None, inter=inter, ooc_end=ooc_end, source="slash")

    @commands.group(aliases=["end"], brief="Denotes end of OOC.", help="Denotes the end of OOC messages.",
                    name="ooc_end", usage="ooc_end <string>")
    @commands.guild_only()
    async def ooc_end_message(self, ctx, ooc_end: str):
        await self.ooc_end(self, ctx=ctx, inter=None, ooc_end=ooc_end, source="message")

    @commands.slash_command(name="ooc_start", description="Denotes the start of OOC messages.", dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_server=True)
    async def ooc_start_slash(self, inter, ooc_start: str):
        await self.ooc_start(self, ctx=None, inter=inter, ooc_start=ooc_start, source="slash")

    @commands.group(aliases=["start"], brief="Denotes start of OOC.", help="Denotes the start of OOC messages.",
                    name="ooc_start", usage="ooc_start <string>")
    @commands.guild_only()
    async def ooc_start_message(self, ctx, ooc_start: str):
        await self.ooc_start(self, ctx=ctx, inter=None, ooc_start=ooc_start, source="message")

    @commands.slash_command(name="time_between",
                            description="Sets the time (in seconds) between experience-rewarding messages.",
                            dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_server=True)
    async def time_between_slash(self, inter, time_between: int):
        await self.time_between(self, ctx=None, inter=inter, time_between=time_between, source="slash")

    @commands.group(aliases=["time"], brief="Sets seconds between messages.",
                    help="Sets the time (in seconds) between experience-rewarding messages.", name="time_between",
                    usage="time_between <#>")
    @commands.guild_only()
    async def time_between_message(self, ctx, time_between: int):
        await self.time_between(self, ctx=ctx, inter=None, time_between=time_between, source="message")


def setup(bot):
    bot.add_cog(Aurora(bot))
