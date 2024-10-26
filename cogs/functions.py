import disnake


class EmbedBuilder(disnake.Embed):
    embed = None

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

    @staticmethod
    async def embed_builder(ctx, custom_color, custom_thumbnail, custom_title, description, fields, footer_text,
                            status):
        color = None
        thumbnail = None
        title = None
        add_failure_color = disnake.Color(0xf00a0a)  # Bright red
        add_failure_thumbnail = "https://bg3.wiki/w/images/thumb/3/3f/Bane_Spell.webp/380px-Bane_Spell.webp.png"
        add_failure_title = "Whoops."
        add_success_color = disnake.Color(0x0af021)  # Bright green
        add_success_thumbnail = "https://bg3.wiki/w/images/thumb/1/14/Bless.webp/380px-Bless.webp.png"
        add_success_title = "Nice."
        alert_color = disnake.Color(0xe0d902)  # Bright yellow
        alert_thumbnail = "https://bg3.wiki/w/images/thumb/4/4f/Generic_Threat.webp/380px-Generic_Threat.webp.png"
        alert_title = "Hm."
        deletion_color = disnake.Color(0xa80303)  # Mid. red
        deletion_thumbnail = "https://bg3.wiki/w/images/thumb/2/23/Disintegrate.webp/380px-Disintegrate.webp.png"
        deletion_title = "Oh?!"
        failure_color = disnake.Color(0x5e0606)  # Dark red
        failure_thumbnail = "https://bg3.wiki/w/images/thumb/c/c4/Harm.webp/380px-Harm.webp.png"
        failure_title = "Oops!"
        success_color = disnake.Color(0x023d08)  # Dark green
        success_thumbnail = "https://bg3.wiki/w/images/thumb/3/36/Heal.webp/380px-Heal.webp.png"
        success_title = "Cool!"
        unsure_color = disnake.Color(0x6e6b0e)  # Dark yellow
        unsure_thumbnail = "https://bg3.wiki/w/images/thumb/0/0a/Confusion.webp/380px-Confusion.webp.png"
        unsure_title = "Hm?"
        waiting_color = disnake.Color(0xa8a53e)  # Mid. yellow
        waiting_thumbnail = "https://bg3.wiki/w/images/thumb/5/5f/Slow.webp/380px-Slow.webp.png"
        waiting_title = "Hm..."
        if status == "add_failure":
            color = add_failure_color
            thumbnail = add_failure_thumbnail
            title = add_failure_title
        elif status == "add_success":
            color = add_success_color
            thumbnail = add_success_thumbnail
            title = add_success_title
        elif status == "alert":
            color = alert_color
            thumbnail = alert_thumbnail
            title = alert_title
        elif status == "deletion":
            color = deletion_color
            thumbnail = deletion_thumbnail
            title = deletion_title
        elif status == "failure":
            color = failure_color
            thumbnail = failure_thumbnail
            title = failure_title
        elif status == "success":
            color = success_color
            thumbnail = success_thumbnail
            title = success_title
        elif status == "unsure":
            color = unsure_color
            thumbnail = unsure_thumbnail
            title = unsure_title
        elif status == "waiting":
            color = waiting_color
            thumbnail = waiting_thumbnail
            title = waiting_title
        if custom_color is not None:
            color = custom_color
        if custom_thumbnail is not None:
            thumbnail = custom_thumbnail
        if custom_title is not None:
            title = custom_title
        embed = disnake.Embed(color=color, description=description, title=title)
        if fields is not None:
            for field in fields:
                embed.add_field(inline=bool(field["inline"]), name=field["name"], value=field["value"])
        if ctx.author.guild_avatar is None:
            author_icon = ctx.author.avatar.url
        elif ctx.author.guild_avatar is not None:
            author_icon = ctx.author.guild_avatar.url
        else:
            author_icon = unsure_thumbnail
        embed.set_author(icon_url=author_icon, name=ctx.author.nick)
        embed.set_footer(icon_url=ctx.guild.icon.url, text=f"{footer_text} | {ctx.guild.name}")
        embed.set_thumbnail(url=thumbnail)
        EmbedBuilder.embed = embed
