import disnake
from disnake.ext import commands

from bot import PREFIX

import sqlite3
from sqlite3 import OperationalError

import json

import re


# on_message > ProcessingChecks > ConfigurationChecks > RewardExperience

# ProcessingChecks narrows down whether the message is worth processing. Is it from a non-bot user? Is it in a channel
# that is not in the OOC category? Does the message start with a (/end with a )? And other checks. If all of them pass,
# then the message is processed using the server's configuration.

# ConfigurationChecks applies more checks and modifiers to the message, including whether it should grant experience
# based on a user's role (eg. for the No EXP role), and other configuration parameters.

# RewardExperience processes all the information from ConfigurationChecks to determine the final EXP amount rewarded
# and to which character the experience is rewarded.

class Experience(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def processing_checks(self, ctx):
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
        await Experience.config_checks(self, ctx=ctx)

    @staticmethod
    async def config_checks(self, ctx):
        with open("config.json", "r") as config:
            data = json.load(config)
            config.close()
        config = data["config"][f"{ctx.guild.id}"]["experience"]
        dm_choose = None
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
            for role in config["dm_roles"]:
                dm_roles.append(role)
            dm_choose = True
        print("Configuration complete. Moving to rewarding...")
        await Experience.rewarding(self, ctx=ctx, dm_choose=dm_choose, dm_roles=dm_roles)

    @staticmethod
    async def rewarding(self, ctx, dm_choose, dm_roles):
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
        for characters_list in characters:
            character = []
            for value in characters_list:
                character.append(value)
            if character[6] == 1:  # Global character check. This is the default fallback and intended to be overwritten
                # by the user. Only one character can be a global character per player. At least one character must have
                # the global character flag at all times.
                rewarded = character[1]
                # TODO: grants 1 point
            # The thought process is that global character should overwrite names, but if the channel is specifically
            # set to be for a specific character, then the channel will take precedence.
            # It is possible to not have a global character set. A player with a global character set can still
            # gain EXP on the non-global character if it is... OK, it should be at the top.
            # In most circumstances, one player's character will not talk about the other characters. However,
            # even if they are mentioned, there are other safeguards, such as the channel being a preferred channel.
            # I should add another method of checking to make sure the exp is going to the correct character after or
            # just before the channels check to add a second layer.
            if character[7] == 1:  # Active character check. This is a forced override intended for players who are
                # extraordinarily vigilant about switching their characters. It bypasses all other checks, excluding
                # the DM preferred character check.
                rewarded = character[1]
                break
                # TODO: grants 20 points?
            name_search_pattern = f"{str(character[1][0]).capitalize()}{str(character[1][1:]).lower()}"
            name_search = re.search(rf"[\s|*|\"|\']{name_search_pattern}[\s|*|\"|\'|.|,|?|!]", ctx.content)
            if name_search is not None:  # Character name check. Searches the content of the message for a mention
                # of the character's name, and sets the rewarded character to that character. Has the notable flaw of
                # being able to have character experience awarded to the wrong character if the player mentions multiple
                # of their character names in one message.
                rewarded = character[1]  # TODO: Hold that thought. Perhaps each check could increase the likelihood for
                # TODO: each character, and the character with the highest likelihood gets rewarded?
                # break
                # This should not override all other checks. Right?
                # TODO: grants 5 points
            nicknames = character[19:22]
            nick_slice = 19
            for nick in nicknames:  # Same as the name check, but for nicknames. The same flaw is inherent here, too.
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
                    rewarded = character[1]
                    # TODO: grants 4 points
                    # break
            preferred_channels = character[9:19]
            channel_slice = 9
            for channel in preferred_channels:  # Preferred channel check. If the message sent is in one of the
                # character's preferred channels, that character is rewarded.
                if channel == 0:
                    channel_slice += 1
                    continue
                if ctx.channel.id == character[channel_slice]:
                    rewarded = character[1]
                    break
                channel_slice += 1
                # TODO: Grants 15 points
            underlined_name_search = re.search(rf"_{2}{name_search_pattern}_{2}", ctx.content)
            if underlined_name_search is not None:  # Underlined check. If a character's name is underlined anywhere
                # in the message, that character is rewarded.
                rewarded = character[1]
                break
                # TODO: grants 30 points
            # underlined_name_pattern = f"{str(character[1][0]).capitalize()}{str(character[1][1:]).lower()}"
        print(rewarded)
        # TODO: Add "active" character which can be switched between..? Is that the same as or different from global?
        # TODO: Global and above
        # Global needs to be put somewhere where it won't overwrite preferences but will still take precedence
        # name > nick > preferred > global > slice > choice
        # name and nick need regex to ensure that simply mentioning the other character doesn't trip it?
        # or other sanity matching
        # if nick/name in regex for message, that is rewarded. Unless DM role
        # if DM role present, check DM slice. That is rewarded unless all are 0.
        # if channel id matches preferred for a character, that is rewarded. Unless DM role
        # if DM role is present and DM slice are all 0, send ephem for choice.
        # choice ephem has a 5 minute timeout. If timeout, unclaimed exp is logged for later claim. Dmess>command?
        # if global is 1, that is rewarded. Unless DM role
        # print(characters)

    @commands.Cog.listener()
    async def on_message(self, ctx):
        await Experience.processing_checks(self, ctx=ctx)

    @commands.command(aliases=["wet"], brief="a", help="b", name="test2", usage="bong")
    @commands.guild_only()
    async def testy(self, ctx):
        print(self.bot.user.id)
        return


def setup(bot):
    bot.add_cog(Experience(bot))
