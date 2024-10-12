import disnake
from disnake.ext import commands

from cogs.functions import EmbedBuilder

import json

import sqlite3
from sqlite3 import OperationalError

import uuid


class DeletionSelection(disnake.ui.View):
    selected = None

    def __init__(self, ctx, options):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.character_selection.options = options

    async def interaction_check(self, inter: disnake.MessageInteraction):
        if inter.user.id != self.ctx.message.author.id:
            return
        return inter.user.id == self.ctx.message.author.id

    @disnake.ui.string_select(placeholder="Delete a character?", options=[], min_values=1, max_values=1)
    async def character_selection(self, select: disnake.ui.StringSelect, inter: disnake.MessageInteraction):
        DeletionSelection.selected = select.values[0]
        await inter.response.defer()
        self.stop()


class Characters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["d"], brief="Deletes a character.", help="Deletes a selected character.",
                      name="delete", usage="delete [name]")
    @commands.guild_only()
    async def delete(self, ctx, *, character_name: str = None):
        if character_name is not None and character_name[0].isupper() is False:
            character_name = character_name.capitalize()
        await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description="Please wait.", fields=None,
                                         footer_text="Ideally, you should never see this.", status="waiting")
        response = await ctx.send(embed=EmbedBuilder.embed)
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM characters WHERE player_id = ? AND guild_id = ?",
                    [ctx.author.id, ctx.guild.id])
        characters = [dict(value) for value in cur.fetchall()]
        character = {}
        con.close()
        if not characters:
            await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                             custom_title=None,
                                             description="You have no characters initialized on this server.",
                                             fields=None, footer_text="Please initialize a character, then try again.",
                                             status="unsure")
            await response.edit(embed=EmbedBuilder.embed)
            return
        selected = None  # This needs to be here so there isn't a variable out-of-scope error later on.
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
            view = DeletionSelection(ctx=ctx, options=selects.children[0].options)
            await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="""Please choose which character to delete\
, or cancel the deletion process.""", fields=None, footer_text="This process cannot be undone.", status="waiting")
            await response.edit(embed=EmbedBuilder.embed, view=view)  # This view disappeared immediately once.
            # I cannot reliably reproduce the above glitch, but I... HOPE that it isn't what I think it is.
            timeout = await view.wait()
            selected = DeletionSelection.selected
            if timeout:
                selected = "None, cancel!"
            if selected == "None, cancel!":
                await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None, description="Character deletion aborted.",
                                                 fields=None, footer_text="Please feel free to try again.",
                                                 status="add_failure")
                await response.edit(embed=EmbedBuilder.embed, view=None)
                return
        elif character_name is not None:
            selected = character_name
        for character in characters:
            if character["character_name"] == selected:
                break
        if not character:
            await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                             custom_title=None,
                                             description=f"You have no character named {selected}!",
                                             fields=None, footer_text="Feel free to try again.", status="unsure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        experience = character["experience"]
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        cur = con.cursor()
        cur.execute(f"DELETE FROM characters WHERE character_name = ? AND player_id = ? AND guild_id = ?",
                    [selected, ctx.author.id, ctx.guild.id])
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description=f"{selected} doesn't feel so good...",
                                         fields=None, footer_text="You are now free to initialize a new character.",
                                         status="deletion")
        await response.edit(content=f"-# Was this a mistake? {selected} had {experience} experience.",
                            embed=EmbedBuilder.embed, view=None)
        return

    @commands.command(aliases=["i"], brief="Initializes a character.",
                      help="Initializes a newly created character.", name="initialize", usage="initialize <name>")
    @commands.guild_only()
    async def initialize(self, ctx, *, character_name: str = None):
        await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description="Please wait.", fields=None,
                                         footer_text="Ideally, you should never see this.", status="waiting")
        response = await ctx.send(embed=EmbedBuilder.embed)
        if character_name is None:
            await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                             custom_title=None,
                                             description="You have not specified a name for your character!",
                                             fields=None,
                                             footer_text="Please choose a name that is 32 characters long or less.",
                                             status="alert")
            await response.edit(embed=EmbedBuilder.embed)
            return
        if character_name[0].isupper() is False:
            character_name = character_name.capitalize()
        if len(character_name) > 32:
            await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                             custom_title=None,
                                             description="Your name is too long!",
                                             fields=None,
                                             footer_text="Please choose a name that is 32 characters long or less.",
                                             status="alert")
            await response.edit(embed=EmbedBuilder.embed)
            return
        if character_name == "None, cancel!":
            ass = "https://cdn.discordapp.com/attachments/1291623487990927411/1291664640106958898/\
no_doubles.png?ex=6700ebf0&is=66ff9a70&hm=63351b38b949988071696502b0f101edca7f022dcb6e733dc2eebf3243f386f1&"
            await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=disnake.Color(0x5e0606),
                                             custom_thumbnail=ass,
                                             custom_title="Oops!",
                                             description="Your name sucks ass!",
                                             fields=None,
                                             footer_text="Please choose a name that does not suck ass.",
                                             status=None)
            await response.edit(embed=EmbedBuilder.embed)
            return
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM characters WHERE player_id = ? AND guild_id = ?",
                    [ctx.author.id, ctx.guild.id])
        characters = [dict(value) for value in cur.fetchall()]
        con.close()
        for character in characters:
            if character["character_name"] == character_name:
                await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None,
                                                 description="""You already have a character on this server with that \
name!""", fields=None, footer_text="Please choose a unique name.", status="alert")
                await response.edit(embed=EmbedBuilder.embed)
                return
        try:
            con = sqlite3.connect("server_config.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM server_config WHERE guild_id = ?", [ctx.guild.id])
        server_config = [dict(value) for value in cur.fetchall()][0]  # TODO: Make queries more specific.
        con.close()
        if len(characters) >= int(server_config["character_limit"]):  # This is cast to int even though it already IS
            # one because, of course, PyCharm complains if I don't.
            await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="You have reached the character cap!",
                                             fields=None,
                                             footer_text="""Please choose which character to delete\
, or cancel the deletion process.""", status="alert")
            await response.edit(embed=EmbedBuilder.embed)
            view = disnake.ui.View(timeout=30)
            selects = view.add_item(disnake.ui.StringSelect(placeholder="Select which character to delete.", options=[],
                                                            min_values=1, max_values=1))
            selects.children[0].add_option(label="None, cancel!", value="None, cancel!",
                                           description="This option will abort the initialization process.")
            for character in characters:
                selects.children[0].add_option(label=character["character_name"], value=character["character_name"],
                                               description=f"""This option will PERMANENTLY delete \
{character["character_name"]}!""")
            view = DeletionSelection(ctx=ctx, options=selects.children[0].options)
            await response.edit(view=view)
            timeout = await view.wait()
            selected = DeletionSelection.selected
            if timeout:
                selected = "None, cancel!"
            if selected == "None, cancel!":
                await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None, description="Character initialization aborted.",
                                                 fields=None, footer_text="Please feel free to try again.",
                                                 status="add_failure")
                await response.edit(embed=EmbedBuilder.embed, view=None)
                return
            try:
                con = sqlite3.connect("characters.db", timeout=30)
            except OperationalError:
                await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None, description="Please try again in a moment.",
                                                 fields=None, footer_text="The database is busy.", status="failure")
                await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
                return
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("""SELECT experience FROM characters WHERE character_name = ? AND player_id = ? AND \
guild_id = ?""", [selected, ctx.author.id, ctx.guild.id])
            experience = [dict(value) for value in cur.fetchall()][0]
            cur.execute("DELETE FROM characters WHERE character_name = ? AND player_id = ? AND guild_id = ?",
                        [selected, ctx.author.id, ctx.guild.id])
            con.commit()
            con.close()
            await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description=f"{selected} doesn't feel so good...",
                                             fields=None,
                                             footer_text="Your new character will be initialized in a moment.",
                                             status="deletion")
            await response.edit(content=f"-# Was this a mistake? {selected} had {experience["experience"]} experience.",
                                embed=EmbedBuilder.embed, view=None)
        character_id = uuid.uuid4()
        starting_experience = 6500
        for level, minimum in json.loads(server_config["experience_curve"]).items():
            if int(server_config["starting_level"]) == level:
                starting_experience = int(minimum)
                break
        starting_tier = 2
        for tier, threshold in json.loads(server_config["tier_thresholds"]).items():
            if int(server_config["starting_level"]) > int(threshold):
                starting_tier = int(tier)
        global_switch = 1
        if len(characters) == [0, 1]:
            global_switch = 0
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                             custom_title=None, description="Please try again in a moment.",
                                             fields=None, footer_text="The database is busy.", status="failure")
            await response.edit(content=None, embed=EmbedBuilder.embed, view=None)
            return
        cur = con.cursor()
        cur.execute("""INSERT INTO characters VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, 0, 0, "[]", "[]")""",
                    [str(character_id), str(character_name), ctx.author.id, ctx.guild.id, starting_experience,
                        server_config["starting_level"], starting_tier, global_switch])
        con.commit()
        con.close()
        await EmbedBuilder.embed_builder(self=self, ctx=ctx, custom_color=None, custom_thumbnail=None,
                                         custom_title=None, description="Character initialized!",
                                         fields=None, footer_text=f"Enjoy playing with {character_name}!",
                                         status="add_success")
        await response.edit(embed=EmbedBuilder.embed)


def setup(bot):
    bot.add_cog(Characters(bot))
