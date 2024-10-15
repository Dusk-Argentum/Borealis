import json

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
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"""Updated character limit to \
{character_limit}.""", fields=None, footer_text="""This bot can support a maximum of 10 characters per player \
per server.""", status="success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @staticmethod
    async def experience_threshold(self, ctx, inter, level, experience, source):
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
        try:
            con = sqlite3.connect("server_config.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT maximum_level, experience_thresholds FROM server_config WHERE guild_id = ?",
                    [src.guild.id])
        server_config = [dict(value) for value in cur.fetchall()][0]
        con.close()
        if level > int(server_config["maximum_level"]):
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Level exceeds maximum for this server!",
                                             fields=None, footer_text=f"""The level you are attempting to edit exceeds \
the maximum level for this server ({server_config["maximum_level"]}).""", status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        thresholds = json.loads(server_config["experience_thresholds"])
        if level < int(server_config["maximum_level"]):
            if experience >= int(thresholds[f"{level + 1}"]):
                await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None,
                                                 description="""Experience threshold exceeds the threshold for the \
following level!""", fields=None, footer_text=f"""The threshold for level {level + 1} is \
{thresholds[f"{level + 1}"]}.""", status="alert")
                return
        thresholds[str(level)] = experience
        thresholds = json.dumps(thresholds, indent=2)
        try:
            con = sqlite3.connect("server_config.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        cur = con.cursor()
        cur.execute("UPDATE server_config SET experience_thresholds = ? WHERE guild_id = ?",
                    [thresholds, src.guild.id])
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"""Updated the experience threshold for level \
{level} to {experience}.""", fields=None, footer_text=f"Players now need {experience} experience to hit level {level}.",
                                         status="success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @staticmethod
    async def maximum_level(self, ctx, inter, maximum_level, source):
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
        if maximum_level > 100:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Maximum level is too high!", fields=None,
                                             footer_text="The maximum maximum level is 100.", status="alert")
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
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("""SELECT experience_thresholds FROM server_config WHERE \
guild_id = ?""", [src.guild.id])
        server_config = [dict(value) for value in cur.fetchall()][0]
        con.close()
        thresholds = json.loads(server_config["experience_thresholds"])
        for level in range(1, maximum_level + 1):
            if thresholds.get(str(level)) is None:
                thresholds[str(level)] = int(thresholds[str(level - 1)]) + 1
        thresholds = json.dumps(thresholds, indent=2)
        try:
            con = sqlite3.connect("server_config.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        cur = con.cursor()
        cur.execute("UPDATE server_config SET maximum_level = ?, experience_thresholds = ? WHERE guild_id = ?",
                    [maximum_level, thresholds, src.guild.id])
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"Updated maximum level to {maximum_level}.",
                                         fields=None, footer_text="""Set the threshold of every level between the old \
and new maximum level to be one higher than each previous.\nPlease do not forget to update the thresholds!""",
                                         status="success")
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
        con.commit()
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
        con.commit()
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
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"""Updated the start of OOC messages to be \
denoted as {ooc_start}.""", fields=None, footer_text="""Please note that this feature only works if both ooc_start \
AND ooc_end are set.""", status="success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @staticmethod
    async def starting_level(self, ctx, inter, starting_level, source):
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
        try:
            con = sqlite3.connect("server_config.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("""SELECT maximum_level, experience_thresholds, tier_thresholds FROM server_config WHERE \
guild_id = ?""", [src.guild.id])
        server_config = [dict(value) for value in cur.fetchall()][0]
        con.close()
        if starting_level > int(server_config["maximum_level"]):
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Starting level exceeds maximum level!",
                                             fields=None, footer_text=f"""Please choose a starting level less than \
this server's maximum level ({server_config["maximum_level"]}).""", status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        starting_experience = 1
        for level, minimum in json.loads(server_config["experience_thresholds"]).items():
            if int(server_config["starting_level"]) == int(level):
                starting_experience = int(minimum)
                break
        starting_tier = 1
        for tier, threshold in json.loads(server_config["tier_thresholds"]).items():
            if threshold <= int(server_config["starting_level"]):
                starting_tier = int(tier)
        try:
            con = sqlite3.connect("server_config.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        cur = con.cursor()
        cur.execute("UPDATE server_config SET starting_level = ? WHERE guild_id = ?",
                    [starting_level, src.guild.id])
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"""The starting level has been updated to \
{starting_level}.""", fields=None, footer_text=f"""Players will start with {starting_experience} experience and in \
tier {starting_tier}.""", status="success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @staticmethod
    async def tier_threshold(self, ctx, inter, tier, level, source):
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
        try:
            con = sqlite3.connect("server_config.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT maximum_level FROM server_config WHERE guild_id = ?",
                    [src.guild.id])
        server_config = [dict(value) for value in cur.fetchall()][0]
        con.close()
        if tier > 10:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None,
                                             description="Tier exceeds maximum supported tier!",
                                             fields=None,
                                             footer_text="The maximum number of tiers supported per server is 10.",
                                             status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        if level > int(server_config["maximum_level"]):
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None,
                                             description="Threshold exceeds maximum level for this server!",
                                             fields=None,
                                             footer_text=f"""The threshold you are attempting to set exceeds the \
maximum level for this server ({server_config["maximum_level"]}).""", status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        thresholds = json.loads(server_config["tier_thresholds"])
        if level < int(server_config["maximum_level"]):
            if level >= int(thresholds[f"{tier + 1}"]):
                await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None,
                                                 description="""Level threshold exceeds the threshold for the \
following tier!""", fields=None, footer_text=f"""The threshold for tier {tier + 1} is \
{thresholds[f"{tier + 1}"]}.""", status="alert")
                return
        thresholds[str(tier)] = level
        thresholds = json.dumps(thresholds, indent=2)
        try:
            con = sqlite3.connect("server_config.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        cur = con.cursor()
        cur.execute("UPDATE server_config SET tier_thresholds = ? WHERE guild_id = ?",
                    [thresholds, src.guild.id])
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"""Updated the level threshold for tier \
{tier} to {level}.""", fields=None,
                                         footer_text=f"Players now need to be at least level {level} experience to \
hit tier {tier}.", status="success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @staticmethod  # TODO: Add descriptions to Slash Command arguments.
    # @discord.app_commands.describe(date = "Date in YYYY-MM-DD format")
    async def time_between(self, ctx, inter, time_between, source):
        # TODO: Minimum for this should be 30 to help mitigate load on db?
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
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"""The time between experience-rewarding \
messages to {time_between} seconds.""", fields=None, footer_text="""The maximum length of time between \
experience-rewarding messages is 3600 seconds (1 hour).""", status="success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @commands.slash_command(name="character_limit", description="Sets the server-wide character limit.",
                            dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_guild=True)
    async def character_limit_slash(self, inter, character_limit: int):
        await self.character_limit(self, ctx=None, inter=inter, character_limit=character_limit, source="slash")

    @commands.group(aliases=["limit"], brief="Set character limit.", help="Sets the server-wide character limit.",
                    name="character_limit", usage="character_limit <#>")
    @commands.guild_only()
    async def character_limit_message(self, ctx, character_limit: int):
        await self.character_limit(self, ctx=ctx, inter=None, character_limit=character_limit, source="message")

    @commands.slash_command(name="experience_threshold",
                            description="Sets the amount of experience required to reach the specified level.",
                            dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_guild=True)
    async def experience_threshold_slash(self, inter, level: int, experience: int):
        await self.experience_threshold(self, ctx=None, inter=inter, level=level, experience=experience, source="slash")

    @commands.group(aliases=["xp_thresh"], brief="Sets experience for level.",
                    help="Sets the amount of experience required to reach the specified level.",
                    name="experience_threshold", usage="experience_threshold <#> <#>")
    @commands.guild_only()
    async def experience_threshold_message(self, ctx, level: int, experience: int):
        await self.experience_threshold(self, ctx=ctx, inter=None, level=level, experience=experience, source="message")

    @commands.slash_command(name="maximum_level", description="Sets the maximum level on the server.",
                            dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_guild=True)
    async def maximum_level_slash(self, inter, maximum_level: int):
        await self.maximum_level(self, ctx=None, inter=inter, maximum_level=maximum_level, source="slash")

    @commands.group(aliases=["max"], brief="Sets maximum level.", help="Sets the maximum level on the server.",
                    name="maximum_level", usage="maximum_level <#>")
    @commands.guild_only()
    async def maximum_level_message(self, ctx, maximum_level: int):
        await self.maximum_level(self, ctx=ctx, inter=None, maximum_level=maximum_level, source="message")

    @commands.slash_command(name="minimum_length",
                            description="Sets the minimum length a message must be to gain experience.",
                            dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_guild=True)
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
    @commands.default_member_permissions(manage_guild=True)
    async def ooc_start_slash(self, inter, ooc_end: str):
        await self.ooc_end(self, ctx=None, inter=inter, ooc_end=ooc_end, source="slash")

    @commands.group(aliases=["o_end"], brief="Denotes end of OOC.", help="Denotes the end of OOC messages.",
                    name="ooc_end", usage="ooc_end <string>")
    @commands.guild_only()
    async def ooc_end_message(self, ctx, ooc_end: str):
        await self.ooc_end(self, ctx=ctx, inter=None, ooc_end=ooc_end, source="message")

    @commands.slash_command(name="ooc_start", description="Denotes the start of OOC messages.", dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_guild=True)
    async def ooc_start_slash(self, inter, ooc_start: str):
        await self.ooc_start(self, ctx=None, inter=inter, ooc_start=ooc_start, source="slash")

    @commands.group(aliases=["o_start"], brief="Denotes start of OOC.", help="Denotes the start of OOC messages.",
                    name="ooc_start", usage="ooc_start <string>")
    @commands.guild_only()
    async def ooc_start_message(self, ctx, ooc_start: str):
        await self.ooc_start(self, ctx=ctx, inter=None, ooc_start=ooc_start, source="message")

    @commands.slash_command(name="starting_level",
                            description="Sets the level that newly initialized characters will start at.",
                            dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_guild=True)
    async def starting_level_slash(self, inter, starting_level: int):
        await self.starting_level(self, ctx=None, inter=inter, starting_level=starting_level, source="slash")

    @commands.group(aliases=["start"], brief="Sets starting level.",
                    help="Sets the level that newly initialized characters will start at.", name="starting_level",
                    usage="starting_level <#>")
    @commands.guild_only()
    async def starting_level_message(self, ctx, starting_level: int):
        await self.starting_level(self, ctx=ctx, inter=None, starting_level=starting_level, source="message")

    @commands.slash_command(name="tier_threshold",
                            description="Sets the level required to reach the specified tier.",
                            dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_guild=True)
    async def tier_threshold_slash(self, inter, tier: int, level: int):
        await self.tier_threshold(self, ctx=None, inter=inter, tier=tier, level=level, source="slash")

    @commands.group(aliases=["tier_thresh"], brief="Sets level for tier.",
                    help="Sets the level required to reach the specified tier.", name="tier_threshold",
                    usage="tier_threshold <#> <#>")
    @commands.guild_only()
    async def tier_threshold_message(self, ctx, tier: int, level: int):
        await self.tier_threshold(self, ctx=ctx, inter=None, tier=tier, level=level, source="message")

    @commands.slash_command(name="time_between",
                            description="Sets the time (in seconds) between experience-rewarding messages.",
                            dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_guild=True)
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
