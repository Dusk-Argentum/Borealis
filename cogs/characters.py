import disnake
from disnake import MessageInteraction
from disnake.ext import commands

from bot import GUILD, PREFIX

import sqlite3
from sqlite3 import OperationalError

import uuid

import re

import json


class DeletionSelection(disnake.ui.View):
    forward = None

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
        DeletionSelection.forward = select.values[0]
        await inter.response.defer()
        self.stop()


class Characters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["d"], brief="Deletes your character.", help="Deletes a selected character.",
                      name="delete", usage="delete [name]")
    @commands.guild_only()
    async def delete(self, ctx, *, character_name: str = None):
        embed = disnake.Embed(color=disnake.Color(0xe07e22), description="Verifying your character...",
                              title="Please wait...")
        embed.set_author(
            icon_url=ctx.author.avatar.url if ctx.author.guild_avatar is None else ctx.author.guild_avatar.url,
            name=ctx.author.nick)
        embed.set_footer(icon_url=ctx.guild.icon.url, text=f"Ideally, you should never see this. | {ctx.guild.name}")
        embed.set_thumbnail(url="https://bg3.wiki/w/images/thumb/5/5f/Slow.webp/380px-Slow.webp.png")
        response = await ctx.send(embed=embed)
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await response.edit(content="Please try again in a moment.", embed=None, view=None)
            return
        cur = con.cursor()
        search = f"SELECT * from characters WHERE player_id = ?"
        player_id = [ctx.author.id]
        cur.execute(search, player_id)
        fetch = cur.fetchall()
        con.close()
        print("a")
        if not fetch:
            print("b")
            embed = disnake.Embed(color=disnake.Color(0xe07e22), description="You have no characters initialized.",
                                  title="Oops!")
            embed.set_author(
                icon_url=ctx.author.avatar.url if ctx.author.guild_avatar is None else ctx.author.guild_avatar.url,
                name=ctx.author.nick)
            embed.set_footer(icon_url=ctx.guild.icon.url,
                             text=f"Please initialize a character, then try again. | {ctx.guild.name}")
            embed.set_thumbnail(url="https://bg3.wiki/w/images/thumb/0/0a/Confusion.webp/380px-Confusion.webp.png")
            await response.edit(embed=embed)
            return
        forward = None
        if character_name is None:
            try:
                con = sqlite3.connect("characters.db", timeout=30.0)
            except OperationalError:
                await response.edit(content="Please try again in a moment.", embed=None, view=None)
                return
            cur = con.cursor()
            search = f"SELECT character_name FROM characters WHERE player_id = ?"
            player_id = [ctx.author.id]
            cur.execute(search, player_id)
            results = cur.fetchall()
            con.close()
            characters = []
            for name in results:
                for result in name:
                    characters.append(result)
            view = disnake.ui.View(timeout=30)
            selects = view.add_item(disnake.ui.StringSelect(placeholder="Select which character to delete.", options=[],
                                                            min_values=1, max_values=1))
            selects.children[0].add_option(label="None, cancel!", value="None, cancel!",
                                           description="This option will abort the initialization process.")
            for character in characters:
                selects.children[0].add_option(label=character, value=character,
                                               description=f"This option will PERMANENTLY delete {character}!")
            view = DeletionSelection(ctx=ctx, options=selects.children[0].options)
            await response.edit(view=view)
            timeout = await view.wait()
            if timeout:
                embed = disnake.Embed(color=(disnake.Color(0x991509)), description="Character initialization aborted!",
                                      title="Oops.")
                embed.set_author(
                    icon_url=(ctx.author.avatar.url if ctx.author.guild_avatar is None else
                              ctx.author.guild_avater.url), name=ctx.author.nick)
                embed.set_footer(icon_url=ctx.guild.icon.url,
                                 text=f"Please feel free to try again. | {ctx.guild.name}")
                embed.set_thumbnail(
                    url="https://bg3.wiki/w/images/thumb/3/3f/Bane_Spell.webp/380px-Bane_Spell.webp.png")
                await response.edit(content=None, embed=embed, view=None)
                return
            forward = DeletionSelection.forward
            if forward == "None, cancel!":
                embed = disnake.Embed(color=(disnake.Color(0x991509)), description="Character initialization aborted!",
                                      title="Oops.")
                embed.set_author(
                    icon_url=(ctx.author.avatar.url if ctx.author.guild_avatar is None else
                              ctx.author.guild_avater.url), name=ctx.author.nick)
                embed.set_footer(icon_url=ctx.guild.icon.url,
                                 text=f"Please feel free to try again. | {ctx.guild.name}")
                embed.set_thumbnail(
                    url="https://bg3.wiki/w/images/thumb/3/3f/Bane_Spell.webp/380px-Bane_Spell.webp.png")
                await response.edit(embed=embed, view=None)
                return
        elif character_name is not None:
            forward = character_name
        try:
            con = sqlite3.connect("characters.db", timeout=30)
        except OperationalError:
            await response.edit(content="Please try again in a moment.", embed=None, view=None)
            return
        cur = con.cursor()
        cur.execute("SELECT experience FROM characters WHERE character_name = ? AND player_id = ?",
                    (forward, ctx.author.id))
        fetch = cur.fetchall()
        if not fetch:
            con.close()
            embed = disnake.Embed(color=(disnake.Color(0x991509)),
                                  description=f"You have no character named {forward}!", title="Oops.")
            embed.set_author(
                icon_url=(ctx.author.avatar.url if ctx.author.guild_avatar is None else
                          ctx.author.guild_avater.url), name=ctx.author.nick)
            embed.set_footer(icon_url=ctx.guild.icon.url,
                             text=f"Please feel free to try again. | {ctx.guild.name}")
            embed.set_thumbnail(
                url="https://bg3.wiki/w/images/thumb/0/0a/Confusion.webp/380px-Confusion.webp.png")
            await response.edit(content=None, embed=embed, view=None)
            return
        print(f"cur {fetch}")
        experience = fetch[0][0]
        cur.execute(f"DELETE FROM characters WHERE character_name = ? AND player_id = ?",
                    (forward, ctx.author.id))
        con.commit()
        con.close()
        embed = disnake.Embed(color=(disnake.Color(0x31945c)), description=f"{forward} doesn't feel so good...",
                              title="Character deleted!")
        embed.set_author(
            icon_url=(ctx.author.avatar.url if ctx.author.guild_avatar is None else
                      ctx.author.guild_avater.url), name=ctx.author.nick)
        embed.set_footer(icon_url=ctx.guild.icon.url,
                         text=f"You are now free to initialize a new character. | {ctx.guild.name}")
        embed.set_thumbnail(
            url="https://bg3.wiki/w/images/thumb/2/23/Disintegrate.webp/380px-Disintegrate.webp.png")
        await response.edit(embed=embed, view=None,
                            content=f"-# Was this a mistake? {forward} had {experience} experience.")
        return

    @commands.command(aliases=["i"], brief="Initializes your character.",
                      help="Initializes a newly created character.", name="initialize", usage="initialize <name>")
    @commands.guild_only()
    async def initialize(self, ctx, *, character_name: str = None):
        embed = disnake.Embed(color=disnake.Color(0xe07e22), description="Verifying your character...",
                              title="Please wait...")
        embed.set_author(
            icon_url=ctx.author.avatar.url if ctx.author.guild_avatar is None else ctx.author.guild_avatar.url,
            name=ctx.author.nick)
        embed.set_footer(icon_url=ctx.guild.icon.url, text=f"Ideally, you should never see this. | {ctx.guild.name}")
        embed.set_thumbnail(url="https://bg3.wiki/w/images/thumb/5/5f/Slow.webp/380px-Slow.webp.png")
        response = await ctx.send(embed=embed)
        if character_name is None:
            embed = disnake.Embed(color=(disnake.Color(0x991509)),
                                  description="You have not specified a character name!", title="Oops.")
            embed.set_author(
                icon_url=ctx.author.avatar.url if ctx.author.guild_avatar is None else ctx.author.guild_avater.url,
                name=ctx.author.nick)
            embed.set_footer(icon_url=ctx.guild.icon.url,
                             text=f"""Please choose a name that is less than or equal to 32 characters long. \
| {ctx.guild.name}""")
            embed.set_thumbnail(
                url="https://bg3.wiki/w/images/thumb/4/4f/Generic_Threat.webp/380px-Generic_Threat.webp.png")
            await response.edit(embed=embed)
            return
        if len(character_name) > 32:
            embed = disnake.Embed(color=(disnake.Color(0x991509)),
                                  description="Your name is too long!", title="Oops.")
            embed.set_author(
                icon_url=ctx.author.avatar.url if ctx.author.guild_avatar is None else ctx.author.guild_avater.url,
                name=ctx.author.nick)
            embed.set_footer(icon_url=ctx.guild.icon.url,
                             text=f"""Please choose a name that is less than or equal to 32 characters long. \
| {ctx.guild.name}""")
            embed.set_thumbnail(
                url="https://bg3.wiki/w/images/thumb/4/4f/Generic_Threat.webp/380px-Generic_Threat.webp.png")
            await response.edit(embed=embed)
            return
        if character_name == "None, cancel!":
            embed = disnake.Embed(color=(disnake.Color(0x991509)),
                                  description="Your name sucks ass!", title="Oops.")
            embed.set_author(
                icon_url=ctx.author.avatar.url if ctx.author.guild_avatar is None else ctx.author.guild_avater.url,
                name=ctx.author.nick)
            embed.set_footer(icon_url=ctx.guild.icon.url,
                             text=f"""Please choose a name that doesn't suck ass.""")
            embed.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/1291623487990927411/1291664640106958898/no_doubles.png?ex=6700ebf0&is=66ff9a70&hm=63351b38b949988071696502b0f101edca7f022dcb6e733dc2eebf3243f386f1&")
            await response.edit(embed=embed)
            return
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await response.edit(content="Please try again in a moment.", embed=None, view=None)
            return
        cur = con.cursor()
        search = f"SELECT character_name FROM characters WHERE player_id = ?"
        player_id = [ctx.author.id]
        cur.execute(search, player_id)
        results = cur.fetchall()
        con.close()
        characters = []
        for name in results:
            for result in name:
                if character_name.lower() == result.lower():
                    embed = disnake.Embed(color=(disnake.Color(0x991509)),
                                          description="You already have a character with that name!", title="Oops.")
                    embed.set_author(
                        icon_url=(ctx.author.avatar.url if ctx.author.guild_avatar is None else
                                  ctx.author.guild_avater.url), name=ctx.author.nick)
                    embed.set_footer(icon_url=ctx.guild.icon.url,
                                     text=f"Please choose a unique name. | {ctx.guild.name}")
                    embed.set_thumbnail(
                        url="https://bg3.wiki/w/images/thumb/4/4f/Generic_Threat.webp/380px-Generic_Threat.webp.png")
                    await response.edit(embed=embed)
                    return
                elif character_name.lower() != result.lower():
                    characters.append(result)
        with open("config.json", "r") as config:
            data = json.load(config)
        if len(results) >= data["config"]["character_limit"]:
            embed = disnake.Embed(color=(disnake.Color(0x991509)), description="You have reached the character cap!",
                                  title="Oops.")
            embed.add_field(name="Delete a character?", value="Select a character to delete, or cancel the process.")
            embed.set_author(
                icon_url=(ctx.author.avatar.url if ctx.author.guild_avatar is None else
                          ctx.author.guild_avater.url), name=ctx.author.nick)
            embed.set_footer(icon_url=ctx.guild.icon.url,
                             text=f"The character cap is {str(data['config']['character_limit'])}. | {ctx.guild.name}")
            embed.set_thumbnail(
                url="https://bg3.wiki/w/images/thumb/4/4f/Generic_Threat.webp/380px-Generic_Threat.webp.png")
            await response.edit(embed=embed)
            view = disnake.ui.View(timeout=30)
            selects = view.add_item(disnake.ui.StringSelect(placeholder="Select which character to delete.", options=[],
                                                            min_values=1, max_values=1))
            selects.children[0].add_option(label="None, cancel!", value="None, cancel!",
                                           description="This option will abort the initialization process.")
            for character in characters:
                selects.children[0].add_option(label=character, value=character,
                                               description=f"This option will PERMANENTLY delete {character}!")
            view = DeletionSelection(ctx=ctx, options=selects.children[0].options)
            await response.edit(view=view)
            timeout = await view.wait()
            if timeout:
                embed = disnake.Embed(color=(disnake.Color(0x991509)), description="Character initialization aborted!",
                                      title="Oops.")
                embed.set_author(
                    icon_url=(ctx.author.avatar.url if ctx.author.guild_avatar is None else
                              ctx.author.guild_avater.url), name=ctx.author.nick)
                embed.set_footer(icon_url=ctx.guild.icon.url,
                                 text=f"Please feel free to try again. | {ctx.guild.name}")
                embed.set_thumbnail(
                    url="https://bg3.wiki/w/images/thumb/3/3f/Bane_Spell.webp/380px-Bane_Spell.webp.png")
                await response.edit(content=None, embed=embed, view=None)
                return
            forward = DeletionSelection.forward
            if forward == "None, cancel!":
                embed = disnake.Embed(color=(disnake.Color(0x991509)), description="Character initialization aborted!",
                                      title="Oops.")
                embed.set_author(
                    icon_url=(ctx.author.avatar.url if ctx.author.guild_avatar is None else
                              ctx.author.guild_avater.url), name=ctx.author.nick)
                embed.set_footer(icon_url=ctx.guild.icon.url,
                                 text=f"Please feel free to try again. | {ctx.guild.name}")
                embed.set_thumbnail(
                    url="https://bg3.wiki/w/images/thumb/3/3f/Bane_Spell.webp/380px-Bane_Spell.webp.png")
                await response.edit(embed=embed, view=None)
                return
            elif forward != "None, cancel!":
                try:
                    con = sqlite3.connect("characters.db", timeout=30)
                except OperationalError:
                    await response.edit(content="Please try again in a moment.", embed=None, view=None)
                    return
                cur = con.cursor()
                cur.execute("SELECT experience FROM characters WHERE character_name = ? AND player_id = ?",
                            (forward, ctx.author.id))
                experience = cur.fetchall()[0][0]
                cur.execute(f"DELETE FROM characters WHERE character_name = ? AND player_id = ?",
                            (forward, ctx.author.id))
                con.commit()
                con.close()
                embed = disnake.Embed(color=(disnake.Color(0x31945c)), description=f"{forward} doesn't feel so good...",
                                      title="Character deleted!")
                embed.set_author(
                    icon_url=(ctx.author.avatar.url if ctx.author.guild_avatar is None else
                              ctx.author.guild_avater.url), name=ctx.author.nick)
                embed.set_footer(icon_url=ctx.guild.icon.url,
                                 text=f"Your new character will be initialized in a moment. | {ctx.guild.name}")
                embed.set_thumbnail(
                    url="https://bg3.wiki/w/images/thumb/2/23/Disintegrate.webp/380px-Disintegrate.webp.png")
                await response.edit(embed=embed, view=None,
                                    content=f"-# Was this a mistake? {forward} had {experience} experience.")
        character_id = uuid.uuid4()
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            await ctx.send("Please try again in a moment.")
            return
        cur = con.cursor()
        cur.execute(f"""INSERT INTO characters VALUES ("{character_id}", "{character_name}", {ctx.author.id},
0,5,2,0,0,0,0,0,0,0,0,0,0)""")
        con.commit()
        con.close()
        embed = disnake.Embed(color=(disnake.Color(0x31945c)),
                              description="Character initialized!", title="Yippee!")
        embed.set_author(
            icon_url=(ctx.author.avatar.url if ctx.author.guild_avatar is None else
                      ctx.author.guild_avater.url), name=ctx.author.nick)
        embed.set_footer(icon_url=ctx.guild.icon.url,
                         text=f"Enjoy playing with {character_name}! | {ctx.guild.name}")
        embed.set_thumbnail(
            url="https://bg3.wiki/w/images/thumb/1/14/Bless.webp/380px-Bless.webp.png")
        await response.edit(embed=embed, view=None)
        return


def setup(bot):
    bot.add_cog(Characters(bot))
