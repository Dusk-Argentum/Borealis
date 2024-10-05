import disnake
from disnake.ext import commands

from bot import PREFIX

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
        # TODO: Surely, there's more reasons why a message wouldn't be processed at all.
        print("Processing complete. Moving to config...")
        await Experience.config_checks(self, ctx=ctx)

    @staticmethod
    async def config_checks(self, ctx):
        with open("config.json", "r") as config:
            data = json.load(config)
            config.close()
        config = data["config"][f"{ctx.guild.id}"]["experience"]
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
        print("Configuration complete. Moving to rewarding...")
        await Experience.rewarding(self, ctx=ctx)

    @staticmethod
    async def rewarding(self, ctx):
        print("aa")

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
