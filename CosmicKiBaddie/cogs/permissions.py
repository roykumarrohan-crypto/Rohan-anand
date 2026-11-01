"""
Cosmic ki baddie - Permissions Override Cog
Granular role and command permission management without touching source files.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from config import COLOR_COSMIC_PURPLE, COLOR_SUCCESS, COLOR_DANGER, EMOJI_CHECK, EMOJI_CROSS, EMOJI_SHIELD
from database import db_manager

class Permissions(commands.Cog, name="Permissions"):
    """Manage dynamic role-based command and module access rules."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    perm_group = app_commands.Group(name="permissions", description="Configure command & module access for roles")

    @perm_group.command(name="set", description="Set role or member permission for a specific bot command")
    @app_commands.describe(
        command="Name of the bot command (e.g. ban, kick, purge, ticket)",
        role="Role to grant or deny access to",
        user="Specific user to grant or deny access to (optional)",
        access="Allow (True) or Deny (False)"
    )
    @commands.has_permissions(administrator=True)
    async def perm_set(
        self,
        interaction: discord.Interaction,
        command: str,
        access: bool,
        role: Optional[discord.Role] = None,
        user: Optional[discord.Member] = None
    ):
        if not role and not user:
            return await interaction.response.send_message(f"{EMOJI_CROSS} You must provide either a role or a user.", ephemeral=True)

        entity_type = "role" if role else "user"
        entity_id = role.id if role else user.id
        entity_name = role.name if role else str(user)

        await db_manager.set_command_access(
            guild_id=interaction.guild_id,
            entity_type=entity_type,
            entity_id=entity_id,
            command_name=command.lower().strip(),
            access=access
        )

        status_str = "ALLOWED" if access else "DENIED"
        embed = discord.Embed(
            title=f"{EMOJI_CHECK} Command Permission Updated",
            description=f"Command **`/{command.lower()}`** is now **{status_str}** for {role.mention if role else user.mention}.",
            color=COLOR_SUCCESS if access else COLOR_DANGER
        )
        await interaction.response.send_message(embed=embed)

    @perm_group.command(name="module", description="Set permission for an entire cog module (e.g. moderation, tickets, purge)")
    @app_commands.describe(
        module="Module name (moderation, purge, tickets, giveaways, security, etc.)",
        role="Role to grant or deny access to",
        access="Allow (True) or Deny (False)"
    )
    @commands.has_permissions(administrator=True)
    async def perm_module(self, interaction: discord.Interaction, module: str, role: discord.Role, access: bool):
        await db_manager.set_module_access(
            guild_id=interaction.guild_id,
            entity_type="role",
            entity_id=role.id,
            module_name=module.lower().strip(),
            access=access
        )
        status_str = "ALLOWED" if access else "DENIED"
        embed = discord.Embed(
            title=f"{EMOJI_CHECK} Module Permission Updated",
            description=f"Module **`{module.lower()}`** is now **{status_str}** for {role.mention}.",
            color=COLOR_SUCCESS if access else COLOR_DANGER
        )
        await interaction.response.send_message(embed=embed)

    @perm_group.command(name="view", description="View all customized bot command permissions for this server")
    @commands.has_permissions(administrator=True)
    async def perm_view(self, interaction: discord.Interaction):
        perms = await db_manager.get_all_permissions(interaction.guild_id)
        cmds = perms["commands"]
        mods = perms["modules"]

        if not cmds and not mods:
            return await interaction.response.send_message("No custom command/module overrides configured yet. Standard Discord permissions apply.", ephemeral=True)

        embed = discord.Embed(
            title="🛡️ Bot Permission Hierarchy & Overrides",
            description="Administrators always possess full override access.",
            color=COLOR_COSMIC_PURPLE
        )

        if cmds:
            lines = []
            for c in cmds[:15]:
                target = f"<@&{c['entity_id']}>" if c['entity_type'] == 'role' else f"<@{c['entity_id']}>"
                status = "✅ ALLOW" if c['access'] else "❌ DENY"
                lines.append(f"• `{c['command_name']}` -> {target} [{status}]")
            embed.add_field(name="Command Rules", value="\n".join(lines), inline=False)

        if mods:
            lines = []
            for m in mods[:15]:
                target = f"<@&{m['entity_id']}>" if m['entity_type'] == 'role' else f"<@{m['entity_id']}>"
                status = "✅ ALLOW" if m['access'] else "❌ DENY"
                lines.append(f"• Module `{m['module_name']}` -> {target} [{status}]")
            embed.add_field(name="Module Rules", value="\n".join(lines), inline=False)

        await interaction.response.send_message(embed=embed)


async def check_user_command_access(guild: discord.Guild, member: discord.Member, command_name: str, module_name: Optional[str] = None) -> bool:
    """
    Central permission resolver:
    1. Server Owner & Discord Administrators always have access.
    2. Explicit user deny -> Deny. Explicit user allow -> Allow.
    3. Role deny -> Deny. Role allow -> Allow.
    4. Module rules fallbacks.
    5. Default to True if no overrides exist.
    """
    if member.id == guild.owner_id or member.guild_permissions.administrator:
        return True

    # User-level check
    user_access = await db_manager.get_command_access(guild.id, member.id, command_name)
    if user_access is not None:
        return user_access

    # Role-level checks
    for role in member.roles:
        role_access = await db_manager.get_command_access(guild.id, role.id, command_name)
        if role_access is False:
            return False  # Deny takes priority
        if role_access is True:
            return True

    # Module level checks if available
    if module_name:
        for role in member.roles:
            mod_access = await db_manager.get_module_access(guild.id, role.id, module_name)
            if mod_access is False:
                return False
            if mod_access is True:
                return True

    return True

async def setup(bot: commands.Bot):
    await bot.add_cog(Permissions(bot))
