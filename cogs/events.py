import asyncio
import json

from bot import PREFIX

from datetime import datetime, timezone

import disnake
from disnake import Forbidden
from disnake.ext import commands
from disnake.ext.commands import (
    BotMissingPermissions,
    ChannelNotFound,
    CheckFailure,
    CommandInvokeError,
    CommandNotFound,
    MemberNotFound,
    MissingAnyRole,
    NoPrivateMessage,
    NotOwner,
    UnexpectedQuoteError,
    UserNotFound,
)

import sqlite3
from sqlite3 import OperationalError


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx, error
    ):  # Functions in this block execute when a command errors.
        if (
            ctx.author.id == self.bot.owner_id
        ):  # Functions in this block execute if the command invoker is the bot's
            # owner.
            await ctx.send(error)  # Sends the unedited error text to the channel.
        raw_error = error
        if isinstance(
            error, BotMissingPermissions
        ):  # Functions in this block execute if the bot is missing the
            # permissions required to execute a function.
            error = "I do not have permission to enact this command."
        if isinstance(
            error, ChannelNotFound
        ):  # Functions in this block execute if the bot tries to grab a channel
            # that is invalid.
            error = """Channel not found. Please make sure to #mention the channel, or use its Discord ID.
Example: <#628080650427039764> | `628080650427039764`"""
        if isinstance(
            error, CheckFailure
        ):  # Functions in this block execute if a check (which prevents a command
            # (from progressing if certain prerequisites are not met) fails.
            error = "You cannot use this command."
        if isinstance(
            error, CommandInvokeError
        ):  # Functions in this block execute if there is an unhandled
            # exception which causes the command to execute improperly.
            error = f"Incorrect invocation. Please re-examine the command in `{PREFIX}help`."
        if isinstance(
            error, CommandNotFound
        ):  # Functions in this block execute if the invoker tries to run
            # a command that does not exist.
            error = f"Command not found. Please view `{PREFIX}help` for valid commands."
        if isinstance(
            error, MemberNotFound
        ):  # Functions in this block execute if the provided member is invalid.
            error = """Member not found. Please make sure to @mention the member, or use their Discord ID.
Example: <@97153790897045504> | `97153790897045504`"""
        if isinstance(
            error, MissingAnyRole
        ):  # Functions in this block execute if the invoker is missing
            # a certain role.
            error = "You do not have permission to run this command."
        if isinstance(
            error, NoPrivateMessage
        ):  # Functions in this block execute if the invoker tries to invoke
            # a command in a private message.
            error = "You cannot run this command in a private message."
        if isinstance(
            error, NotOwner
        ):  # Functions in this block execute if the invoker is cringe.
            error = "You're not cool enough to run this command."
        if isinstance(error, UnexpectedQuoteError):
            error = "Unexpected quote. Please use `'` instead of `‘`."
        if isinstance(
            error, UserNotFound
        ):  # Functions in this block execute if the provided user is invalid.
            error = """User not found. Please make sure to @mention the user, or use their Discord ID.
Example: <@97153790897045504> | `97153790897045504`"""
        channel = self.bot.get_channel(
            1299891459255959644
        )  # Grabs the error reporting channel for Mudbot on
        # my private server.
        embed = disnake.Embed(
            color=disnake.Color(0x3B9DA5),
            description="An exception was caught.",
            title="Error!",
        )
        # Functions below define the various aspects of an embed and their content.
        embed.set_author(icon_url=self.bot.user.avatar.url, name=self.bot.user.name)
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        timestamp = int(
            (
                datetime.strptime(
                    str(datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)),
                    "%Y-%m-%d %H:%M:%S",
                )
                - datetime.strptime("1970-01-01", "%Y-%m-%d")
            ).total_seconds()
        )
        value = f"""A command {f"(`{PREFIX}{ctx.command.name}`)" if ctx.command is not None else ""} invoked by \
{ctx.author.mention} (`{ctx.author.id}`) on <t:{timestamp}:F> in {f"{ctx.channel.mention} (`{ctx.channel.id}`)" if
                                                                  ctx.channel.type == disnake.ChannelType.text else
                                                                  (f"a DM with {ctx.author.mention}"
                                                                   f"(`{ctx.author.id}`)")} \
caused the error detailed below."""
        embed.add_field(inline=False, name="Source:", value=value)
        embed.add_field(inline=False, name="Raw Error:", value=str(raw_error))
        embed.add_field(inline=False, name="Message Sent:", value=error)
        embed.add_field(
            inline=False, name="Message Content:", value=f"`{ctx.message.content}`"
        )
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=self.bot.user.name)
        await channel.send(embed=embed)
        await ctx.send(f"Error: {error}")  # Sends the error text.

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        exp_thresholds = {
            "1": 0,
            "2": 300,
            "3": 900,
            "4": 2700,
            "5": 6500,
            "6": 14000,
            "7": 23000,
            "8": 34000,
            "9": 48000,
            "10": 64000,
            "11": 85000,
            "12": 100000,
            "13": 120000,
            "14": 140000,
            "15": 165000,
            "16": 195000,
            "17": 225000,
            "18": 265000,
            "19": 305000,
            "20": 355000,
            "21": 415000,
            "22": 475000,
            "23": 545000,
            "24": 615000,
            "25": 695000,
            "26": 775000,
            "27": 865000,
            "28": 955000,
            "29": 1055000,
            "30": 1155000,
        }
        exp_thresholds = json.dumps(exp_thresholds, indent=2)
        tier_thresholds = {"1": 0, "2": 5, "3": 11, "4": 17}
        tier_thresholds = json.dumps(tier_thresholds, indent=2)
        try:
            con = sqlite3.connect("server_config.db", timeout=30.0)
        except OperationalError:
            await guild.leave()
            return
        cur = con.cursor()
        cur.execute(
            """INSERT INTO server_config VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                str(guild.id),
                2,
                "(",
                ")",
                1,
                300,
                1,
                30,
                str(exp_thresholds),
                str(tier_thresholds),
                1,
                "{}",
                "{}",
                "{}",
                1,
                1,
                "{}",
                "{}",
                1,
                "{}",
                0,
                0,
            ],
        )
        con.commit()
        con.close()
        player_role = disnake.utils.get(guild.roles, name="Player")
        if player_role is None:
            try:
                await guild.create_role(name="Player")
            except Forbidden:
                await guild.leave()
                return
        aurora_role = disnake.utils.get(guild.roles, name="Aurora")
        if aurora_role is None:
            try:
                await guild.create_role(name="Aurora")
            except Forbidden:
                await guild.leave()
                return

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(1)
        await self.bot.change_presence(activity=disnake.Game(f"TTRPGs! | /help"))
        print(f"{self.bot.user.name} is online! Awaiting commands and messages.")


def setup(bot):
    bot.add_cog(Events(bot))
