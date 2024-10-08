import disnake
from disnake.ext import commands

from bot import PREFIX

import sqlite3
from sqlite3 import OperationalError

import json

import re

from datetime import datetime

import time


class Experience(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def processing(self, ctx):
        if ctx.author.id == self.bot.user.id:
            return
        if ctx.author.bot:
            return
        if type(ctx.channel) is disnake.DMChannel:
            return
        if ctx.content.startswith(PREFIX):
            return
        # TODO: Check for if sender is active player?
        # TODO: Surely, there's more reasons why a message wouldn't be processed at all.
        print("Processing complete. Moving to config...")
        await Experience.config(self, ctx=ctx)

    @staticmethod
    async def config(self, ctx):
        with open("config.json", "r") as config:
            data = json.load(config)
            config.close()
        config = data["config"][f"{ctx.guild.id}"]["experience"]
        dm_choose = False
        dm_roles = []
        if config["ooc_messages"]["start"] is not False and config["ooc_messages"]["end"] is not False:
            pattern = f"\\{config['ooc_messages']['start']}.*\\{config['ooc_messages']['end']}"
            ooc_check = re.search(pattern, ctx.content)
            if ooc_check is not None:
                return
        if config["minimum_length"] is not False:
            if len(ctx.content) < config["minimum_length"]:
                return
        if config["ignored_channels"] is not False:
            for channel_id in config["ignored_channels"]:
                if ctx.channel.id == channel_id:
                    return
        if config["ignored_roles"] is not False:
            for role in ctx.author.roles:
                if role.id in config["ignored_roles"]:
                    return
        if config["dm"]["choose_experience"] is not False:
            for role in config["dm"]["roles"]:
                dm_roles.append(role)
            dm_choose = True
        print("Configuration complete. Moving to determination...")
        await Experience.determination(self, ctx=ctx, dm_choose=dm_choose, dm_roles=dm_roles)

    @staticmethod
    async def determination(self, ctx, dm_choose, dm_roles):
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            return
        cur = con.cursor()
        cur.execute("SELECT * FROM characters WHERE player_id = ?", [ctx.author.id])
        characters = cur.fetchall()
        con.close()
        if not characters:
            return
        rewarded = None
        highest_points = 0
        next_experience = 0
        for characters_list in characters:
            character = []
            for value in characters_list:
                character.append(value)
            character.append(0)
            if character[6] == 1:  # GLOBAL check. There must always be one GLOBAL character per player. This adds
                # one point to the specified GLOBAL character's likelihood to break a tie of zeroes.
                character[23] += 1
            if character[7] == 1:  # ACTIVE check. Rewards players who are vigilant with switching characters by giving
                # the character who is ACTIVE a greater likelihood without completely overriding other checks.
                character[23] += 20
            name_search_pattern = f"{str(character[1][0]).capitalize()}{str(character[1][1:]).lower()}"
            name_search = re.search(rf"[\s|*|\"|\'|_]{name_search_pattern}[\s|*|\"|\'|.|,|?|!|_]", ctx.content)
            if name_search is not None:  # NAME check. Searches the content of the message for a mention of the
                # character's name, and adds likelihood to that character. Can trip for multiple characters on a player
                # if their message mentions multiple of their characters, hence why its increase is so low.
                character[23] += 5
            nicknames = character[19:22]
            nick_slice = 19
            for nick in nicknames:  # NICK check. Similar to NAME, but less powerful to mitigate ties and misuse.
                if nick == "":
                    nick_slice += 1
                    continue
                nick_search_pattern = f"""{str(character[nick_slice][0]).capitalize()}\
{str(character[nick_slice][1:]).lower()}"""
                nick_search = re.search(rf"[\s|*|\"|\']{nick_search_pattern}[\s|*|\"|\'|.|,|?|!]", ctx.content)
                if nick_search is None:
                    nick_slice += 1
                    continue
                elif nick_search is not None:
                    character[23] += 4
            preferred_channels = character[9:19]
            channel_slice = 9
            for channel in preferred_channels:  # CHANNEL check. Rewards players who predefine channels where that
                # character is most likely to be, such as a house channel, or channels set before an outing. Powerful
                # enough to be rewarding, while still enabling overwrite if a player forgets to unset channels.
                if channel == 0:
                    channel_slice += 1
                    continue
                if ctx.channel.id == character[channel_slice]:
                    character[23] += 15
                channel_slice += 1
            underlined_name_search = re.search(rf"_{r"{2}"}{name_search_pattern}_{r"{2}"}", ctx.content)
            if underlined_name_search is not None:  # UNDERLINE check. Essentially allows a player to manually set
                # which character obtains experience. Able to be misused, but very obvious, both in message content,
                # and in message logs.
                character[23] += 100
            if dm_choose is True and dm_roles != []:  # DM check. Allows a DM to set a preferred character for obtaining
                # experience while running adventures. Can only be overridden by UNDERLINE.
                for role in dm_roles:
                    if role in ctx.author.roles:
                        if character[8] == 1:
                            character[23] += 50
                            break
            for character_points in characters:  # Compares the points of characters and sets them as rewarded if theirs
                # is the highest total.
                if character[23] > highest_points:
                    highest_points = character[23]
                    rewarded = character[1]
            print(f"{character[1]} has {character[23]} points. The highest point total is {highest_points}.")
        print("Determination complete. Moving to rewarding...")
        await Experience.rewarding(self, ctx=ctx, rewarded=rewarded)

    @staticmethod
    async def rewarding(self, ctx, rewarded):
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            return
        cur = con.cursor()
        cur.execute("""SELECT experience, level, tier, next_experience FROM characters \
WHERE player_id = ? AND character_name = ?""", [ctx.author.id, rewarded])
        values = cur.fetchall()
        con.close()
        value_list = []
        for value in values[0]:
            value_list.append(value)
        if datetime.now(tz=None) < datetime.fromtimestamp(value_list[3], tz=None):
            return
        experience = value_list[0] + 1  # Here, the experience added will be modified.
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            return
        cur = con.cursor()
        cur.execute("UPDATE characters SET experience = ? WHERE player_id = ? AND character_name = ?",
                    [experience, ctx.author.id, rewarded])
        con.commit()
        cur.execute("SELECT experience FROM characters WHERE player_id = ? AND character_name = ?",
                    [ctx.author.id, rewarded])
        final_experience = cur.fetchall()[0][0]
        con.close()
        with open("config.json", "r") as config:
            data = json.load(config)
            config.close()
        config = data["config"][str(ctx.guild.id)]["experience"]
        next_experience = int(time.time()) + config["time_between"]
        try:
            con = sqlite3.connect("characters.db", timeout=30.0)
        except OperationalError:
            return
        cur = con.cursor()
        cur.execute("UPDATE characters SET next_experience = ? WHERE player_id = ? AND character_name = ?",
                    [next_experience, ctx.author.id, rewarded])
        con.commit()
        con.close()
        with open("experience.json", "r") as experience_reference:
            data = json.load(experience_reference)
            experience_reference.close()
        if final_experience > data["experience"][f"{value_list[1] + 1}"]:
            await Experience.level(self, ctx=ctx, rewarded=rewarded)
        print(f"Dew's experience total is {final_experience}.")
        exp = datetime.fromtimestamp(next_experience, tz=None)
        print(f"Dew will be able to gain experience again at {exp}")
        # print(value_list)

    @staticmethod
    async def level(self, ctx, rewarded):
        print("yey level. woo, etc.")

    @commands.Cog.listener()
    async def on_message(self, ctx):
        await Experience.processing(self, ctx=ctx)


def setup(bot):
    bot.add_cog(Experience(bot))
