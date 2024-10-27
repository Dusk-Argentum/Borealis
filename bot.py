import disnake
from disnake.ext import commands


import os


DESCRIPTION = """A bot for use on the Northern Lights Province Discord server to facilitate playing multiple D&D \
characters on the same Discord account while still retaining the ability to gain experience based on messages."""
GUILD = 348897377400258560
PREFIX = "DEFAULT_PREFIX"
TESTS = None
TOKEN = os.environ.get("BorealisBETA_TOKEN")
VERSION = "0.0.1-BETA-RC1"

if TOKEN == os.environ.get("Borealis_TOKEN"):
    GUILD = 1031055347319832666
    PREFIX = "!"
    TESTS = None
elif TOKEN == os.environ.get("BorealisBETA_TOKEN"):
    GUILD = 348897377400258560
    PREFIX = "."
    TESTS = [GUILD]


command_sync_flags = commands.CommandSyncFlags.default()


# intents = disnake.Intents.all()
intents = disnake.Intents.default()
intents.members = True
intents.message_content = True


bot = commands.Bot(case_insensitive=True, command_prefix=PREFIX, command_sync_flags=command_sync_flags,
                   description=DESCRIPTION, intents=intents, test_guilds=TESTS, owner_id=97153790897045504)


bot.remove_command("help")


bot.load_extension("cogs.aurora")
bot.load_extension("cogs.characters")
bot.load_extension("cogs.dev")
bot.load_extension("cogs.events")
bot.load_extension("cogs.experience")
bot.load_extension("cogs.help")


if __name__ == "__main__":
    bot.run(TOKEN)
