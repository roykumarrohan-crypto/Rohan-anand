"""
Cosmic ki baddie - Role Management Cog
Create, delete, color, assign, and deploy interactive self-assignable role panels.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
from config import COLOR_COSMIC_PURPLE, COLOR_SUCCESS, COLOR_DANGER, EMOJI_CHECK, EMOJI_CROSS
from database import db_manager

class RoleButton(discord.ui.Button):
    def __init__(self, role_id: int, label: str, emoji: Optional[str] = None):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            emoji=emoji or "✨",
            custom_id=f"cosmic_selfrole_{role_id}"
        )
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = guild.get_role(self.role_id)
        if not role:
            return await interaction.response.send_message(f"{EMOJI_CROSS} That role no longer exists on this server.", ephemeral=True)

        user = interaction.user
        if role in user.roles:
            try:
                await user.remove_roles(role, reason="Self-assign role removal")
                await interaction.response.send_message(f"Removed role **{role.name}** from your profile.", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message(f"{EMOJI_CROSS} Bot cannot modify this role (role hierarchy).", ephemeral=True)
        else:
            try:
                await user.add_roles(role, reason="Self-assign role addition")
                await interaction.response.send_message(f"{EMOJI_CHECK} Granted you the **{role.name}** role!", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message(f"{EMOJI_CROSS} Bot cannot modify this role (role hierarchy).", ephemeral=True)


class SelfRolePanelView(discord.ui.View):
    """Dynamic view for self-assignable roles."""
    def __init__(self, role_configs: List[dict]):
        super().__init__(timeout=None)
        for r in role_configs[:25]:
            self.add_item(RoleButton(role_id=r["id"], label=r["name"], emoji=r.get("emoji")))


class Roles(commands.Cog, name="Roles"):
    """Role creation, editing, assignment, and interactive self-assign menus."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    role_group = app_commands.Group(name="role", description="Manage server roles")

    @role_group.command(name="create", description="Create a new role")
    @app_commands.describe(name="Role name", color_hex="Hex color e.g. #8A2BE2", mentionable="Allow anyone to mention this role")
    @commands.has_permissions(manage_roles=True)
    async def role_create(self, interaction: discord.Interaction, name: str, color_hex: Optional[str] = None, mentionable: bool = False):
        guild = interaction.guild
        color = discord.Color.default()
        if color_hex:
            try:
                cleaned = color_hex.lstrip("#")
                color = discord.Color(int(cleaned, 16))
            except ValueError:
                return await interaction.response.send_message(f"{EMOJI_CROSS} Invalid Hex color format. Example: `#00E5FF`", ephemeral=True)

        role = await guild.create_role(name=name, color=color, mentionable=mentionable, reason=f"Created by {interaction.user}")
        embed = discord.Embed(
            title=f"{EMOJI_CHECK} Role Created",
            description=f"Successfully created {role.mention} (`{role.id}`).",
            color=role.color or COLOR_SUCCESS
        )
        await interaction.response.send_message(embed=embed)

    @role_group.command(name="delete", description="Delete an existing role")
    @app_commands.describe(role="Role to delete", reason="Reason for deletion")
    @commands.has_permissions(manage_roles=True)
    async def role_delete(self, interaction: discord.Interaction, role: discord.Role, reason: str = "Admin action"):
        guild = interaction.guild
        if role >= guild.me.top_role:
            return await interaction.response.send_message(f"{EMOJI_CROSS} Cannot delete a role higher than the bot's highest role.", ephemeral=True)
        if role >= interaction.user.top_role and interaction.user.id != guild.owner_id:
            return await interaction.response.send_message(f"{EMOJI_CROSS} Cannot delete a role higher than your own highest role.", ephemeral=True)

        role_name = role.name
        await role.delete(reason=f"{interaction.user}: {reason}")
        await interaction.response.send_message(f"{EMOJI_CHECK} Deleted role **{role_name}**.")

    @role_group.command(name="assign", description="Assign a role to a member")
    @app_commands.describe(member="Target member", role="Role to give")
    @commands.has_permissions(manage_roles=True)
    async def role_assign(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        guild = interaction.guild
        if role >= guild.me.top_role:
            return await interaction.response.send_message(f"{EMOJI_CROSS} Cannot assign a role higher than the bot's role.", ephemeral=True)
        if role in member.roles:
            return await interaction.response.send_message(f"{member.mention} already has the {role.mention} role.", ephemeral=True)

        await member.add_roles(role, reason=f"Assigned by {interaction.user}")
        await interaction.response.send_message(f"{EMOJI_CHECK} Added {role.mention} to {member.mention}.")

    @role_group.command(name="remove", description="Remove a role from a member")
    @app_commands.describe(member="Target member", role="Role to remove")
    @commands.has_permissions(manage_roles=True)
    async def role_remove(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        guild = interaction.guild
        if role >= guild.me.top_role:
            return await interaction.response.send_message(f"{EMOJI_CROSS} Cannot remove a role higher than the bot's role.", ephemeral=True)
        if role not in member.roles:
            return await interaction.response.send_message(f"{member.mention} does not possess {role.mention}.", ephemeral=True)

        await member.remove_roles(role, reason=f"Removed by {interaction.user}")
        await interaction.response.send_message(f"{EMOJI_CHECK} Removed {role.mention} from {member.mention}.")

    @role_group.command(name="panel", description="Deploy a self-assignable role button panel")
    @app_commands.describe(
        title="Panel title",
        role1="First selectable role",
        role2="Second selectable role",
        role3="Third selectable role",
        role4="Fourth selectable role"
    )
    @commands.has_permissions(administrator=True)
    async def role_panel(
        self,
        interaction: discord.Interaction,
        title: str = "Select Your Roles",
        role1: discord.Role = None,
        role2: Optional[discord.Role] = None,
        role3: Optional[discord.Role] = None,
        role4: Optional[discord.Role] = None
    ):
        roles_to_add = [r for r in [role1, role2, role3, role4] if r is not None]
        if not roles_to_add:
            return await interaction.response.send_message(f"{EMOJI_CROSS} Please specify at least one role.", ephemeral=True)

        role_configs = [{"id": r.id, "name": r.name, "emoji": "⭐"} for r in roles_to_add]
        view = SelfRolePanelView(role_configs)

        embed = discord.Embed(
            title=f"🎭 {title}",
            description="Click the buttons below to toggle your roles.\n" +
                        "\n".join([f"• {r.mention}" for r in roles_to_add]),
            color=COLOR_COSMIC_PURPLE
        )
        embed.set_footer(text="Side Quest Studio • Self Roles")
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"{EMOJI_CHECK} Role panel deployed successfully!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))
