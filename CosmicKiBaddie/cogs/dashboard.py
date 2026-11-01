"""
Cosmic ki baddie - Central Dashboard Cog
All-in-one Discord-native server control panel with category select and instant toggles.
"""

import discord
from discord.ext import commands
from discord import app_commands
from config import COLOR_COSMIC_PURPLE, COLOR_SUCCESS, COLOR_STELLAR_CYAN, COLOR_DANGER, EMOJI_SHIELD, EMOJI_CHECK, EMOJI_TICKET
from database import db_manager

class DashboardCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Server Overview", emoji="🌌", value="overview", description="System health, guild stats, and active status"),
            discord.SelectOption(label="Security & Anti-Nuke", emoji="🛡️", value="security", description="Rate limits, safe mode, and audit safeguards"),
            discord.SelectOption(label="Support Tickets", emoji="🎫", value="tickets", description="Categories, support roles, and transcripts"),
            discord.SelectOption(label="Audit Logging", emoji="📜", value="logs", description="Message, voice, and member event channels"),
            discord.SelectOption(label="Welcome & Onboarding", emoji="✨", value="welcome", description="Autoroles, greeting channels, and cards"),
            discord.SelectOption(label="Autoresponder & Triggers", emoji="🤖", value="auto", description="Keyword rules, match types, and cooldowns")
        ]
        super().__init__(placeholder="Navigate Management Dashboard...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        cat = self.values[0]
        guild = interaction.guild
        cfg = await db_manager.get_guild_config(guild.id)
        anti = await db_manager.get_antinuke_config(guild.id)

        if cat == "overview":
            embed = discord.Embed(
                title="🌌 Side Quest Studio • Control Hub",
                description="Centralized administration panel for Cosmic ki baddie.",
                color=COLOR_COSMIC_PURPLE
            )
            embed.add_field(name="Total Members", value=str(guild.member_count), inline=True)
            embed.add_field(name="Text Channels", value=str(len(guild.text_channels)), inline=True)
            embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
            embed.add_field(name="Active Mode", value=f"`{anti.get('protection_mode', 'SERVER_PROTECTION')}`", inline=True)
            embed.add_field(name="Prefix", value=f"`{cfg.get('prefix', '!')}`", inline=True)
            embed.add_field(name="Database Engine", value="SQLite (WAL Async)", inline=True)

        elif cat == "security":
            embed = discord.Embed(
                title="🛡️ Security & Anti-Nuke Settings",
                description="Thresholds for rapid bulk mutations.",
                color=COLOR_DANGER
            )
            embed.add_field(name="Anti-Nuke Protection", value="🟢 ACTIVE" if anti.get("is_enabled") else "🔴 DISABLED", inline=True)
            embed.add_field(name="Protection Mode", value=f"`{anti.get('protection_mode')}`", inline=True)
            embed.add_field(name="Max Bans / 60s", value=str(anti.get("kick_ban_threshold", 3)), inline=True)
            embed.add_field(name="Max Channel Deletes", value=str(anti.get("channel_delete_threshold", 3)), inline=True)

        elif cat == "tickets":
            embed = discord.Embed(
                title="🎫 Support Ticket Hub",
                color=COLOR_COSMIC_PURPLE
            )
            support_role = guild.get_role(cfg.get("ticket_support_role_id")) if cfg.get("ticket_support_role_id") else None
            ticket_cat = guild.get_channel(cfg.get("ticket_category_id")) if cfg.get("ticket_category_id") else None
            embed.add_field(name="Support Team Role", value=support_role.mention if support_role else "*Not Assigned*", inline=True)
            embed.add_field(name="Ticket Category", value=ticket_cat.name if ticket_cat else "*Not Assigned*", inline=True)
            embed.add_field(name="Transcript Archive", value="Enabled (SQLite & TXT)", inline=True)

        elif cat == "logs":
            embed = discord.Embed(
                title="📜 Server Audit Logs",
                color=COLOR_STELLAR_CYAN
            )
            mod_ch = guild.get_channel(cfg.get("mod_log_channel_id")) if cfg.get("mod_log_channel_id") else None
            gen_ch = guild.get_channel(cfg.get("general_log_channel_id")) if cfg.get("general_log_channel_id") else None
            embed.add_field(name="Mod Logs", value=mod_ch.mention if mod_ch else "*Disabled*", inline=True)
            embed.add_field(name="General Logs", value=gen_ch.mention if gen_ch else "*Disabled*", inline=True)

        elif cat == "welcome":
            embed = discord.Embed(
                title="✨ Member Welcome Gate",
                color=COLOR_SUCCESS
            )
            wel_ch = guild.get_channel(cfg.get("welcome_channel_id")) if cfg.get("welcome_channel_id") else None
            auto_r = guild.get_role(cfg.get("autorole_id")) if cfg.get("autorole_id") else None
            embed.add_field(name="Welcome Channel", value=wel_ch.mention if wel_ch else "*Disabled*", inline=True)
            embed.add_field(name="Autorole", value=auto_r.mention if auto_r else "*None*", inline=True)

        elif cat == "auto":
            rules = await db_manager.get_autoresponders(guild.id)
            embed = discord.Embed(
                title="🤖 Autoresponder Configuration",
                description=f"Active custom rules: **{len(rules)}**",
                color=COLOR_COSMIC_PURPLE
            )
            for r in rules[:5]:
                embed.add_field(name=f"`{r['trigger_text']}` ({r['match_type']})", value=f"> {r['response_text'][:50]}", inline=False)

        await interaction.response.edit_message(embed=embed)


class DashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(DashboardCategorySelect())

    @discord.ui.button(label="Toggle Safe Mode", style=discord.ButtonStyle.danger, emoji="🔒", row=1)
    async def toggle_safemode(self, interaction: discord.Interaction, button: discord.ui.Button):
        anti = await db_manager.get_antinuke_config(interaction.guild_id)
        current = anti.get("protection_mode", "SERVER_PROTECTION")
        new_mode = "SAFE_MODE" if current != "SAFE_MODE" else "SERVER_PROTECTION"
        await db_manager.update_antinuke_config(interaction.guild_id, protection_mode=new_mode)
        await interaction.response.send_message(f"{EMOJI_CHECK} Protection mode switched to **`{new_mode}`**.", ephemeral=True)


class Dashboard(commands.Cog, name="Dashboard"):
    """In-Discord management control center."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="dashboard", description="Open the in-Discord server management dashboard")
    @commands.has_permissions(administrator=True)
    async def dashboard(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🌌 Side Quest Studio • Central Command Dashboard",
            description="Select any administrative category from the dropdown below to view or manage live settings without opening Python source files.",
            color=COLOR_COSMIC_PURPLE,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
        embed.set_footer(text="Cosmic ki baddie • Native Management Engine")

        view = DashboardView()
        await ctx.send(embed=embed, view=view, ephemeral=True)

    @commands.hybrid_command(name="prefix", description="View or change the custom server command prefix")
    @app_commands.describe(new_prefix="New command prefix (e.g. ?, ., !)")
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx: commands.Context, new_prefix: Optional[str] = None):
        if not new_prefix:
            curr = await db_manager.get_prefix(ctx.guild.id)
            return await ctx.send(f"Current server command prefix is: `{curr}` (Example: `{curr}help`)")

        clean_p = new_prefix.strip()[:5]
        await db_manager.set_prefix(ctx.guild.id, clean_p)
        await ctx.send(f"{EMOJI_CHECK} Command prefix updated to: `{clean_p}`. Commands can now be triggered via `{clean_p}help`, `{clean_p}ban`, etc.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Dashboard(bot))
