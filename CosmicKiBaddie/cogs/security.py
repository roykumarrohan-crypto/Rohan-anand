"""
Cosmic ki baddie - Anti-Nuke & Server Protection Cog
Monitors rapid destructive actions (mass bans, kicks, channel/role purges) and enforces safe modes.
"""

import discord
from discord.ext import commands
from discord import app_commands
import time
from typing import Optional
from config import COLOR_DANGER, COLOR_WARNING, COLOR_SUCCESS, COLOR_COSMIC_PURPLE, EMOJI_SHIELD, EMOJI_CHECK, EMOJI_CROSS
from database import db_manager

class Security(commands.Cog, name="Security"):
    """Anti-nuke protection, threshold rate-limiting, whitelist management, and emergency lockdown."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def is_action_exempt(self, guild: discord.Guild, user_id: int) -> bool:
        """Server owner and explicitly whitelisted users bypass anti-nuke limits."""
        if user_id == guild.owner_id or user_id == self.bot.user.id:
            return True
        return await db_manager.is_whitelisted(guild.id, user_id)

    async def handle_security_breach(self, guild: discord.Guild, perpetrator: discord.Member, action_name: str, count: int, threshold: int):
        """Enforces configured action when threshold is violated."""
        cfg = await db_manager.get_antinuke_config(guild.id)
        if not cfg.get("is_enabled", 1):
            return

        action_to_take = cfg.get("action_on_trigger", "QUARANTINE_ROLE")
        details = f"Exceeded threshold: {count}/{threshold} {action_name} actions within window."

        # Quarantine: strip dangerous permissions / remove administrative roles
        mitigated = False
        if action_to_take == "QUARANTINE_ROLE":
            dangerous_perms = ["administrator", "manage_guild", "manage_channels", "manage_roles", "ban_members", "kick_members"]
            roles_to_remove = []
            for r in perpetrator.roles:
                if r < guild.me.top_role and not r.is_default():
                    if any(getattr(r.permissions, p, False) for p in dangerous_perms):
                        roles_to_remove.append(r)
            if roles_to_remove:
                try:
                    await perpetrator.remove_roles(*roles_to_remove, reason="Cosmic Anti-Nuke: Triggered threshold breach")
                    mitigated = True
                except Exception:
                    pass

        await db_manager.log_antinuke_action(guild.id, perpetrator.id, action_name, details, mitigated=mitigated)

        # Notify via log channel or server owner
        g_cfg = await db_manager.get_guild_config(guild.id)
        log_ch_id = g_cfg.get("mod_log_channel_id") or g_cfg.get("general_log_channel_id")
        embed = discord.Embed(
            title="🚨 COSMIC ANTI-NUKE TRIGGERED",
            description=f"**Perpetrator:** {perpetrator.mention} (`{perpetrator.id}`)\n"
                        f"**Action:** `{action_name}` ({count} events within window)\n"
                        f"**Status:** {'Quarantined (roles stripped)' if mitigated else 'Alert Logged'}\n"
                        f"**Protection Mode:** `{cfg.get('protection_mode', 'SERVER_PROTECTION')}`",
            color=COLOR_DANGER,
            timestamp=discord.utils.utcnow()
        )
        if log_ch_id:
            ch = guild.get_channel(log_ch_id)
            if ch:
                await ch.send(content="@here", embed=embed)

    # ==========================
    # Discord Audit Log Event Listeners
    # ==========================
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        guild = channel.guild
        cfg = await db_manager.get_antinuke_config(guild.id)
        if not cfg.get("is_enabled", 1):
            return

        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                user = entry.user
                if not user or await self.is_action_exempt(guild, user.id):
                    return

                await db_manager.log_antinuke_action(guild.id, user.id, "channel_delete")
                count = await db_manager.get_recent_action_count(guild.id, user.id, "channel_delete", cfg.get("window_seconds", 60))
                thresh = cfg.get("channel_delete_threshold", 3)

                if count >= thresh and isinstance(user, discord.Member):
                    await self.handle_security_breach(guild, user, "mass_channel_delete", count, thresh)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        guild = role.guild
        cfg = await db_manager.get_antinuke_config(guild.id)
        if not cfg.get("is_enabled", 1):
            return

        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                user = entry.user
                if not user or await self.is_action_exempt(guild, user.id):
                    return

                await db_manager.log_antinuke_action(guild.id, user.id, "role_delete")
                count = await db_manager.get_recent_action_count(guild.id, user.id, "role_delete", cfg.get("window_seconds", 60))
                thresh = cfg.get("role_delete_threshold", 3)

                if count >= thresh and isinstance(user, discord.Member):
                    await self.handle_security_breach(guild, user, "mass_role_delete", count, thresh)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        cfg = await db_manager.get_antinuke_config(guild.id)
        if not cfg.get("is_enabled", 1):
            return

        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                actor = entry.user
                if not actor or await self.is_action_exempt(guild, actor.id):
                    return

                await db_manager.log_antinuke_action(guild.id, actor.id, "member_ban")
                count = await db_manager.get_recent_action_count(guild.id, actor.id, "member_ban", cfg.get("window_seconds", 60))
                thresh = cfg.get("kick_ban_threshold", 3)

                if count >= thresh and isinstance(actor, discord.Member):
                    await self.handle_security_breach(guild, actor, "mass_ban", count, thresh)
        except Exception:
            pass

    # ==========================
    # Security Commands
    # ==========================
    security_group = app_commands.Group(name="security", description="Server anti-nuke and security management")

    @security_group.command(name="status", description="View anti-nuke configuration and active protection mode")
    @commands.has_permissions(administrator=True)
    async def security_status(self, interaction: discord.Interaction):
        cfg = await db_manager.get_antinuke_config(interaction.guild_id)
        embed = discord.Embed(
            title="🛡️ Cosmic Anti-Nuke Status & Security Engine",
            color=COLOR_COSMIC_PURPLE,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="System State", value="🟢 ACTIVE" if cfg.get("is_enabled") else "🔴 DISABLED", inline=True)
        embed.add_field(name="Current Mode", value=f"`{cfg.get('protection_mode', 'SERVER_PROTECTION')}`", inline=True)
        embed.add_field(name="Action on Trigger", value=f"`{cfg.get('action_on_trigger', 'QUARANTINE_ROLE')}`", inline=True)
        embed.add_field(name="Channel Delete Limit", value=f"{cfg.get('channel_delete_threshold', 3)} / {cfg.get('window_seconds', 60)}s", inline=True)
        embed.add_field(name="Role Delete Limit", value=f"{cfg.get('role_delete_threshold', 3)} / {cfg.get('window_seconds', 60)}s", inline=True)
        embed.add_field(name="Kick/Ban Limit", value=f"{cfg.get('kick_ban_threshold', 3)} / {cfg.get('window_seconds', 60)}s", inline=True)

        await interaction.response.send_message(embed=embed)

    @security_group.command(name="mode", description="Switch server protection mode")
    @app_commands.describe(mode="SAFE_MODE (restrict sensitive commands), SERVER_PROTECTION (standard), or EMERGENCY_LOCKDOWN")
    @app_commands.choices(mode=[
        app_commands.Choice(name="SAFE MODE (Restrict bot mutations & hold automation)", value="SAFE_MODE"),
        app_commands.Choice(name="SERVER PROTECTION (Standard anti-nuke rate monitoring)", value="SERVER_PROTECTION"),
        app_commands.Choice(name="EMERGENCY LOCKDOWN (Lock down sensitive text channels)", value="EMERGENCY_LOCKDOWN")
    ])
    @commands.has_permissions(administrator=True)
    async def security_mode(self, interaction: discord.Interaction, mode: app_commands.Choice[str]):
        await db_manager.update_antinuke_config(interaction.guild_id, protection_mode=mode.value)
        if mode.value == "EMERGENCY_LOCKDOWN":
            await interaction.response.send_message(f"🚨 **EMERGENCY LOCKDOWN ACTIVATED!** Enhancing monitoring and restricting public channel creations.")
        else:
            await interaction.response.send_message(f"{EMOJI_CHECK} Protection mode switched to **{mode.name}**.")

    @security_group.command(name="whitelist", description="Add or remove trusted administrators from anti-nuke checks")
    @app_commands.describe(action="add or remove", user="Target user")
    @app_commands.choices(action=[
        app_commands.Choice(name="Add to Whitelist", value="add"),
        app_commands.Choice(name="Remove from Whitelist", value="remove")
    ])
    @commands.has_permissions(administrator=True)
    async def security_whitelist(self, interaction: discord.Interaction, action: app_commands.Choice[str], user: discord.Member):
        if action.value == "add":
            await db_manager.add_whitelist(interaction.guild_id, user.id, interaction.user.id)
            await interaction.response.send_message(f"{EMOJI_CHECK} Added {user.mention} to trusted security whitelist.")
        else:
            await db_manager.remove_whitelist(interaction.guild_id, user.id)
            await interaction.response.send_message(f"{EMOJI_CHECK} Removed {user.mention} from security whitelist.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Security(bot))
