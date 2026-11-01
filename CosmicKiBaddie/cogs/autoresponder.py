"""
Cosmic ki baddie - Autoresponder Cog
Deterministic rule-based trigger engine with exact/contains/starts-with matching, cooldowns, and loop prevention.
"""

import discord
from discord.ext import commands
from discord import app_commands
import time
from typing import Optional
from config import COLOR_COSMIC_PURPLE, COLOR_SUCCESS, COLOR_WARNING, EMOJI_CHECK, EMOJI_CROSS
from database import db_manager

class Autoresponder(commands.Cog, name="Autoresponder"):
    """Rule-based keyword autoresponder for Side Quest Studio."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # In-memory cooldown tracker: (guild_id, rule_id) -> last_triggered_ts
        self.cooldowns: dict = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Loop prevention: Ignore bots and DMs
        if message.author.bot or not message.guild:
            return

        rules = await db_manager.get_autoresponders(message.guild.id)
        if not rules:
            return

        content = message.content.lower().strip()
        now = time.time()

        for rule in rules:
            if not rule["is_enabled"]:
                continue

            # Channel filter
            if rule["channel_id"] and rule["channel_id"] != message.channel.id:
                continue

            # Role filter
            if rule["role_id"]:
                author_roles = [r.id for r in message.author.roles]
                if rule["role_id"] not in author_roles:
                    continue

            # Cooldown check
            cd_key = (message.guild.id, rule["id"])
            if now - self.cooldowns.get(cd_key, 0) < rule["cooldown_sec"]:
                continue

            trigger = rule["trigger_text"]
            match_type = rule["match_type"]
            matched = False

            if match_type == "exact" and content == trigger:
                matched = True
            elif match_type == "contains" and trigger in content:
                matched = True
            elif match_type == "startswith" and content.startswith(trigger):
                matched = True

            if matched:
                self.cooldowns[cd_key] = now
                if rule["is_embed"]:
                    embed = discord.Embed(
                        description=rule["response_text"],
                        color=COLOR_COSMIC_PURPLE
                    )
                    await message.channel.send(embed=embed)
                else:
                    await message.channel.send(rule["response_text"])
                break  # Fire at most one autoresponder per message

    auto_group = app_commands.Group(name="autoresponder", description="Automated keyword response rules")

    @auto_group.command(name="add", description="Add an automated keyword response rule")
    @app_commands.describe(
        trigger="Trigger word or phrase",
        response="The response message to send",
        match_type="exact, contains, or startswith",
        is_embed="Send response wrapped in a sleek embed",
        channel="Restrict to a specific channel (optional)",
        cooldown="Cooldown between responses in seconds (default 5)"
    )
    @app_commands.choices(match_type=[
        app_commands.Choice(name="Exact match only", value="exact"),
        app_commands.Choice(name="Contains keyword anywhere in message", value="contains"),
        app_commands.Choice(name="Message starts with keyword", value="startswith")
    ])
    @commands.has_permissions(manage_guild=True)
    async def auto_add(
        self,
        interaction: discord.Interaction,
        trigger: str,
        response: str,
        match_type: app_commands.Choice[str],
        is_embed: bool = False,
        channel: Optional[discord.TextChannel] = None,
        cooldown: int = 5
    ):
        rule_id = await db_manager.add_autoresponder(
            guild_id=interaction.guild_id,
            trigger=trigger,
            response=response,
            match_type=match_type.value,
            is_embed=is_embed,
            channel_id=channel.id if channel else None,
            cooldown=max(1, min(3600, cooldown))
        )
        embed = discord.Embed(
            title=f"{EMOJI_CHECK} Autoresponder Rule Created (#{rule_id})",
            color=COLOR_SUCCESS
        )
        embed.add_field(name="Trigger", value=f"`{trigger}` ({match_type.name})", inline=True)
        embed.add_field(name="Response", value=response[:100], inline=False)
        if channel:
            embed.add_field(name="Channel", value=channel.mention, inline=True)
        await interaction.response.send_message(embed=embed)

    @auto_group.command(name="list", description="List all configured autoresponder rules")
    @commands.has_permissions(manage_guild=True)
    async def auto_list(self, interaction: discord.Interaction):
        rules = await db_manager.get_autoresponders(interaction.guild_id)
        if not rules:
            return await interaction.response.send_message("No autoresponder rules configured yet.", ephemeral=True)

        embed = discord.Embed(
            title="🤖 Configured Autoresponder Rules",
            color=COLOR_COSMIC_PURPLE
        )
        for r in rules[:20]:
            status = "🟢 Enabled" if r["is_enabled"] else "🔴 Disabled"
            embed.add_field(
                name=f"Rule #{r['id']} | `{r['trigger_text']}` [{r['match_type']}]",
                value=f"**Status:** {status} | **Cooldown:** {r['cooldown_sec']}s\n> {r['response_text'][:80]}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @auto_group.command(name="delete", description="Delete an autoresponder rule")
    @app_commands.describe(rule_id="ID of rule to delete")
    @commands.has_permissions(manage_guild=True)
    async def auto_delete(self, interaction: discord.Interaction, rule_id: int):
        success = await db_manager.delete_autoresponder(interaction.guild_id, rule_id)
        if success:
            await interaction.response.send_message(f"{EMOJI_CHECK} Rule #{rule_id} deleted successfully.")
        else:
            await interaction.response.send_message(f"{EMOJI_CROSS} Rule #{rule_id} not found.", ephemeral=True)

    @auto_group.command(name="toggle", description="Enable or disable an autoresponder rule")
    @app_commands.describe(rule_id="ID of rule to toggle", enable="True to enable, False to disable")
    @commands.has_permissions(manage_guild=True)
    async def auto_toggle(self, interaction: discord.Interaction, rule_id: int, enable: bool):
        success = await db_manager.toggle_autoresponder(interaction.guild_id, rule_id, enable)
        if success:
            state = "enabled" if enable else "disabled"
            await interaction.response.send_message(f"{EMOJI_CHECK} Rule #{rule_id} is now **{state}**.")
        else:
            await interaction.response.send_message(f"{EMOJI_CROSS} Rule #{rule_id} not found.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Autoresponder(bot))
