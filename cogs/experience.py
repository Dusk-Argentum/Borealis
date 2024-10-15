from bot import PREFIX

from datetime import datetime

import disnake
from disnake.ext import commands

import json

import random

import re

import sqlite3
from sqlite3 import OperationalError

import time


class Experience(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, ctx):
        await Experience.processing(self, ctx=ctx)

    @staticmethod
    async def processing(self, ctx):
        if ctx.author.id == self.bot.user.id:
            return
        elif ctx.author.bot:
            return
        elif type(ctx.channel) is disnake.DMChannel or type(ctx.channel) is disnake.GroupChannel:
            return
        elif ctx.content.startswith(PREFIX):
            return
        elif ctx.content.startswith("!"):
            return
        for role in ctx.author.roles:
            if role.name.lower() == "player":
                break
        else:
            return
        await Experience.bot_config(ctx=ctx)

    @staticmethod
    async def bot_config(ctx):
        try:
            con = sqlite3.connect("bot_config.db", timeout=30.0)
        except OperationalError:
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT banned_users, banned_guilds FROM bot_config")
        banned = [dict(value) for value in cur.fetchall()][0]
        con.close()
        banned_users = []
        banned_guilds = []
        if banned["banned_users"] is not None:
            banned_users = json.loads(banned["banned_users"])
        if banned["banned_guilds"] is not None:
            banned_guilds = json.loads(banned["banned_guilds"])
        for user in banned_users:
            if ctx.author.id == int(user):
                return
        for guild in banned_guilds:
            if ctx.guild.id == int(guild):
                return
        await Experience.server_config(ctx=ctx)

    @staticmethod
    async def server_config(ctx):
        try:
            con = sqlite3.connect("server_config.db", timeout=30.0)
        except OperationalError:
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("""SELECT ooc_start, ooc_end, minimum_length, ignored_channels, ignored_roles, dm_choose \
FROM server_config WHERE guild_id = ?""", [ctx.guild.id])
        server_config = [dict(value) for value in cur.fetchall()][0]
        con.close()
        if server_config["ooc_start"] != "0" and server_config["ooc_end"] != "0":
            pattern = f"""\\{server_config["ooc_start"]}.*\\{server_config["ooc_end"]}"""
            ooc_check = re.search(pattern, ctx.content)
            if ooc_check is not None:
                return
        if int(server_config["minimum_length"]) != 0:
            if len(ctx.content) < int(server_config["minimum_length"]):
                return
        if server_config["ignored_channels"] is not None:
            ignored_channels = json.loads(server_config["ignored_channels"])
            for channel in ignored_channels:
                if channel == ctx.channel.id:
                    return
        if server_config["ignored_roles"] is not None:
            ignored_roles = json.loads(server_config["ignored_roles"])
            for role in ignored_roles:
                for author_role in ctx.author.roles:
                    if role == author_role.id:
                        return
        await Experience.determination(ctx=ctx)

    @staticmethod
    async def determination(ctx):
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("""SELECT character_name, global, active, dm, channels, nicks \
FROM characters WHERE player_id = ? AND guild_id = ?""", [ctx.author.id, ctx.guild.id])
        characters = [dict(value) for value in cur.fetchall()]
        con.close()
        if not characters:
            return
        rewarded = None
        highest_points = 0
        for character in characters:
            points = 0
            if character["global"] == 1:  # GLOBAL check. There must always be one GLOBAL character per player. This
                # adds one point to the specified GLOBAL character's likelihood to break a tie of zeroes.
                points += 1
            if character["active"] == 1:  # ACTIVE check. Rewards players who are vigilant with switching characters by
                # giving the character who is ACTIVE a greater likelihood without completely overriding other checks.
                points += 20
            name_search_pattern = f"""{character["character_name"][0].capitalize()}\
{character["character_name"][1:].lower()}"""
            name_search = re.search(rf"[\s|*|\"|\'|_]{name_search_pattern}[\s|*|\"|\'|.|,|?|!|_]", ctx.content)
            if name_search is not None:  # NAME check. Searches the content of the message for a mention of the
                # character's name, and adds likelihood to that character. Can trip for multiple characters on a player
                # if their message mentions multiple of their characters, hence why its increase is so low.
                points += 5
            if character["channels"] is not None:  # CHANNEL check. Rewards players who predefine channels where that
                # character is most likely to be, such as a house channel, or channels set before an outing. Powerful
                # enough to be rewarding, while still enabling overwrite if a player forgets to unset channels.
                channels = json.loads(character["channels"])
                for channel in channels:
                    if channel == ctx.channel.id:
                        points += 15
            if character["nicks"] is not None:  # NICK check. Similar to NAME, but less powerful to mitigate ties
                # and misuse.
                nicks = json.loads(character["nicks"])
                for nick in nicks:
                    nick_search_pattern = f"{nick[0].capitalize()}{nick[1:].lower()}"
                    nick_search = re.search(rf"[\s|*|\"|\']{nick_search_pattern}[\s|*|\"|\'|.|,|?|!]",
                                            ctx.content)
                    if nick_search is not None:
                        points += 4
            underlined_name_search = re.search(rf"_{r"{2}"}{name_search_pattern}_{r"{2}"}", ctx.content)
            if underlined_name_search is not None:  # UNDERLINE check. Essentially allows a player to manually set
                # which character obtains experience. Able to be misused, but very obvious, both in message content,
                # and in message logs.
                points += 100
            try:
                con = sqlite3.connect("server_config.db", timeout=30.0)
            except OperationalError:
                return
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("""SELECT dm_choose, dm_roles FROM server_config WHERE guild_id = ?""",
                        [ctx.guild.id])
            server_config = [dict(value) for value in cur.fetchall()][0]
            con.close()
            dm_choose = False
            dm_roles = []
            if server_config["dm_choose"] != 0 and server_config["dm_roles"] is not None:
                dm_choose = True
                dm_roles = json.loads(server_config["dm_roles"])
                for role in dm_roles:
                    dm_roles.append(role)
            if dm_choose is True and dm_roles is not None:  # DM check. Allows a DM to set a preferred character for
                # obtaining experience while running adventures. Can only be overridden by UNDERLINE.
                for role in dm_roles:
                    if role in ctx.author.roles:
                        if character["dm"] == 1:
                            points += 50
                            break
            if points > highest_points:
                highest_points = points
                rewarded = character["character_name"]
        await Experience.rewarding(ctx=ctx, rewarded=rewarded)

    @staticmethod
    async def rewarding(ctx, rewarded):
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("""SELECT experience, level, next_experience FROM characters \
WHERE player_id = ? AND guild_id = ? AND character_name = ?""", [ctx.author.id, ctx.guild.id, rewarded])
        character = [dict(value) for value in cur.fetchall()][0]
        con.close()
        if datetime.now(tz=None) < datetime.fromtimestamp(int(character["next_experience"]), tz=None):
            return
        try:
            con = sqlite3.connect("server_config.db", timeout=30.0)
        except OperationalError:
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT time_between, experience_thresholds, base_multiplier, level_multipliers, \
role_multipliers, min_wiggle, max_wiggle FROM server_config WHERE guild_id = ?", [ctx.guild.id])
        server_config = [dict(value) for value in cur.fetchall()][0]
        con.close()
        experience = int((int(json.loads(server_config["experience_thresholds"])[f"{int(character['level']) + 1}"])
                          * float(server_config["base_multiplier"])))
        experience = int(int(json.loads(server_config["level_multipliers"])[f"{int(character['level'])}"]) * experience)
        for role, multiplier in json.loads(server_config["role_multipliers"]).items():
            for author_role in ctx.author.roles:
                if int(role) == author_role.id:
                    experience = int(experience * float(multiplier))
        wiggle = float(str(random.uniform(float(server_config["min_wiggle"]), float(server_config["max_wiggle"])))[0:4])
        experience = int(experience * wiggle) + int(character["experience"])
        # TODO: Bugtest this and ensure it'll work with weird configs.
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            return
        cur = con.cursor()
        cur.execute("""UPDATE characters SET experience = ? WHERE player_id = ? AND guild_id = ? AND \
character_name = ?""", [experience, ctx.author.id, ctx.guild.id, rewarded])
        con.commit()
        con.close()
        try:
            con = sqlite3.connect("server_config.db", timeout=30.0)
        except OperationalError:
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT time_between, experience_thresholds FROM server_config WHERE guild_id = ?",
                    [ctx.guild.id])
        server_config = [dict(value) for value in cur.fetchall()][0]
        con.close()
        next_experience = int(time.time()) + int(server_config["time_between"])
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            return
        cur = con.cursor()
        cur.execute("""UPDATE characters SET next_experience = ? WHERE player_id = ? AND guild_id = ? AND \
character_name = ?""", [next_experience, ctx.author.id, ctx.guild.id, rewarded])
        con.commit()
        con.close()
        if experience >= (json.loads(server_config["experience_thresholds"]))[f"{int(character["level"]) + 1}"]:
            await Experience.level(ctx=ctx, rewarded=rewarded)

    @staticmethod
    async def level(ctx, rewarded):
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("""SELECT experience FROM characters WHERE player_id = ? AND guild_id = ? AND \
character_name = ?""", [ctx.author.id, ctx.guild.id, rewarded])
        character = [dict(value) for value in cur.fetchall()][0]
        con.close()
        try:
            con = sqlite3.connect("server_config.db", timeout=30.0)
        except OperationalError:
            return
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("""SELECT experience_thresholds, tier_thresholds, level_channel, level_message \
FROM server_config WHERE guild_id = ?""", [ctx.guild.id])
        server_config = [dict(value) for value in cur.fetchall()][0]
        con.close()
        new_level = 1
        for level, threshold in json.loads(server_config["experience_thresholds"]).items():
            if threshold <= int(character["experience"]):
                new_level = int(level)
        new_tier = 1
        for tier, threshold in json.loads(server_config["tier_thresholds"]).items():
            if threshold <= new_level:
                new_tier = int(tier)
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            return
        cur = con.cursor()
        cur.execute("""UPDATE characters SET level = ?, tier = ? WHERE player_id = ? AND guild_id = ? AND \
character_name = ?""", [new_level, new_tier, ctx.author.id, ctx.guild.id, rewarded])
        con.commit()
        con.close()
        if server_config["level_channel"] != 0 and server_config["level_message"] != 0:
            channel = disnake.utils.get(ctx.guild.channels, id=int(server_config["level_channel"]))
            message = re.sub(r"%PING", ctx.author.mention, server_config["level_message"])
            message = re.sub(r"%CHAR", rewarded, message)
            message = re.sub(r"%LVL", str(new_level), message)
            message = re.sub(r"\\n", "\n", message)
            await channel.send(message)


def setup(bot):
    bot.add_cog(Experience(bot))
