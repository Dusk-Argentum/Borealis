import json

from cogs.functions import EmbedBuilder

import disnake
from disnake.ext import commands

import sqlite3
from sqlite3 import OperationalError


class ChannelSelection(disnake.ui.View):  # TODO: Change to MultiSelect?
    selected = None

    def __init__(self, src, options, max_values):
        super().__init__(timeout=30)
        self.src = src
        self.channel_selection.options = options
        self.channel_selection.max_values = max_values

    async def interaction_check(self, inter: disnake.MessageInteraction):
        try:
            if inter.user.id != self.src.message.author.id:
                return
            return inter.user.id == self.src.message.author.id
        except AttributeError:
            if inter.user.id != self.src.author.id:
                return
            return inter.user.id == self.src.author.id

    @disnake.ui.string_select(placeholder="Select a channel.", options=[], min_values=1, max_values=1)
    async def channel_selection(self, select: disnake.ui.StringSelect, inter: disnake.MessageInteraction):
        ChannelSelection.selected = select.values
        await inter.response.defer()
        self.stop()


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
    async def base_percentage(self, ctx, inter, base_percentage, source):
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
        base_percentage = float("{:.2f}".format(base_percentage))
        if base_percentage > 10:  # TODO: Do I truly need error handling on all of these to make sure the numbers are
            # not negative?
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Base multiplier is too high!", fields=None,
                                             footer_text="The maximum base percentage is 10.", status="alert")
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
        cur.execute("UPDATE server_config SET base_percentage = ? WHERE guild_id = ?",
                    [base_percentage, src.guild.id])
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"""Updated base percentage to \
{base_percentage}.""", fields=None, footer_text=f"""Each message will grant a base {base_percentage}% of the \
experience required for the next level, before multipliers.""", status="success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @staticmethod
    async def channel_multiplier(self, ctx, inter, channel, multiplier, source):
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
        if channel.guild != src.guild:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="That is not a channel in this server!",
                                             fields=None, footer_text="Please select a channel from this server.",
                                             status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        if len(channel.name) > 50:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Channel name too long!",
                                             fields=None, footer_text="""For technical reasons, please only select \
channels with names that are less than 50 characters.""", status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        multiplier = float("{:.2f}".format(multiplier))
        if multiplier > 10:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Multiplier exceeds maximum supported!",
                                             fields=None, footer_text="The maximum supported channel multiplier is 10.",
                                             status="alert")
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
        cur.execute("SELECT level_multipliers FROM server_config WHERE guild_id = ?",
                    [src.guild.id])
        server_config = [dict(value) for value in cur.fetchall()][0]
        multipliers = json.loads(server_config["level_multipliers"])
        multipliers[f"{channel.id}"] = multiplier
        multipliers = json.dumps(multiplier, indent=2)
        cur.execute("UPDATE server_config SET channel_multipliers = ? WHERE guild_id = ?",
                    [multipliers, src.guild.id])
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"""Updated the experience multiplier for \
{channel.mention} to {multiplier}.""", fields=None,
                                         footer_text="A multiplier of 1 has no impact on the experience formula.",
                                         status="success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

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
    async def ignore_channel(self, ctx, inter, channel, source):
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
        if channel.guild != src.guild:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="That is not a channel in this server!",
                                             fields=None, footer_text="Please select a channel from this server.",
                                             status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        if len(channel.name) > 50:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Channel name too long!",
                                             fields=None, footer_text="""For technical reasons, please only select \
channels with names that are less than 50 characters.""", status="alert")
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
        cur.execute("SELECT ignored_channels FROM server_config WHERE guild_id = ?",
                    [src.guild.id])
        server_config = [dict(value) for value in cur.fetchall()][0]
        con.close()
        for channel_in_list in json.loads(server_config["ignored_channels"]):
            channel_in_list = disnake.utils.get(src.guild.channels, id=int(channel_in_list))
            if channel_in_list.id == channel.id:
                channel_list = []
                current_channel = disnake.utils.get(src.guild.channels, id=channel.id)
                for channel_id in json.loads(server_config["ignored_channels"]):
                    channel_resolve = disnake.utils.get(src.guild.channels, id=channel_id)
                    channel_list.append(channel_resolve)
                view = disnake.ui.View(timeout=30)
                selects = view.add_item(
                    disnake.ui.StringSelect(placeholder="Select which channel(s) to remove.", options=[],
                                            min_values=1, max_values=1))
                selects.children[0].add_option(label="None, cancel!", value="None, cancel!",
                                               description="This option will abort the modification process.")
                selects.children[0].add_option(label=current_channel.name, value=current_channel.id,
                                               description=f"""This option will remove {current_channel.name} \
from this server's list of ignored channels.""")
                for channel_in_list_ in channel_list:
                    if channel_in_list_.id != current_channel.id:
                        selects.children[0].add_option(label=channel_in_list_.name, value=channel_in_list_.id,
                                                       description=f"""This option will remove \
{channel_in_list_.name} from this server's list of ignored channels.""")
                view = ChannelSelection(src=src, options=selects.children[0].options, max_values=len(channel_list))
                await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None, description=f"""Unassign {channel.mention} as an \
ignored channel on this server?""", fields=None, footer_text="You may also select other ignored channels to remove.",
                                                 status="unsure")
                await response.edit(content=None, embed=EmbedBuilder.embed, view=view)
                timeout = await view.wait()
                selected = ChannelSelection.selected
                if timeout:
                    selected = "None, cancel!"
                if "None, cancel!" == selected[0] or "None, cancel!" == selected:
                    await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                     custom_title=None,
                                                     description="Server modification aborted.",
                                                     fields=None, footer_text="Please feel free to try again.",
                                                     status="add_failure")
                    await response.edit(embed=EmbedBuilder.embed, view=None)
                    return
                for entry in selected:
                    channel_select = disnake.utils.get(src.guild.channels, id=int(entry))
                    channel_list.remove(channel_select)
                channels = []
                for entry in channel_list:
                    channels.append(entry.id)
                channels = json.dumps(channels)
                break
        else:
            channels = json.loads(server_config["ignored_channels"])
            channels.append(channel.id)
            channels = json.dumps(channels)
        try:
            con = sqlite3.connect("server_config.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        cur = con.cursor()
        cur.execute("UPDATE server_config SET ignored_channels = ? WHERE guild_id = ?",
                    [channels, src.guild.id])
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description="Updated the ignored channels list.",
                                         fields=None,
                                         footer_text="Ignored channels are disqualified from granting any experience.",
                                         status="success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @staticmethod
    async def ignore_role(self, ctx, inter, role, source):
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
        if role.guild != src.guild:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="That is not a role in this server!",
                                             fields=None, footer_text="Please select a role from this server.",
                                             status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        if len(role.name) > 50:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Role name too long!",
                                             fields=None, footer_text="""For technical reasons, please only select \
roles with names that are less than 50 characters.""", status="alert")
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
        cur.execute("SELECT ignored_roles FROM server_config WHERE guild_id = ?",
                    [src.guild.id])
        server_config = [dict(value) for value in cur.fetchall()][0]
        con.close()
        for role_in_list in json.loads(server_config["ignored_roles"]):
            role_in_list = disnake.utils.get(src.guild.roles, id=int(role_in_list))
            if role_in_list.id == role.id:
                role_list = []
                current_role = disnake.utils.get(src.guild.roles, id=role.id)
                for role_id in json.loads(server_config["ignored_roles"]):
                    role_resolve = disnake.utils.get(src.guild.channels, id=role_id)
                    role_list.append(role_resolve)
                view = disnake.ui.View(timeout=30)
                selects = view.add_item(
                    disnake.ui.StringSelect(placeholder="Select which role(s) to remove.", options=[],
                                            min_values=1, max_values=1))
                selects.children[0].add_option(label="None, cancel!", value="None, cancel!",
                                               description="This option will abort the modification process.")
                selects.children[0].add_option(label=current_role.name, value=current_role.id,
                                               description=f"""This option will remove {current_role.name} \
from this server's list of ignored roles.""")  # TODO: Limit on the amount of ignored channels/roles for dropdown
                # technical reasons?
                for role_in_list_ in role_list:  # TODO: if len selects.children[0] > 20: pass
                    if role_in_list_.id != current_role.id:
                        selects.children[0].add_option(label=role_in_list_.name, value=role_in_list_.id,
                                                       description=f"""This option will remove \
{role_in_list_.name} from this server's list of ignored roles.""")
                view = ChannelSelection(src=src, options=selects.children[0].options, max_values=len(role_list))
                await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None, description=f"""Unassign {role.name} as an \
ignored role on this server?""", fields=None,
                                                 footer_text="You may also select other ignored roles to remove.",
                                                 status="unsure")
                await response.edit(content=None, embed=EmbedBuilder.embed, view=view)
                timeout = await view.wait()
                selected = ChannelSelection.selected
                if timeout:
                    selected = "None, cancel!"
                if "None, cancel!" == selected[0] or "None, cancel!" == selected:
                    await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                     custom_title=None,
                                                     description="Server modification aborted.",
                                                     fields=None, footer_text="Please feel free to try again.",
                                                     status="add_failure")
                    await response.edit(embed=EmbedBuilder.embed, view=None)
                    return
                for entry in selected:
                    role_select = disnake.utils.get(src.guild.channels, id=int(entry))
                    role_list.remove(role_select)
                roles = []
                for entry in role_list:
                    roles.append(entry.id)
                roles = json.dumps(roles)
                break
        else:
            roles = json.loads(server_config["ignored_roles"])
            roles.append(role.id)
            roles = json.dumps(roles)
        try:
            con = sqlite3.connect("server_config.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        cur = con.cursor()
        cur.execute("UPDATE server_config SET ignored_roles = ? WHERE guild_id = ?",
                    [roles, src.guild.id])
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description="Updated the ignored roles list.",
                                         fields=None,
                                         footer_text="Ignored roles are disqualified from gaining any experience.",
                                         status="success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @staticmethod
    async def level_multiplier(self, ctx, inter, level, multiplier, source):
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
        multiplier = float("{:.2f}".format(multiplier))
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
        if level > int(server_config["maximum_level"]):
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Level exceeds maximum for this server!",
                                             fields=None, footer_text=f"""The level you are attempting to edit exceeds \
the maximum level for this server ({server_config["maximum_level"]}).""", status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        if multiplier > 10:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Multiplier exceeds maximum supported!",
                                             fields=None, footer_text="The maximum supported level multiplier is 10.",
                                             status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        multipliers = json.loads(server_config["level_multipliers"])
        multipliers[level] = multiplier
        multipliers = json.dumps(multiplier, indent=2)
        try:
            con = sqlite3.connect("server_config.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        cur = con.cursor()
        cur.execute("UPDATE server_config SET level_multipliers = ? WHERE guild_id = ?",
                    [multipliers, src.guild.id])
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"""Updated the experience multiplier for \
level {level} to {multiplier}.""", fields=None,
                                         footer_text="A multiplier of 1 has no impact on the experience formula.",
                                         status="success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @staticmethod
    async def max_wiggle(self, ctx, inter, max_wiggle, source):
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
        max_wiggle = float("{:.2f}".format(max_wiggle))
        if max_wiggle > 5:  # TODO: Do I truly need error handling on all of these to make sure the numbers are
            # not negative?
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Maximum wiggle is too high!", fields=None,
                                             footer_text="The maximum maximum wiggle is 5.", status="alert")
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
        cur.execute("UPDATE server_config SET max_wiggle = ? WHERE guild_id = ?",
                    [max_wiggle, src.guild.id])
        con.commit()
        cur.execute("SELECT min_wiggle, max_wiggle FROM server_config WHERE guild_id = ?",
                    [src.guild.id])
        server_config = [dict(value) for value in cur.fetchall()][0]
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"Updated maximum wiggle to {max_wiggle}.",
                                         fields=None, footer_text=f"""Experience per message will be multiplied by \
between {server_config["minimum_wiggle"]} and {max_wiggle}. If both wiggles are 1, there is no wiggle.""",
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
    async def min_wiggle(self, ctx, inter, min_wiggle, source):
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
        min_wiggle = float("{:.2f}".format(min_wiggle))
        if min_wiggle > 5:  # TODO: Do I truly need error handling on all of these to make sure the numbers are
            # not negative?
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Minimum wiggle is too high!", fields=None,
                                             footer_text="The maximum minimum wiggle is 5.", status="alert")
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
        cur.execute("UPDATE server_config SET min_wiggle = ? WHERE guild_id = ?",
                    [min_wiggle, src.guild.id])
        con.commit()
        cur.execute("SELECT min_wiggle, max_wiggle FROM server_config WHERE guild_id = ?",
                    [src.guild.id])
        server_config = [dict(value) for value in cur.fetchall()][0]
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"Updated minimum wiggle to {min_wiggle}.",
                                         fields=None, footer_text=f"""Experience per message will be multiplied by \
between {min_wiggle} and {server_config["max_wiggle"]}. If both wiggles are 1, there is no wiggle.""",
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
    async def role_multiplier(self, ctx, inter, role, multiplier, source):
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
        if role.guild != src.guild:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="That is not a role in this server!",
                                             fields=None, footer_text="Please select a role from this server.",
                                             status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        if len(role.name) > 50:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Role name too long!",
                                             fields=None, footer_text="""For technical reasons, please only select \
roles with names that are less than 50 characters.""", status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        multiplier = float("{:.2f}".format(multiplier))
        if multiplier > 10:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Multiplier exceeds maximum supported!",
                                             fields=None, footer_text="The maximum supported role multiplier is 10.",
                                             status="alert")
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
        cur.execute("SELECT role_multipliers FROM server_config WHERE guild_id = ?", [src.guild.id])
        server_config = [dict(value) for value in cur.fetchall()][0]
        multipliers = json.loads(server_config["role_multipliers"])
        multipliers[f"{role.id}"] = multiplier
        multipliers = json.dumps(multiplier, indent=2)
        cur.execute("UPDATE server_config SET role_multipliers = ? WHERE guild_id = ?",
                    [multipliers, src.guild.id])
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"""Updated the experience multiplier for \
{role.name} to {multiplier}.""", fields=None,
                                         footer_text="A multiplier of 1 has no impact on the experience formula.",
                                         status="success")
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

    @commands.slash_command(name="base_percentage",
                            description="""Sets the base percentage of experience needed for the next level to grant \
per message.""", dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_guild=True)
    async def base_percentage_slash(self, inter, base_percentage: float):
        await self.base_percentage(self, ctx=None, inter=inter, base_percentage=base_percentage, source="slash")

    @commands.group(aliases=["percent"], brief="Set base percentage granted.",
                    help="Sets the base percentage of experience needed for the next level to grant per message.",
                    name="base_percentage", usage="base_percentage <#>")
    @commands.guild_only()
    async def base_percentage_message(self, ctx, base_percentage: float):
        await self.base_percentage(self, ctx=ctx, inter=None, base_percentage=base_percentage, source="message")

    @commands.slash_command(name="channel_multiplier",
                            description="Sets the experience multiplier for the specified channel.",
                            dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_guild=True)
    async def channel_multiplier_slash(self, inter, channel: disnake.TextChannel, multiplier: float):
        await self.channel_multiplier(self, ctx=None, inter=inter, channel=channel, multiplier=multiplier,
                                      source="slash")

    @commands.group(aliases=["chan_mult"], brief="Sets multiplier in channel.",
                    help="Sets the experience multiplier for the specified channel.",
                    name="channel_multiplier", usage="channel_multiplier <channel.Mention> <#>")
    @commands.guild_only()
    async def channel_multiplier_message(self, ctx, channel: disnake.TextChannel, multiplier: float):
        await self.channel_multiplier(self, ctx=ctx, inter=None, channel=channel, multiplier=multiplier,
                                      source="message")

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

    @commands.slash_command(name="ignore_channel",
                            description="Sets a channel to be disqualified from granting experience.",
                            dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_guild=True)
    async def ignore_channel_slash(self, inter, channel: disnake.TextChannel):
        await self.ignore_channel(self, ctx=None, inter=inter, channel=channel, source="slash")

    @commands.group(aliases=["x_chan"], brief="No experience from channel.",
                    help="Sets a channel to be disqualified from granting experience.",
                    name="ignore_channel", usage="ignore_channel <channel.Mention>")
    @commands.guild_only()
    async def ignore_channel_message(self, ctx, channel: disnake.TextChannel):
        await self.ignore_channel(self, ctx=ctx, inter=None, channel=channel, source="message")

    @commands.slash_command(name="ignore_role",
                            description="Sets a role to be disqualified from gaining experience.",
                            dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_guild=True)
    async def ignore_role_slash(self, inter, role: disnake.Role):
        await self.ignore_role(self, ctx=None, inter=inter, role=role, source="slash")

    @commands.group(aliases=["x_role"], brief="No experience for role.",
                    help="Sets a role to be disqualified from gaining experience.",
                    name="ignore_role", usage="ignore_role <role.Mention>")
    @commands.guild_only()
    async def ignore_role_message(self, ctx, role: disnake.Role):
        await self.ignore_role(self, ctx=ctx, inter=None, role=role, source="message")

    @commands.slash_command(name="level_multiplier",
                            description="Sets the experience multiplier for the specified level.",
                            dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_guild=True)
    async def level_multiplier_slash(self, inter, level: int, multiplier: float):
        await self.level_multiplier(self, ctx=None, inter=inter, level=level, multiplier=multiplier, source="slash")

    @commands.group(aliases=["lv_mult"], brief="Sets multiplier at level.",
                    help="Sets the experience multiplier for the specified level.",
                    name="level_multiplier", usage="level_multiplier <#> <#>")
    @commands.guild_only()
    async def level_multiplier_message(self, ctx, level: int, multiplier: float):
        await self.level_multiplier(self, ctx=ctx, inter=None, level=level, multiplier=multiplier, source="message")

    @commands.slash_command(name="max_wiggle",
                            description="""Sets the maximum random multiplier for experience granted on a message.""",
                            dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_guild=True)
    async def max_wiggle_slash(self, inter, max_wiggle: float):
        await self.max_wiggle(self, ctx=None, inter=inter, max_wiggle=max_wiggle, source="slash")

    @commands.group(aliases=["max_wig"], brief="Set maximum random multiplier.",
                    help="Sets the maximum random multiplier for experience granted on a message.",
                    name="max_wiggle", usage="max_wiggle <#>")
    @commands.guild_only()
    async def max_wiggle_message(self, ctx, max_wiggle: float):
        await self.max_wiggle(self, ctx=ctx, inter=None, max_wiggle=max_wiggle, source="message")

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

    @commands.slash_command(name="min_wiggle",
                            description="""Sets the minimum random multiplier for experience granted on a message.""",
                            dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_guild=True)
    async def min_wiggle_slash(self, inter, min_wiggle: float):
        await self.min_wiggle(self, ctx=None, inter=inter, min_wiggle=min_wiggle, source="slash")

    @commands.group(aliases=["min_wig"], brief="Set minimum random multiplier.",
                    help="Sets the minimum random multiplier for experience granted on a message.",
                    name="min_wiggle", usage="min_wiggle <#>")
    @commands.guild_only()
    async def min_wiggle_message(self, ctx, min_wiggle: float):
        await self.min_wiggle(self, ctx=ctx, inter=None, min_wiggle=min_wiggle, source="message")

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

    @commands.slash_command(name="role_multiplier",
                            description="Sets the experience multiplier for the specified role.",
                            dm_permission=False)
    @commands.guild_only()
    @commands.default_member_permissions(manage_guild=True)
    async def role_multiplier_slash(self, inter, role: disnake.Role, multiplier: float):
        await self.role_multiplier(self, ctx=None, inter=inter, role=role, multiplier=multiplier, source="slash")

    @commands.group(aliases=["role_mult"], brief="Sets multiplier for role.",
                    help="Sets the experience multiplier for the specified role.",
                    name="role_multiplier", usage="role_multiplier <role.Mention> <#>")
    @commands.guild_only()
    async def role_multiplier_message(self, ctx, role: disnake.Role, multiplier: float):
        await self.role_multiplier(self, ctx=ctx, inter=None, role=role, multiplier=multiplier, source="message")

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
