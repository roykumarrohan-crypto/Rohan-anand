"""
Cosmic ki baddie - Welcome & Goodbye System Cog
Aesthetic member onboarding for Side Quest Studio with autoroles, custom embeds, and DMs.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from config import COLOR_COSMIC_PURPLE, COLOR_SUCCESS, COLOR_DANGER, EMOJI_SPARKLE, EMOJI_CHECK
from database import db_manager

DEFAULT_WELCOME_TEXT = (
    "Another side quest unlocked! ✨\n\n"
    "Welcome {user} to **Side Quest Studio**!\n\n"
    "Your adventure starts here. Explore the channels, meet the community, and find your people.\n\n"
    "Don't forget to check out the rules!"
)

DEFAULT_GOODBYE_TEXT = (
    "**{user_name}** has completed their journey and left Side Quest Studio. Until next time traveler! 🌌"
)

class Welcome(commands.Cog, name="Welcome"):
    """Member onboarding, aesthetic embeds, autorole assignments, and departure logs."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        cfg = await db_manager.get_guild_config(guild.id)

        # 1. Automatic role assignment if configured
        autorole_id = cfg.get("autorole_id")
        if autorole_id:
            role = guild.get_role(autorole_id)
            if role and role < guild.me.top_role:
                try:
                    await member.add_roles(role, reason="Cosmic Welcome: Autorole assignment")
                except Exception:
                    pass

        # 2. Welcome Channel Announcement
        welcome_ch_id = cfg.get("welcome_channel_id")
        if welcome_ch_id:
            channel = guild.get_channel(welcome_ch_id)
            if channel and isinstance(channel, discord.TextChannel):
                custom_msg = cfg.get("welcome_message") or DEFAULT_WELCOME_TEXT
                formatted_body = custom_msg.replace("{user}", member.mention).replace("{user_name}", member.name).replace("{guild_name}", guild.name)

                embed = discord.Embed(
                    title=f"✨ Welcome to {guild.name}!",
                    description=formatted_body,
                    color=COLOR_COSMIC_PURPLE,
                    timestamp=discord.utils.utcnow()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Member #{guild.member_count} • Side Quest Studio", icon_url=guild.icon.url if guild.icon else None)

                try:
                    await channel.send(content=member.mention, embed=embed)
                except Exception:
                    pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        cfg = await db_manager.get_guild_config(guild.id)
        goodbye_ch_id = cfg.get("goodbye_channel_id")
        if goodbye_ch_id:
            channel = guild.get_channel(goodbye_ch_id)
            if channel and isinstance(channel, discord.TextChannel):
                custom_msg = cfg.get("goodbye_message") or DEFAULT_GOODBYE_TEXT
                formatted = custom_msg.replace("{user_name}", member.name).replace("{guild_name}", guild.name)

                embed = discord.Embed(
                    description=formatted,
                    color=COLOR_DANGER,
                    timestamp=discord.utils.utcnow()
                )
                embed.set_footer(text=f"Remaining Members: {guild.member_count}")
                try:
                    await channel.send(embed=embed)
                except Exception:
                    pass

    welcome_group = app_commands.Group(name="welcome", description="Configure server welcome system")

    @welcome_group.command(name="setup", description="Configure welcome channel and automatic role")
    @app_commands.describe(
        channel="Channel where welcome cards are posted",
        autorole="Role to automatically grant to newcomers",
        custom_message="Custom message body (use {user}, {guild_name})"
    )
    @commands.has_permissions(administrator=True)
    async def welcome_setup(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        autorole: Optional[discord.Role] = None,
        custom_message: Optional[str] = None
    ):
        updates = {"welcome_channel_id": channel.id}
        if autorole:
            updates["autorole_id"] = autorole.id
        if custom_message:
            updates["welcome_message"] = custom_message

        await db_manager.update_guild_config(interaction.guild_id, **updates)

        embed = discord.Embed(
            title=f"{EMOJI_CHECK} Welcome System Updated",
            color=COLOR_SUCCESS
        )
        embed.add_field(name="Welcome Channel", value=channel.mention, inline=True)
        if autorole:
            embed.add_field(name="Autorole", value=autorole.mention, inline=True)
        await interaction.response.send_message(embed=embed)

    @welcome_group.command(name="test", description="Send a preview of the welcome embed to this channel")
    @commands.has_permissions(administrator=True)
    async def welcome_test(self, interaction: discord.Interaction):
        guild = interaction.guild
        cfg = await db_manager.get_guild_config(guild.id)
        msg_text = cfg.get("welcome_message") or DEFAULT_WELCOME_TEXT
        formatted = msg_text.replace("{user}", interaction.user.mention).replace("{user_name}", interaction.user.name).replace("{guild_name}", guild.name)

        embed = discord.Embed(
            title=f"✨ Welcome to {guild.name}!",
            description=formatted,
            color=COLOR_COSMIC_PURPLE,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"Member #{guild.member_count} • Side Quest Studio", icon_url=guild.icon.url if guild.icon else None)
        await interaction.response.send_message(content=f"[Preview for {interaction.user.mention}]", embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
