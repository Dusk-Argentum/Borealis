from cogs.functions import EmbedBuilder

import disnake
from disnake.ext import commands

import json

import sqlite3
from sqlite3 import OperationalError

import uuid


class ChannelSelection(disnake.ui.View):
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


class CharacterSelection(disnake.ui.View):
    selected = None

    def __init__(self, src, options):
        super().__init__(timeout=30)
        self.src = src
        self.character_selection.options = options

    async def interaction_check(self, inter: disnake.MessageInteraction):
        try:
            if inter.user.id != self.src.message.author.id:
                return
            return inter.user.id == self.src.message.author.id
        except AttributeError:
            if inter.user.id != self.src.author.id:
                return
            return inter.user.id == self.src.author.id

    @disnake.ui.string_select(placeholder="Select a character.", options=[], min_values=1, max_values=1)
    async def character_selection(self, select: disnake.ui.StringSelect, inter: disnake.MessageInteraction):
        CharacterSelection.selected = select.values[0]
        await inter.response.defer()
        self.stop()


class Characters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def active(self, ctx, inter, character_name, source):
        src = None
        if source == "slash":
            src = inter
        elif source == "message":
            src = ctx
        if character_name is not None and character_name[0].isupper() is False:
            character_name = character_name.capitalize()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description="Please wait.", fields=None,
                                         footer_text="Ideally, you should never see this.", status="waiting")
        response = await src.send(embed=EmbedBuilder.embed)
        if source == "slash":
            response = inter
            src.edit = inter.edit_original_response
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT character_name FROM characters WHERE player_id = ? AND guild_id = ?",
                    [src.author.id, src.guild.id])
        characters = [dict(value) for value in cur.fetchall()]
        con.close()
        if not characters:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None,
                                             description="You have no characters initialized on this server.",
                                             fields=None, footer_text="Please initialize a character, then try again.",
                                             status="unsure")
            await response.edit(embed=EmbedBuilder.embed)
            return
        character = None
        for character in characters:
            if character["character_name"] == character_name:
                break
        else:
            character_name = None
        if character_name is None:
            character_list = []
            for character in characters:
                character_list.append(character["character_name"])
            view = disnake.ui.View(timeout=30)
            selects = view.add_item(disnake.ui.StringSelect(placeholder="Select which character to modify.", options=[],
                                                            min_values=1, max_values=1))
            selects.children[0].add_option(label="None, cancel!", value="None, cancel!",
                                           description="This option will abort the modification process.")
            selects.children[0].add_option(label="Clear, please!", value="Clear, please!",
                                           description="This option will clear your ACTIVE character.")
            for name in character_list:
                selects.children[0].add_option(label=name, value=name,
                                               description=f"This option will modify {name}'s preferences.")
            view = CharacterSelection(src=src, options=selects.children[0].options)
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="""Please choose which character to modify\
, or cancel the modification process.""", fields=None,
                                             footer_text="""You may only have up to one character with the ACTIVE tag \
per server.""", status="waiting")
            await response.edit(embed=EmbedBuilder.embed, view=view)
            timeout = await view.wait()
            selected = CharacterSelection.selected
            if timeout:
                selected = "None, cancel!"
            if selected == "None, cancel!":
                await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None, description="Character modification aborted.",
                                                 fields=None, footer_text="Please feel free to try again.",
                                                 status="add_failure")
                await response.edit(embed=EmbedBuilder.embed, view=None)
                return
            if selected == "Clear, please!":
                try:
                    con = sqlite3.connect("characters.db", timeout=30.0)
                except OperationalError:
                    await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                     custom_title=None, description="Please try again in a moment.",
                                                     fields=None, footer_text="The database is busy.", status="failure")
                    await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                    return
                cur = con.cursor()
                cur.execute("""UPDATE characters SET active = 0 WHERE player_id = ? AND guild_id = ? AND \
active = 1""", [src.author.id, src.guild.id])
                con.commit()
                con.close()
                await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None, description=f"You have cleared the ACTIVE tag.",
                                                 fields=None,
                                                 footer_text="""Please feel free to designate a new character to have \
the ACTIVE tag.""", status="deletion")
                await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                return
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        cur = con.cursor()
        cur.execute("""UPDATE characters SET active = 0 WHERE player_id = ? AND guild_id = ? AND \
active = 1""", [src.author.id, src.guild.id])
        con.commit()
        cur.execute("""UPDATE characters SET active = 1 WHERE player_id = ? AND guild_id = ? AND \
character_name = ?""", [src.author.id, src.guild.id, character["character_name"]])
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None,
                                         description=f"{character['character_name']} now has the ACTIVE tag.",
                                         fields=None,
                                         footer_text="This grants +20 to the experience determination likelihood.",
                                         status="add_success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @staticmethod
    async def channel(self, ctx, inter, character_name, channel, source):
        src = None
        if source == "slash":
            src = inter
        elif source == "message":
            src = ctx
        if character_name is not None and character_name[0].isupper() is False:
            character_name = character_name.capitalize()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description="Please wait.", fields=None,
                                         footer_text="Ideally, you should never see this.", status="waiting")
        response = await src.send(embed=EmbedBuilder.embed)
        if source == "slash":
            response = inter
            src.edit = inter.edit_original_response
        if channel is None:
            channel = src.channel
        if channel.guild != src.guild:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="That is not a CHANNEL in this server!",
                                             fields=None, footer_text="Please select a CHANNEL from this server.",
                                             status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        if len(channel.name) > 50:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="CHANNEL name too long!",
                                             fields=None, footer_text="""For technical reasons, please only select \
CHANNELs with names that are less than 50 characters.""", status="waiting")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT character_name, channels FROM characters WHERE player_id = ? AND guild_id = ?",
                    [src.author.id, src.guild.id])
        characters = [dict(value) for value in cur.fetchall()]
        con.close()
        if not characters:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None,
                                             description="You have no characters initialized on this server.",
                                             fields=None, footer_text="Please initialize a character, then try again.",
                                             status="unsure")
            await response.edit(embed=EmbedBuilder.embed)
            return
        character = None
        for character in characters:
            if character["character_name"] == character_name:
                break
        else:
            character_name = None
        if character_name is None:
            character_list = []
            for character in characters:
                character_list.append(character["character_name"])
            view = disnake.ui.View(timeout=30)
            selects = view.add_item(disnake.ui.StringSelect(placeholder="Select which character to modify.", options=[],
                                                            min_values=1, max_values=1))
            selects.children[0].add_option(label="None, cancel!", value="None, cancel!",
                                           description="This option will abort the modification process.")
            for name in character_list:
                selects.children[0].add_option(label=name, value=name,
                                               description=f"This option will modify {name}'s preferences.")
            view = CharacterSelection(src=src, options=selects.children[0].options)
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="""Please choose which character to modify\
, or cancel the modification process.""", fields=None,
                                             footer_text="You may have up to ten CHANNELs per character.",
                                             status="waiting")
            await response.edit(embed=EmbedBuilder.embed, view=view)
            timeout = await view.wait()
            selected = CharacterSelection.selected
            if timeout:
                selected = "None, cancel!"
            if selected == "None, cancel!":
                await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None, description="Character modification aborted.",
                                                 fields=None, footer_text="Please feel free to try again.",
                                                 status="add_failure")
                await response.edit(embed=EmbedBuilder.embed, view=None)
                return
            for character in characters:
                if character["character_name"] == selected:
                    break
        for character_channels in characters:  # TODO: Unique unsetting command.
            for channel_entry in json.loads(character_channels["channels"]):
                if (channel.id == int(channel_entry)
                        and character_channels["character_name"] == character["character_name"]):
                    await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                     custom_title=None,
                                                     description=f"""Unassign {channel.mention} as a CHANNEL for \
{character["character_name"]}?""", fields=None, footer_text="You can also select other CHANNELs, if you wish.",
                                                     status="unsure")
                    channel_list = []
                    current_channel = disnake.utils.get(src.guild.channels, id=channel_entry)
                    for channel_id in json.loads(character["channels"]):
                        channel_resolve = disnake.utils.get(src.guild.channels, id=channel_id)
                        channel_list.append(channel_resolve)
                    view = disnake.ui.View(timeout=30)
                    selects = view.add_item(
                        disnake.ui.StringSelect(placeholder="Select which CHANNEL(s) to remove.", options=[],
                                                min_values=1, max_values=1))
                    selects.children[0].add_option(label="None, cancel!", value="None, cancel!",
                                                   description="This option will abort the modification process.")
                    selects.children[0].add_option(label=current_channel.name, value=current_channel.id,
                                                   description=f"""This option will remove {current_channel.name} \
from {character["character_name"]}'s list of CHANNELs.""")
                    for channel_in_list in channel_list:
                        if channel_in_list.id != current_channel.id:
                            selects.children[0].add_option(label=channel_in_list.name, value=channel_in_list.id,
                                                           description=f"""This option will remove \
{channel_in_list.name} from {character["character_name"]}'s list of CHANNELs.""")
                    view = ChannelSelection(src=src, options=selects.children[0].options, max_values=len(channel_list))
                    await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                     custom_title=None,
                                                     description=f"""Unassign {channel.mention} as a CHANNEL for \
{character["character_name"]}?""", fields=None,
                                                     footer_text="You can also select other CHANNELs, if you wish.",
                                                     status="unsure")
                    await response.edit(embed=EmbedBuilder.embed, view=view)
                    timeout = await view.wait()
                    selected = ChannelSelection.selected
                    if timeout:
                        selected = "None, cancel!"
                    if "None, cancel!" == selected[0] or "None, cancel!" == selected:
                        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                         custom_title=None,
                                                         description="Character modification aborted.",
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
                    try:
                        con = sqlite3.connect("characters.db", timeout=30.0)
                    except OperationalError:
                        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                         custom_title=None, description="Please try again in a moment.",
                                                         fields=None, footer_text="The database is busy.",
                                                         status="failure")
                        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                        return
                    cur = con.cursor()
                    cur.execute("""UPDATE characters SET channels = ? WHERE player_id = ? AND guild_id = ? AND \
character_name = ?""", [channels, src.author.id, src.guild.id, character["character_name"]])
                    con.commit()
                    con.close()
                    await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                     custom_title=None, description=f"""The selected CHANNEL(s) are no \
longer preferred CHANNEL(s) of {character["character_name"]}.""", fields=None,
                                                     footer_text="Please feel free to add more CHANNELs.",
                                                     status="deletion")
                    await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                    return
                elif channel.id == int(channel_entry):
                    await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                     custom_title=None,
                                                     description=f"""{channel.mention} is already a CHANNEL for \
{character_channels['character_name']}.""", fields=None,
                                                     footer_text="""To unset, try setting that CHANNEL again for that \
character.""", status="alert")
                    await response.edit(embed=EmbedBuilder.embed, view=None)
                    return
        if len(json.loads(character["channels"])) >= 10:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None,
                                             description=f"{character['character_name']} already has 10 CHANNELs!",
                                             fields=None,
                                             footer_text="You may have up to ten CHANNELs per character.",
                                             status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        channels = json.loads(character["channels"])
        channels.append(channel.id)
        channels = json.dumps(channels)
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        cur = con.cursor()
        cur.execute("""UPDATE characters SET channels = ? WHERE player_id = ? AND guild_id = ? AND \
character_name = ?""", [channels, src.author.id, src.guild.id, character["character_name"]])
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"""{channel.mention} is now a preferred \
CHANNEL of {character["character_name"]}.""", fields=None,
                                         footer_text="This grants +15 to the experience determination likelihood.",
                                         status="add_success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @staticmethod
    async def delete(self, ctx, inter, character_name, source):
        src = None
        if source == "slash":
            src = inter
        elif source == "message":
            src = ctx
        if character_name is not None and character_name[0].isupper() is False:
            character_name = character_name.capitalize()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description="Please wait.", fields=None,
                                         footer_text="Ideally, you should never see this.", status="waiting")
        response = await src.send(embed=EmbedBuilder.embed)
        if source == "slash":
            response = inter
            src.edit = inter.edit_original_response
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT character_name, experience FROM characters WHERE player_id = ? AND guild_id = ?",
                    [src.author.id, src.guild.id])
        characters = [dict(value) for value in cur.fetchall()]
        con.close()
        if not characters:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None,
                                             description="You have no characters initialized on this server.",
                                             fields=None, footer_text="Please initialize a character, then try again.",
                                             status="unsure")
            await response.edit(embed=EmbedBuilder.embed)
            return
        character = None
        for character in characters:
            if character["character_name"] == character_name:
                break
        else:
            character_name = None
        if character_name is None:
            character_list = []
            for character in characters:
                character_list.append(character["character_name"])
            view = disnake.ui.View(timeout=30)
            selects = view.add_item(disnake.ui.StringSelect(placeholder="Select which character to delete.", options=[],
                                                            min_values=1, max_values=1))
            selects.children[0].add_option(label="None, cancel!", value="None, cancel!",
                                           description="This option will abort the deletion process.")
            for name in character_list:
                selects.children[0].add_option(label=name, value=name,
                                               description=f"This option will PERMANENTLY delete {name}!")
            view = CharacterSelection(src=src, options=selects.children[0].options)
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="""Please choose which character to delete\
, or cancel the deletion process.""", fields=None, footer_text="This process cannot be undone.",
                                             status="waiting")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=view)  # This view disappeared immediately
            # one time. I cannot reliably reproduce the above glitch, but I... HOPE that it isn't what I think it is.
            timeout = await view.wait()
            selected = CharacterSelection.selected
            if timeout:
                selected = "None, cancel!"
            if selected == "None, cancel!":
                await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None, description="Character deletion aborted.",
                                                 fields=None, footer_text="Please feel free to try again.",
                                                 status="add_failure")
                await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                return
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        cur = con.cursor()
        cur.execute(f"DELETE FROM characters WHERE character_name = ? AND player_id = ? AND guild_id = ?",
                    [character["character_name"], src.author.id, src.guild.id])
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None,
                                         description=f"{character['character_name']} doesn't feel so good...",
                                         fields=None, footer_text="You are now free to initialize a new character.",
                                         status="deletion")
        experience = character["experience"]
        await response.edit(content=f"""-# Was this a mistake? {character["character_name"]} had \
{experience} experience.""", embed=EmbedBuilder.embed, view=None)

    @staticmethod
    async def dm(self, ctx, inter, character_name, source):  # This function does not have a check preventing non-DMs
        # from using it so that former DMs can force-unset their characters with the DM tag as a failsafe.
        src = None
        if source == "slash":
            src = inter
        elif source == "message":
            src = ctx
        if character_name is not None and character_name[0].isupper() is False:
            character_name = character_name.capitalize()
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
        cur.execute("SELECT dm_choose, dm_roles FROM server_config WHERE guild_id = ?", [src.guild.id])
        server_config = [dict(value) for value in cur.fetchall()][0]
        con.close()
        try:  # Character list checking has to go before the DM roles check to ensure that the UPDATE query in the
            # DM roles check never tries to operate on a user that does not have any characters.
            # It is a little deceptive to allow non-DM users to select a character before checking their role, but
            # it kind of makes sense.
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT character_name FROM characters WHERE player_id = ? AND guild_id = ?",
                    [src.author.id, src.guild.id])
        characters = [dict(value) for value in cur.fetchall()]
        con.close()
        if not characters:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None,
                                             description="You have no characters initialized on this server.",
                                             fields=None, footer_text="Please initialize a character, then try again.",
                                             status="unsure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        dm_roles = []
        for role in server_config["dm_roles"]:
            role = disnake.utils.get(src.guild.roles, id=role)
            dm_roles.append(role)
        for role in src.author.roles:
            for dm_role in dm_roles:
                if role.id == dm_role:
                    break
            else:
                try:
                    con = sqlite3.connect("characters.db", timeout=30.0)
                except OperationalError:
                    await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                     custom_title=None, description="Please try again in a moment.",
                                                     fields=None, footer_text="The database is busy.", status="failure")
                    await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                    return
                cur = con.cursor()
                cur.execute("UPDATE characters SET dm = 0 WHERE player_id = ? AND guild_id = ? AND dm = 1",
                            [src.author.id, src.guild.id])
                con.commit()
                con.close()
                await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None, description="You are not a DM!",
                                                 fields=None,
                                                 footer_text="""DM tag unset from all of your characters in this \
server as a failsafe.""", status="alert")
                await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                return
        character = None
        for character in characters:
            if character["character_name"] == character_name:
                break
        else:
            character_name = None
        if character_name is None:
            character_list = []
            for character in characters:
                character_list.append(character["character_name"])
            view = disnake.ui.View(timeout=30)
            selects = view.add_item(disnake.ui.StringSelect(placeholder="Select which character to modify.", options=[],
                                                            min_values=1, max_values=1))
            selects.children[0].add_option(label="None, cancel!", value="None, cancel!",
                                           description="This option will abort the modification process.")
            selects.children[0].add_option(label="Clear, please!", value="Clear, please!",
                                           description="This option will clear your DM character.")
            for name in character_list:
                selects.children[0].add_option(label=name, value=name,
                                               description=f"This option will modify {name}'s preferences.")
            view = CharacterSelection(src=src, options=selects.children[0].options)
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="""Please choose which character to modify\
, or cancel the modification process.""", fields=None,
                                             footer_text="""You may only have one character with the DM tag\
per server.""", status="waiting")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=view)
            timeout = await view.wait()
            selected = CharacterSelection.selected
            if timeout:
                selected = "None, cancel!"
            if selected == "None, cancel!":
                await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None, description="Character modification aborted.",
                                                 fields=None, footer_text="Please feel free to try again.",
                                                 status="add_failure")
                await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                return
            if selected == "Clear, please!":
                try:
                    con = sqlite3.connect("characters.db", timeout=30.0)
                except OperationalError:
                    await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                     custom_title=None, description="Please try again in a moment.",
                                                     fields=None, footer_text="The database is busy.", status="failure")
                    await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                    return
                cur = con.cursor()
                cur.execute("UPDATE characters SET dm = 0 WHERE player_id = ? AND guild_id = ? AND dm = 1",
                            [src.author.id, src.guild.id])
                con.commit()
                con.close()
                await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None, description=f"You have cleared the DM tag.",
                                                 fields=None,
                                                 footer_text="""Please feel free to designate a new character to have \
the DM tag.""", status="deletion")
                await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                return
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        cur = con.cursor()
        cur.execute("UPDATE characters SET dm = 0 WHERE player_id = ? AND guild_id = ? AND dm = 1",
                    [src.author.id, src.guild.id])
        con.commit()
        cur.execute("UPDATE characters SET dm = 1 WHERE character_name = ? AND player_id = ? AND guild_id = ?",
                    [character["character_name"], src.author.id, src.guild.id])
        con.commit()
        con.close()
        footer = ""
        if server_config["dm_choose"] == 0:
            footer = """The DM tag will have no effect on this server unless the DM Choose server configuration option \
is set to True by an administrator."""
        elif server_config["dm_choose"] == 1:
            footer = "This grants +50 to the experience determination likelihood."
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None,
                                         description=f"{character['character_name']} now has the DM tag.",
                                         fields=None,
                                         footer_text=footer,
                                         status="add_success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @staticmethod
    async def global_switch(self, ctx, inter, character_name, source):
        src = None
        if source == "slash":
            src = inter
        elif source == "message":
            src = ctx
        if character_name is not None and character_name[0].isupper() is False:
            character_name = character_name.capitalize()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description="Please wait.", fields=None,
                                         footer_text="Ideally, you should never see this.", status="waiting")
        response = await src.send(embed=EmbedBuilder.embed)
        if source == "slash":
            response = inter
            src.edit = inter.edit_original_response
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT character_name FROM characters WHERE player_id = ? AND guild_id = ?",
                    [src.author.id, src.guild.id])
        characters = [dict(value) for value in cur.fetchall()]
        con.close()
        if not characters:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None,
                                             description="You have no characters initialized on this server.",
                                             fields=None, footer_text="Please initialize a character, then try again.",
                                             status="unsure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        character = None
        for character in characters:
            if character["character_name"] == character_name:
                break
        else:
            character_name = None
        if character_name is None:
            character_list = []
            for character in characters:
                character_list.append(character["character_name"])
            view = disnake.ui.View(timeout=30)
            selects = view.add_item(disnake.ui.StringSelect(placeholder="Select which character to modify.", options=[],
                                                            min_values=1, max_values=1))
            selects.children[0].add_option(label="None, cancel!", value="None, cancel!",
                                           description="This option will abort the modification process.")
            for name in character_list:
                selects.children[0].add_option(label=name, value=name,
                                               description=f"This option will modify {name}'s preferences.")
            view = CharacterSelection(src=src, options=selects.children[0].options)
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="""Please choose which character to modify\
, or cancel the modification process.""", fields=None,
                                             footer_text="""You may only have one character with the GLOBAL tag\
per server.""", status="waiting")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=view)
            timeout = await view.wait()
            selected = CharacterSelection.selected
            if timeout:
                selected = "None, cancel!"
            if selected == "None, cancel!":
                await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None, description="Character modification aborted.",
                                                 fields=None, footer_text="Please feel free to try again.",
                                                 status="add_failure")
                await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                return
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        cur = con.cursor()
        cur.execute("UPDATE characters SET global = 0 WHERE player_id = ? AND guild_id = ? AND global = 1",
                    [src.author.id, src.guild.id])
        con.commit()
        cur.execute("UPDATE characters SET global = 1 WHERE character_name = ? AND player_id = ? AND guild_id = ?",
                    [character["character_name"], src.author.id, src.guild.id])
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None,
                                         description=f"{character['character_name']} now has the GLOBAL tag.",
                                         fields=None,
                                         footer_text="This grants +1 to the experience determination likelihood.",
                                         status="add_success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @staticmethod
    async def initialize(self, ctx, inter, character_name, source):
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
        if character_name is None:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None,
                                             description="You have not specified a NAME for your character!",
                                             fields=None,
                                             footer_text="Please choose a NAME that is 32 characters long or less.",
                                             status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        if character_name[0].isupper() is False:
            character_name = character_name.capitalize()
        if len(character_name) > 32:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None,
                                             description="Your NAME is too long!",
                                             fields=None,
                                             footer_text="Please choose a NAME that is 32 characters long or less.",
                                             status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        banned_names = ["Clear, please!", "None, cancel!"]
        for banned_name in banned_names:
            if character_name == banned_name:
                ass = "https://cdn.discordapp.com/attachments/1291623487990927411/1291664640106958898/\
no_doubles.png?ex=6700ebf0&is=66ff9a70&hm=63351b38b949988071696502b0f101edca7f022dcb6e733dc2eebf3243f386f1&"
                await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=disnake.Color(0x5e0606),
                                                 custom_thumbnail=ass,
                                                 custom_title="Oops!",
                                                 description="Your NAME sucks ass!",
                                                 fields=None,
                                                 footer_text="Please choose a NAME that does not suck ass.",
                                                 status=None)
                await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                return
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT character_name FROM characters WHERE player_id = ? AND guild_id = ?",
                    [src.author.id, src.guild.id])
        characters = [dict(value) for value in cur.fetchall()]
        con.close()
        for character in characters:
            if character["character_name"] == character_name:
                await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None,
                                                 description="""You already have a character on this server with that \
NAME!""", fields=None, footer_text="Please choose a unique NAME.", status="alert")
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
        cur.execute("""SELECT character_limit, starting_level, experience_thresholds, tier_thresholds \
FROM server_config WHERE guild_id = ?""", [src.guild.id])
        server_config = [dict(value) for value in cur.fetchall()][0]
        con.close()
        if len(characters) >= int(server_config["character_limit"]):
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="You have reached the character cap!",
                                             fields=None,
                                             footer_text="""Please choose which character to delete\
, or cancel the deletion process.""", status="alert")
            view = disnake.ui.View(timeout=30)
            selects = view.add_item(disnake.ui.StringSelect(placeholder="Select which character to delete.", options=[],
                                                            min_values=1, max_values=1))
            selects.children[0].add_option(label="None, cancel!", value="None, cancel!",
                                           description="This option will abort the initialization process.")
            for character in characters:
                selects.children[0].add_option(label=character["character_name"], value=character["character_name"],
                                               description=f"""This option will PERMANENTLY delete \
{character["character_name"]}!""")
            view = CharacterSelection(src=src, options=selects.children[0].options)
            await response.edit(content=None, embed=EmbedBuilder.embed, view=view)
            timeout = await view.wait()
            selected = CharacterSelection.selected
            if timeout:
                selected = "None, cancel!"
            if selected == "None, cancel!":
                await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None, description="Character initialization aborted.",
                                                 fields=None, footer_text="Please feel free to try again.",
                                                 status="add_failure")
                await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                return
            try:
                con = sqlite3.connect("characters.db", timeout=30)
            except OperationalError:
                await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None, description="Please try again in a moment.",
                                                 fields=None, footer_text="The database is busy.", status="failure")
                await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                return
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("""SELECT experience FROM characters WHERE character_name = ? AND player_id = ? AND \
guild_id = ?""", [selected, src.author.id, src.guild.id])
            experience = [dict(value) for value in cur.fetchall()][0]
            cur.execute("DELETE FROM characters WHERE character_name = ? AND player_id = ? AND guild_id = ?",
                        [selected, src.author.id, src.guild.id])
            con.commit()
            con.close()
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description=f"{selected} doesn't feel so good...",
                                             fields=None,
                                             footer_text="Your new character will be initialized in a moment.",
                                             status="deletion")
            await response.edit(content=f"-# Was this a mistake? {selected} had {experience["experience"]} experience.",
                                embed=EmbedBuilder.embed, view=None)
        character_id = uuid.uuid4()
        starting_experience = 1
        for level, minimum in json.loads(server_config["experience_thresholds"]).items():
            if int(server_config["starting_level"]) == int(level):
                starting_experience = int(minimum)
                break
        starting_tier = 1
        for tier, threshold in json.loads(server_config["tier_thresholds"]).items():
            if threshold <= int(server_config["starting_level"]):
                starting_tier = int(tier)
        global_switch = 1
        if len(characters) > 0:
            global_switch = 0
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        cur = con.cursor()
        cur.execute("""INSERT INTO characters VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, 0, 0, "[]", "[]")""",
                    [str(character_id), str(character_name), src.author.id, src.guild.id,
                     starting_experience, server_config["starting_level"], starting_tier, global_switch])
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description="Character initialized!",
                                         fields=None, footer_text=f"Enjoy playing with {character_name}!",
                                         status="add_success")
        await response.edit(embed=EmbedBuilder.embed, view=None)  # Content is not None so that experience lingers.

    @staticmethod
    async def nick(self, ctx, inter, character_name, character_nick, source):
        src = None
        if source == "slash":
            src = inter
        elif source == "message":
            src = ctx
        if character_name is not None and character_name[0].isupper() is False:
            character_name = character_name.capitalize()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description="Please wait.", fields=None,
                                         footer_text="Ideally, you should never see this.", status="waiting")
        response = await src.send(embed=EmbedBuilder.embed)
        if source == "slash":
            response = inter
            src.edit = inter.edit_original_response
        if character_nick is None:
            character_nick = "Nicholasname"
        if len(character_nick) > 32:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None,
                                             description="Your NICK is too long!",
                                             fields=None,
                                             footer_text="Please choose a NICK that is 32 characters long or less.",
                                             status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT character_name, nicks FROM characters WHERE player_id = ? AND guild_id = ?",
                    [src.author.id, src.guild.id])
        characters = [dict(value) for value in cur.fetchall()]
        con.close()
        if not characters:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None,
                                             description="You have no characters initialized on this server.",
                                             fields=None, footer_text="Please initialize a character, then try again.",
                                             status="unsure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        character = None
        for character in characters:
            if character["character_name"] == character_name:
                break
        else:
            character_name = None
        if character_name is None:
            character_list = []
            for character in characters:
                character_list.append(character["character_name"])
            view = disnake.ui.View(timeout=30)
            selects = view.add_item(disnake.ui.StringSelect(placeholder="Select which character to modify.", options=[],
                                                            min_values=1, max_values=1))
            selects.children[0].add_option(label="None, cancel!", value="None, cancel!",
                                           description="This option will abort the modification process.")
            for name in character_list:
                selects.children[0].add_option(label=name, value=name,
                                               description=f"This option will modify {name}'s preferences.")
            view = CharacterSelection(src=src, options=selects.children[0].options)
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="""Please choose which character to modify\
, or cancel the modification process.""", fields=None,
                                             footer_text="You may have up to three NICKs per character.",
                                             status="waiting")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=view)
            timeout = await view.wait()
            selected = CharacterSelection.selected
            if timeout:
                selected = "None, cancel!"
            if selected == "None, cancel!":
                await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None, description="Character modification aborted.",
                                                 fields=None, footer_text="Please feel free to try again.",
                                                 status="add_failure")
                await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                return
            for character in characters:
                if character["character_name"] == selected:
                    break
        for character_nicks in characters:  # TODO: Unique unsetting command.
            for nick_entry in json.loads(character_nicks["nicks"]):
                if (character_nick == nick_entry
                        and character_nicks["character_name"] == character["character_name"]):
                    await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                     custom_title=None,
                                                     description=f"""Unassign {character_nick} as a NICK for \
{character["character_name"]}?""", fields=None, footer_text="You can also select other NICKs, if you wish.",
                                                     status="unsure")
                    nick_list = []
                    for nick_name in json.loads(character["nicks"]):
                        nick_list.append(nick_name)
                    view = disnake.ui.View(timeout=30)
                    selects = view.add_item(
                        disnake.ui.StringSelect(placeholder="Select which NICK(s) to remove.", options=[],
                                                min_values=1, max_values=1))
                    selects.children[0].add_option(label="None, cancel!", value="None, cancel!",
                                                   description="This option will abort the modification process.")
                    selects.children[0].add_option(label=character_nick, value=character_nick,
                                                   description=f"""This option will remove {character_nick} \
from {character["character_name"]}'s list of NICKs.""")
                    for nick_in_list in nick_list:
                        if nick_in_list != character_nick:
                            selects.children[0].add_option(label=nick_in_list, value=nick_in_list,
                                                           description=f"""This option will remove \
{nick_in_list} from {character["character_name"]}'s list of NICKs.""")
                    view = ChannelSelection(src=src, options=selects.children[0].options,
                                            max_values=len(nick_list))
                    await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                     custom_title=None,
                                                     description=f"""Unassign {character_nick} as a NICK for \
{character["character_name"]}?""", fields=None, footer_text="You can also select other NICKs, if you wish.",
                                                        status="unsure")
                    await response.edit(content=None, embed=EmbedBuilder.embed, view=view)
                    timeout = await view.wait()
                    selected = ChannelSelection.selected
                    if timeout:
                        selected = "None, cancel!"
                    if "None, cancel!" == selected[0] or "None, cancel!" == selected:
                        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None,
                                                         custom_thumbnail=None,
                                                         custom_title=None,
                                                         description="Character modification aborted.",
                                                         fields=None, footer_text="Please feel free to try again.",
                                                         status="add_failure")
                        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                        return
                    for entry in selected:
                        nick_list.remove(entry)
                    nicks = []
                    for entry in nick_list:
                        nicks.append(entry)
                    nicks = json.dumps(nicks)
                    try:
                        con = sqlite3.connect("characters.db", timeout=30.0)
                    except OperationalError:
                        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None,
                                                         custom_thumbnail=None,
                                                         custom_title=None,
                                                         description="Please try again in a moment.",
                                                         fields=None, footer_text="The database is busy.",
                                                         status="failure")
                        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                        return
                    cur = con.cursor()
                    cur.execute("""UPDATE characters SET nicks = ? WHERE player_id = ? AND guild_id = ? AND \
character_name = ?""", [nicks, src.author.id, src.guild.id, character["character_name"]])
                    con.commit()
                    con.close()
                    await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                     custom_title=None, description=f"""The selected NICK(s) are \
no longer NICK(s) of {character["character_name"]}.""", fields=None,
                                                     footer_text="Please feel free to add more NICKs.",
                                                     status="deletion")
                    await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                    return
                elif character_nick == nick_entry:
                    await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                                     custom_title=None,
                                                     description=f"""{character_nick} is already a NICK for \
{character_nicks['character_name']}.""", fields=None, footer_text="""To unset, try setting that NICK again for that \
character.""", status="alert")
                    await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                    return
        if len(json.loads(character["nicks"])) >= 3:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None,
                                             description=f"{character['character_name']} already has 3 NICKs!",
                                             fields=None,
                                             footer_text="You may have up to ten NICKs per character.",
                                             status="alert")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        nicks = json.loads(character["nicks"])
        nicks.append(character_nick)
        nicks = json.dumps(nicks)
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        cur = con.cursor()
        cur.execute("""UPDATE characters SET nicks = ? WHERE player_id = ? AND guild_id = ? AND \
character_name = ?""", [nicks, src.author.id, src.guild.id, character["character_name"]])
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=src, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"""{character_nick} is now a NICK of \
{character["character_name"]}.""", fields=None, footer_text="""This grants +4 to the experience determination \
likelihood.""", status="add_success")
        await response.edit(content=None, embed=EmbedBuilder.embed, view=None)

    @commands.slash_command(name="active", description="Gives a character the ACTIVE tag.", dm_permission=False)
    @commands.guild_only()
    async def active_slash(self, inter, character_name: str = None):
        await self.active(self, ctx=None, inter=inter, character_name=character_name, source="slash")

    @commands.slash_command(name="channel", description="Sets a CHANNEL as a character's preferred CHANNEL.",
                            dm_permission=False)
    @commands.guild_only()
    async def channel_slash(self, inter, character_name: str = None,
                            channel: disnake.TextChannel | disnake.ForumChannel = None):
        await self.channel(self, ctx=None, inter=inter, character_name=character_name, channel=channel, source="slash")

    @commands.slash_command(name="delete", description="Deletes a character.", dm_permission=False)
    @commands.guild_only()
    async def delete_slash(self, inter, character_name: str = None):
        await self.delete(self, ctx=None, inter=inter, character_name=character_name, source="slash")

    @commands.slash_command(name="dm", description="Gives a character the DM tag.", dm_permission=False)
    @commands.guild_only()
    async def dm_slash(self, inter, character_name: str = None):
        await self.dm(self, ctx=None, inter=inter, character_name=character_name, source="slash")

    @commands.slash_command(name="global", description="Gives a character the GLOBAL tag.", dm_permission=False)
    @commands.guild_only()
    async def global_slash(self, inter, character_name: str = None):
        await self.global_switch(self, ctx=None, inter=inter, character_name=character_name, source="slash")

    @commands.slash_command(name="initialize", description="Initializes a character.", dm_permission=False)
    @commands.guild_only()
    async def initialize_slash(self, inter, character_name: str):
        await self.initialize(self, ctx=None, inter=inter, character_name=character_name, source="slash")

    @commands.slash_command(name="nick", description="Grants a NICK to a character.", dm_permission=False)
    @commands.guild_only()
    async def nick_slash(self, inter, character_name: str = None, character_nick: str = None):
        await self.nick(self, ctx=None, inter=inter, character_name=character_name, character_nick=character_nick,
                        source="slash")

    @commands.command(aliases=["a"], brief="Grants ACTIVE to a character.",
                      help="Grants the ACTIVE tag to a selected character.", name="active", usage="active [name]")
    @commands.guild_only()
    async def active_message(self, ctx, *, character_name: str = None):
        await self.active(self, ctx=ctx, inter=None, character_name=character_name, source="message")

    @commands.command(aliases=["c"], brief="Sets preferred CHANNEL for a character.",
                      help="Sets the mentioned CHANNEL as preferred for the selected character.", name="channel",
                      usage="""channel "[name]" [channel.Mention]""")
    @commands.guild_only()
    # TODO: on_error handling for ChannelNotFound raised when using a channel from another server/invalid channel.
    async def channel_message(self, ctx, character_name: str = None,
                              channel: disnake.TextChannel | disnake.ForumChannel = None):
        await self.channel(self, ctx=ctx, inter=None, character_name=character_name, channel=channel, source="message")

    @commands.command(aliases=["d"], brief="Deletes a character.", help="Deletes a selected character.",
                      name="delete", usage="delete [name]")
    @commands.guild_only()
    async def delete_message(self, ctx, *, character_name: str = None):
        await self.delete(self, ctx=ctx, inter=None, character_name=character_name, source="message")

    @commands.command(aliases=["dungeonmaster"], brief="Grants DM to a character.",
                      help="Grants the DM tag to a selected character.", name="dm", usage="dm [name]")
    async def dm_message(self, ctx, *, character_name: str = None):
        await self.dm(self, ctx=ctx, inter=None, character_name=character_name, source="message")

    @commands.command(aliases=["g"], brief="Grants GLOBAL to a character.",
                      help="Grants the GLOBAL tag to a selected character.", name="global", usage="global [name]")
    @commands.guild_only()
    async def global_message(self, ctx, *, character_name: str = None):
        await self.global_switch(self, ctx=ctx, inter=None, character_name=character_name, source="message")

    @commands.command(aliases=["i"], brief="Initializes a character.",
                      help="Initializes a newly created character.", name="initialize", usage="initialize <name>")
    @commands.guild_only()
    async def initialize_message(self, ctx, *, character_name: str = None):
        await self.initialize(self, ctx=ctx, inter=None, character_name=character_name, source="message")

    @commands.command(aliases=["n"], brief="Grants a NICK to a character.",
                      help="Grants a NICK name to a selected character.", name="nick", usage="nick [name] [nick]")
    async def nick_message(self, ctx, character_name: str = None, character_nick: str = None):
        await self.nick(self, ctx=ctx, inter=None, character_name=character_name, character_nick=character_nick,
                        source="message")


def setup(bot):
    bot.add_cog(Characters(bot))
