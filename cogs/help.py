from bot import PREFIX, VERSION

from cogs.functions import EmbedBuilder

import disnake
from disnake import Forbidden
from disnake.ext import commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def help(self, ctx, inter, module, source):
        src = None
        if source == "slash":
            src = inter
        elif source == "message":
            src = ctx
        if source == "slash":
            src.edit = inter.edit_original_response
        aurora_role = disnake.utils.get(src.guild.roles, name="Aurora")
        if aurora_role is None:
            try:
                await src.guild.create_role(name="Aurora")
            except Forbidden:
                await EmbedBuilder.embed_builder(ctx=src, custom_color=None, custom_thumbnail=None,
                                                 custom_title=None,
                                                 description="I don't have permission to Manage Roles!",
                                                 fields=None,
                                                 footer_text="""Please ask your Administrator(s) to grant me the \
Manage Roles permission. I can't function without it!""", status="failure")
                return
        for cog in self.bot.cogs:
            if cog == "Aurora" and aurora_role not in src.author.roles:
                continue
            elif cog == "Dev" and src.author.id != self.bot.owner_id:
                continue
            elif cog == "Events":
                continue
            elif cog == "Experience":
                continue
            elif cog == "Help":
                continue
            if module is not None and module.lower() != cog.lower():
                continue
            elif module is not None and module.lower() == "aurora" and aurora_role not in src.author.roles:
                continue
            fields = []
            for command in self.bot.get_cog(cog).walk_commands():
                fields.append({"inline": False, "name": f"{command.name} (`{"`, `".join(command.aliases)}`)",
                               "value": f"""{command.help}\n`/{command.usage}` (`{PREFIX}{command.usage}`)"""})
            await EmbedBuilder.embed_builder(ctx=src, custom_color=disnake.Color(0x023d08), custom_thumbnail=None,
                                             custom_title=f"{cog}: Commands",
                                             description="""Arguments in `<>` are required. Arguments in `[]` have \
default values that can be overwritten.""", fields=fields, footer_text=f"Made by @dusk_argentum! | Version: {VERSION}",
                                             status=None)
            await src.send(embed=EmbedBuilder.embed)

    @commands.slash_command(name="help", description="Shows commands and how to use them.", dm_permission=False)
    @commands.guild_only()
    async def help_slash(self, inter, module: str = None):
        """
        Parameters
        ----------

        inter:
        module: Name of module to list commands. Valid values: Aurora (admins), Characters. Defaults to all.
        """
        await self.help(self=self, ctx=None, inter=inter, module=module, source="slash")

    @commands.command(aliases=["h"], brief="Shows commands.", help="Shows commands and how to use them.", name="help",
                      usage="help [module]")
    async def help_message(self, ctx, module: str = None):
        await self.help(self=self, ctx=ctx, inter=None, module=module, source="message")


def setup(bot):
    bot.add_cog(Help(bot))
