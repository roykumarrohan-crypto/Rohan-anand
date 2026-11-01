"""
Cosmic ki baddie - Interactive Help Cog
Hybrid help system with interactive category select, usage examples, and required permissions.
"""

import discord
from discord.ext import commands
from discord import app_commands
from config import COLOR_COSMIC_PURPLE, COLOR_STELLAR_CYAN, EMOJI_SPARKLE
from database import db_manager

HELP_CATEGORIES = {
    "Moderation": {
        "emoji": "🛡️",
        "desc": "Server protection and member discipline tools",
        "commands": [
            {"cmd": "kick", "desc": "Kick a member from the server", "usage": "/kick @user [reason]", "perms": "Kick Members"},
            {"cmd": "ban", "desc": "Ban a user with optional message deletion", "usage": "/ban @user [days] [reason]", "perms": "Ban Members"},
            {"cmd": "unban", "desc": "Pardon and unban a user ID", "usage": "/unban <id> [reason]", "perms": "Ban Members"},
            {"cmd": "timeout", "desc": "Mute a user for X minutes", "usage": "/timeout @user <mins> [reason]", "perms": "Moderate Members"},
            {"cmd": "untimeout", "desc": "Remove active timeout", "usage": "/untimeout @user [reason]", "perms": "Moderate Members"},
            {"cmd": "warn", "desc": "Issue formal strike to a member", "usage": "/warn @user [reason]", "perms": "Manage Messages"},
            {"cmd": "warnings", "desc": "View strike history", "usage": "/warnings @user", "perms": "Manage Messages"},
            {"cmd": "clearwarns", "desc": "Reset member strikes", "usage": "/clearwarns @user", "perms": "Kick Members"},
            {"cmd": "slowmode", "desc": "Set channel rate limit", "usage": "/slowmode <seconds>", "perms": "Manage Channels"},
            {"cmd": "lock", "desc": "Prevent members from typing in channel", "usage": "/lock [#channel]", "perms": "Manage Channels"},
            {"cmd": "unlock", "desc": "Restore channel typing", "usage": "/unlock [#channel]", "perms": "Manage Channels"},
            {"cmd": "snipe", "desc": "View last deleted message", "usage": "/snipe", "perms": "Manage Messages"},
            {"cmd": "modlogs", "desc": "Inspect audit moderation logs", "usage": "/modlogs [@user]", "perms": "Kick Members"}
        ]
    },
    "Purge": {
        "emoji": "🧹",
        "desc": "Bulk message cleaner with filters",
        "commands": [
            {"cmd": "purge", "desc": "Clean messages with user/text/link/bot filters", "usage": "/purge amount:50 user:@spammer links_only:true", "perms": "Manage Messages"}
        ]
    },
    "Tickets": {
        "emoji": "🎫",
        "desc": "Support ticket system with transcripts and claims",
        "commands": [
            {"cmd": "ticket setup", "desc": "Link category, support role, and logs", "usage": "/ticket setup", "perms": "Administrator"},
            {"cmd": "ticket panel", "desc": "Deploy interactive ticket button panel", "usage": "/ticket panel [#channel]", "perms": "Administrator"},
            {"cmd": "ticket add", "desc": "Add member to current ticket", "usage": "/ticket add @user", "perms": "Manage Channels"},
            {"cmd": "ticket remove", "desc": "Remove member from current ticket", "usage": "/ticket remove @user", "perms": "Manage Channels"},
            {"cmd": "ticket claim", "desc": "Claim ticket handling", "usage": "/ticket claim", "perms": "Support Staff"},
            {"cmd": "ticket close", "desc": "Archive and lock ticket channel", "usage": "/ticket close", "perms": "Ticket Owner/Staff"},
            {"cmd": "ticket transcript", "desc": "Download text archive of discussion", "usage": "/ticket transcript", "perms": "Support Staff"}
        ]
    },
    "Roles & Permissions": {
        "emoji": "🎭",
        "desc": "Dynamic command authorization and self-assign panels",
        "commands": [
            {"cmd": "permissions set", "desc": "Grant or deny command access for a role", "usage": "/permissions set role:@Mod command:ban access:true", "perms": "Administrator"},
            {"cmd": "permissions module", "desc": "Toggle entire module for a role", "usage": "/permissions module module:tickets role:@Helper access:true", "perms": "Administrator"},
            {"cmd": "permissions view", "desc": "List all configured command overrides", "usage": "/permissions view", "perms": "Administrator"},
            {"cmd": "role panel", "desc": "Deploy interactive button self-role panel", "usage": "/role panel title:'Choose Roles' role1:@Gamer", "perms": "Administrator"}
        ]
    },
    "Security": {
        "emoji": "🛡️",
        "desc": "Anti-nuke safeguards and emergency lockdown",
        "commands": [
            {"cmd": "security status", "desc": "View active threshold rates & protection state", "usage": "/security status", "perms": "Administrator"},
            {"cmd": "security mode", "desc": "Switch SAFE MODE / SERVER PROTECTION / LOCKDOWN", "usage": "/security mode mode:SAFE_MODE", "perms": "Administrator"},
            {"cmd": "security whitelist", "desc": "Bypass trusted staff from anti-nuke kicks", "usage": "/security whitelist action:add user:@CoOwner", "perms": "Administrator"}
        ]
    },
    "Giveaways & Events": {
        "emoji": "🎉",
        "desc": "Community engagements, contests, and scheduled events",
        "commands": [
            {"cmd": "giveaway start", "desc": "Launch giveaway with interactive entry button", "usage": "/giveaway start prize:'Nitro' duration:'2h' winners:1", "perms": "Manage Guild"},
            {"cmd": "giveaway reroll", "desc": "Pick new random winner", "usage": "/giveaway reroll <id>", "perms": "Manage Guild"},
            {"cmd": "event create", "desc": "Schedule server event with RSVP buttons", "usage": "/event create title:'Game Night' in_hours:24", "perms": "Manage Events"},
            {"cmd": "event list", "desc": "View upcoming events and RSVP totals", "usage": "/event list", "perms": "@everyone"}
        ]
    },
    "Polls & Autoresponder": {
        "emoji": "📊",
        "desc": "Interactive polls and deterministic keyword automations",
        "commands": [
            {"cmd": "poll create", "desc": "Launch poll with up to 5 vote options", "usage": "/poll create question:'Next game?' option1:'Valorant' option2:'Minecraft'", "perms": "Manage Messages"},
            {"cmd": "poll results", "desc": "View live percentage progress bar tallies", "usage": "/poll results <poll_id>", "perms": "@everyone"},
            {"cmd": "autoresponder add", "desc": "Register keyword trigger and response", "usage": "/autoresponder add trigger:'hello' response:'Welcome!' match_type:exact", "perms": "Manage Guild"},
            {"cmd": "autoresponder list", "desc": "Inspect all auto responder rules", "usage": "/autoresponder list", "perms": "Manage Guild"}
        ]
    },
    "General & Setup": {
        "emoji": "⚙️",
        "desc": "System setup wizard, dashboard, and general utilities",
        "commands": [
            {"cmd": "dashboard", "desc": "Central in-Discord management control room", "usage": "/dashboard", "perms": "Administrator"},
            {"cmd": "setup start", "desc": "Step-by-step interactive onboarding wizard", "usage": "/setup start", "perms": "Administrator"},
            {"cmd": "setup status", "desc": "Overview of linked channels and roles", "usage": "/setup status", "perms": "Administrator"},
            {"cmd": "prefix", "desc": "View or set server command prefix", "usage": "/prefix [new_prefix]", "perms": "Administrator"},
            {"cmd": "rank", "desc": "Check your level and activity stats", "usage": "/rank [@user]", "perms": "@everyone"},
            {"cmd": "leaderboard", "desc": "Side Quest Studio top XP rankings", "usage": "/leaderboard", "perms": "@everyone"}
        ]
    }
}

class HelpSelect(discord.ui.Select):
    def __init__(self, prefix: str):
        options = []
        for cat_name, data in HELP_CATEGORIES.items():
            options.append(discord.SelectOption(
                label=cat_name,
                emoji=data["emoji"],
                description=data["desc"][:100]
            ))
        super().__init__(placeholder="Select a category to view commands...", min_values=1, max_values=1, options=options)
        self.prefix = prefix

    async def callback(self, interaction: discord.Interaction):
        cat_name = self.values[0]
        data = HELP_CATEGORIES[cat_name]

        embed = discord.Embed(
            title=f"{data['emoji']} {cat_name} Commands",
            description=f"{data['desc']}\n*Both Slash (`/`) and Prefix (`{self.prefix}`) commands supported.*",
            color=COLOR_COSMIC_PURPLE
        )

        for c in data["commands"]:
            embed.add_field(
                name=f"/{c['cmd']}",
                value=f"**Description:** {c['desc']}\n**Usage:** `{c['usage']}`\n**Perms:** `{c['perms']}`",
                inline=False
            )

        embed.set_footer(text=f"Cosmic ki baddie • Side Quest Studio | Prefix: {self.prefix}")
        await interaction.response.edit_message(embed=embed)


class HelpView(discord.ui.View):
    def __init__(self, prefix: str):
        super().__init__(timeout=180)
        self.add_item(HelpSelect(prefix))


class Help(commands.Cog, name="Help"):
    """Interactive help directory with category dropdowns."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.help_command = None  # Remove default unformatted help

    @commands.hybrid_command(name="help", description="Show the interactive Cosmic ki baddie command directory")
    async def help_command(self, ctx: commands.Context):
        prefix = await db_manager.get_prefix(ctx.guild.id if ctx.guild else None)

        embed = discord.Embed(
            title="🌌 Cosmic ki baddie • Command Directory",
            description=f"Welcome to **Side Quest Studio's** primary server management and automation engine!\n\n"
                        f"• **Current Prefix:** `{prefix}`\n"
                        f"• **Slash Commands:** Enabled (`/`)\n\n"
                        "Select any category from the dropdown menu below to explore detailed command syntax and permission requirements.",
            color=COLOR_COSMIC_PURPLE,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author.name} • Version 2.4.0-Production")

        view = HelpView(prefix)
        await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
