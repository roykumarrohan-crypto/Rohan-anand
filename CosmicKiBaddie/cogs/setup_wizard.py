"""
Cosmic ki baddie - Setup Wizard Cog
Interactive multi-step server onboarding wizard with dropdowns, buttons, and validation.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from config import COLOR_COSMIC_PURPLE, COLOR_SUCCESS, COLOR_STELLAR_CYAN, EMOJI_CHECK, EMOJI_CROSS
from database import db_manager

class WizardStepChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, key: str, placeholder: str):
        super().__init__(
            placeholder=placeholder,
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            custom_id=f"wizard_ch_{key}"
        )
        self.key = key

    async def callback(self, interaction: discord.Interaction):
        ch = self.values[0]
        updates = {self.key: ch.id}
        await db_manager.update_guild_config(interaction.guild_id, **updates)
        await interaction.response.send_message(f"{EMOJI_CHECK} Configured `{self.key}` to {ch.mention}!", ephemeral=True)


class WizardStepRoleSelect(discord.ui.RoleSelect):
    def __init__(self, key: str, placeholder: str):
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            custom_id=f"wizard_role_{key}"
        )
        self.key = key

    async def callback(self, interaction: discord.Interaction):
        role = self.values[0]
        updates = {self.key: role.id}
        await db_manager.update_guild_config(interaction.guild_id, **updates)
        await interaction.response.send_message(f"{EMOJI_CHECK} Configured `{self.key}` to {role.mention}!", ephemeral=True)


class SetupWizardView(discord.ui.View):
    def __init__(self, step: int = 1):
        super().__init__(timeout=300)
        self.step = step
        self.build_step_items()

    def build_step_items(self):
        self.clear_items()
        if self.step == 1:
            # Welcome & Autorole
            self.add_item(WizardStepChannelSelect("welcome_channel_id", "Select Welcome Channel..."))
            self.add_item(WizardStepRoleSelect("autorole_id", "Select Automatic Newcomer Role..."))
        elif self.step == 2:
            # Audit Logs
            self.add_item(WizardStepChannelSelect("general_log_channel_id", "Select General Log Channel..."))
            self.add_item(WizardStepChannelSelect("mod_log_channel_id", "Select Moderation Log Channel..."))
        elif self.step == 3:
            # Ticket System
            self.add_item(WizardStepRoleSelect("ticket_support_role_id", "Select Ticket Support Staff Role..."))
            self.add_item(WizardStepChannelSelect("ticket_log_channel_id", "Select Ticket Transcripts Log Channel..."))

        # Nav Buttons
        if self.step > 1:
            prev_btn = discord.ui.Button(label="Previous", style=discord.ButtonStyle.secondary, emoji="⬅️")
            prev_btn.callback = self.go_prev
            self.add_item(prev_btn)

        if self.step < 3:
            next_btn = discord.ui.Button(label="Next Step", style=discord.ButtonStyle.primary, emoji="➡️")
            next_btn.callback = self.go_next
            self.add_item(next_btn)

        finish_btn = discord.ui.Button(label="Complete Setup", style=discord.ButtonStyle.success, emoji="✅")
        finish_btn.callback = self.complete_wizard
        self.add_item(finish_btn)

    async def go_next(self, interaction: discord.Interaction):
        self.step += 1
        self.build_step_items()
        embed = self.get_step_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def go_prev(self, interaction: discord.Interaction):
        self.step -= 1
        self.build_step_items()
        embed = self.get_step_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def complete_wizard(self, interaction: discord.Interaction):
        cfg = await db_manager.get_guild_config(interaction.guild_id)
        embed = discord.Embed(
            title="🎉 Side Quest Studio • Setup Complete!",
            description="All essential modules have been linked with persistent SQLite storage.\n"
                        "You can refine settings anytime with `/dashboard` or `/setup status`.",
            color=COLOR_SUCCESS
        )
        self.clear_items()
        await interaction.response.edit_message(embed=embed, view=self)

    def get_step_embed(self) -> discord.Embed:
        titles = {
            1: "Step 1: Welcome Gate & Autoroles ✨",
            2: "Step 2: Server Audit & Mod Logs 🛡️",
            3: "Step 3: Support Tickets & Staff 🎫"
        }
        descs = {
            1: "Configure where new travelers are welcomed and which role they automatically receive.",
            2: "Select audit channels for tracking deleted messages, member leaves, and moderation cases.",
            3: "Set up the support role who can view and claim private support tickets."
        }
        embed = discord.Embed(
            title=titles.get(self.step, "Cosmic Setup"),
            description=descs.get(self.step, ""),
            color=COLOR_COSMIC_PURPLE
        )
        embed.set_footer(text=f"Wizard Step {self.step} of 3 • Side Quest Studio")
        return embed


class SetupWizard(commands.Cog, name="Setup"):
    """Guided onboarding wizard to configure the bot step by step."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    setup_group = app_commands.Group(name="setup", description="Server configuration wizard")

    @setup_group.command(name="start", description="Launch the interactive Side Quest Studio setup wizard")
    @commands.has_permissions(administrator=True)
    async def setup_start(self, interaction: discord.Interaction):
        view = SetupWizardView(step=1)
        embed = view.get_step_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @setup_group.command(name="status", description="Display current server configuration summary")
    @commands.has_permissions(administrator=True)
    async def setup_status(self, interaction: discord.Interaction):
        guild = interaction.guild
        cfg = await db_manager.get_guild_config(guild.id)
        anti = await db_manager.get_antinuke_config(guild.id)

        embed = discord.Embed(
            title="🌌 Side Quest Studio • Configuration Status",
            color=COLOR_STELLAR_CYAN,
            timestamp=discord.utils.utcnow()
        )

        def ch_fmt(cid):
            if not cid:
                return "*Not Set*"
            ch = guild.get_channel(cid)
            return ch.mention if ch else f"ID: {cid}"

        def role_fmt(rid):
            if not rid:
                return "*Not Set*"
            r = guild.get_role(rid)
            return r.mention if r else f"ID: {rid}"

        embed.add_field(name="Default Prefix", value=f"`{cfg.get('prefix', '!')}`", inline=True)
        embed.add_field(name="Welcome Channel", value=ch_fmt(cfg.get("welcome_channel_id")), inline=True)
        embed.add_field(name="Autorole", value=role_fmt(cfg.get("autorole_id")), inline=True)
        embed.add_field(name="General Logs", value=ch_fmt(cfg.get("general_log_channel_id")), inline=True)
        embed.add_field(name="Mod Logs", value=ch_fmt(cfg.get("mod_log_channel_id")), inline=True)
        embed.add_field(name="Ticket Support Role", value=role_fmt(cfg.get("ticket_support_role_id")), inline=True)
        embed.add_field(name="Anti-Nuke", value="🟢 Enabled" if anti.get("is_enabled") else "🔴 Disabled", inline=True)
        embed.add_field(name="Security Mode", value=f"`{anti.get('protection_mode')}`", inline=True)

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(SetupWizard(bot))
