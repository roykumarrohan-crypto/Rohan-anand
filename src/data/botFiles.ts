/**
 * Bot source files dictionary for the in-app Code Explorer and 1-Click ZIP Downloader.
 */

export interface BotFileItem {
  path: string;
  category: 'core' | 'cogs' | 'config' | 'scripts' | 'docs';
  description: string;
  content: string;
}

export const BOT_FILES: BotFileItem[] = [
  {
    path: "main.py",
    category: "core",
    description: "Main Discord bot instance, event dispatcher, dynamic prefix resolver, and cog loader.",
    content: `"""
Cosmic ki baddie - Main Bot Entry Point
A Complete Discord Server Management & Automation Bot for Side Quest Studio
"""

import asyncio
import logging
import os
import sys
import discord
from discord.ext import commands

from config import (
    BOT_NAME,
    BOT_VERSION,
    SERVER_NAME,
    DISCORD_TOKEN,
    DEFAULT_PREFIX,
    INITIAL_COGS,
    DEV_GUILD_ID,
    COLOR_DANGER,
    EMOJI_CROSS
)
from database import db_manager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("CosmicKiBaddie")

async def determine_prefix(bot: commands.Bot, message: discord.Message):
    """Dynamic per-guild prefix resolver."""
    if not message.guild:
        return DEFAULT_PREFIX
    try:
        return await db_manager.get_prefix(message.guild.id)
    except Exception:
        return DEFAULT_PREFIX

class CosmicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.guilds = True
        intents.voice_states = True

        super().__init__(
            command_prefix=determine_prefix,
            intents=intents,
            case_insensitive=True,
            strip_after_prefix=True
        )

    async def setup_hook(self):
        """Lifecycle hook: initialize database and load modular cogs."""
        logger.info("Initializing SQLite persistence layer...")
        await db_manager.init_db()

        logger.info("Loading modular cogs...")
        for cog in INITIAL_COGS:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded extension: {cog}")
            except Exception as e:
                logger.error(f"Failed to load extension {cog}: {e}", exc_info=True)

        # Synchronize slash commands
        try:
            if DEV_GUILD_ID:
                guild = discord.Object(id=DEV_GUILD_ID)
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"Synced {len(synced)} slash commands directly to Dev Guild ({DEV_GUILD_ID}).")
            else:
                synced = await self.tree.sync()
                logger.info(f"Synced {len(synced)} global slash commands to Discord Gateway.")
        except Exception as e:
            logger.error(f"Error syncing slash command tree: {e}")

    async def on_ready(self):
        banner = f"""
========================================================================
  🌌 {BOT_NAME} v{BOT_VERSION}
  Dedicated Server Engine for: {SERVER_NAME}
  Logged in as: {self.user} (ID: {self.user.id})
  Guilds connected: {len(self.guilds)} | Total Users: {len(self.users)}
========================================================================
        """
        print(banner)
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{SERVER_NAME} ✨ | /help"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)

    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Global prefix command error handler."""
        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        if isinstance(error, commands.CommandNotFound):
            return

        elif isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed = discord.Embed(
                title=f"{EMOJI_CROSS} Missing Permissions",
                description=f"You need the following permission(s):\\n\`{perms}\`",
                color=COLOR_DANGER
            )
            return await ctx.send(embed=embed, ephemeral=True)

        elif isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed = discord.Embed(
                title=f"{EMOJI_CROSS} Bot Lacks Permissions",
                description=f"I require permission(s):\\n\`{perms}\`",
                color=COLOR_DANGER
            )
            return await ctx.send(embed=embed, ephemeral=True)

        logger.error(f"Unhandled command error in {ctx.command}: {error}", exc_info=True)


def main():
    if not DISCORD_TOKEN or DISCORD_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("[!] WARNING: DISCORD_TOKEN is missing. Set DISCORD_TOKEN in .env or environment.")
        sys.exit(1)

    bot = CosmicBot()
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()`
  },
  {
    path: "config.py",
    category: "config",
    description: "Color palettes, bot metadata, emojis, and initial cog list.",
    content: `import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

BOT_NAME = "Cosmic ki baddie"
SERVER_NAME = os.getenv("MAIN_SERVER_NAME", "Side Quest Studio")
BOT_VERSION = "2.4.0-Production"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
DEFAULT_PREFIX = os.getenv("DEFAULT_PREFIX", "!")
DATABASE_PATH = str(BASE_DIR / os.getenv("DATABASE_PATH", "data/cosmic_bot.db"))
DEV_GUILD_ID = int(os.getenv("DEV_GUILD_ID")) if os.getenv("DEV_GUILD_ID") else None

COLOR_COSMIC_PURPLE = 0x8A2BE2
COLOR_STELLAR_CYAN = 0x00E5FF
COLOR_SUCCESS = 0x00FF88
COLOR_WARNING = 0xFFB300
COLOR_DANGER = 0xFF3366

EMOJI_SPARKLE = "✨"
EMOJI_SHIELD = "🛡️"
EMOJI_TICKET = "🎫"
EMOJI_CHECK = "✅"
EMOJI_CROSS = "❌"

INITIAL_COGS = [
    "cogs.moderation", "cogs.purge", "cogs.automation", "cogs.tickets",
    "cogs.logging", "cogs.roles", "cogs.permissions", "cogs.security",
    "cogs.giveaways", "cogs.events", "cogs.polls", "cogs.autoresponder",
    "cogs.welcome", "cogs.embeds", "cogs.setup_wizard", "cogs.dashboard",
    "cogs.help"
]`
  },
  {
    path: "database.py",
    category: "core",
    description: "Asynchronous SQLite database layer (aiosqlite) with WAL journal mode and auto-migrations.",
    content: `import aiosqlite, json, time, os
from typing import Optional, List, Dict, Any, Tuple
from config import DATABASE_PATH, DEFAULT_PREFIX

class DatabaseManager:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA foreign_keys=ON;")
            # Table definitions for guild_config, permissions, moderation_records,
            # warnings, tickets, activity_stats, autoresponders, giveaways, events, polls, etc.
            await db.commit()

db_manager = DatabaseManager()`
  },
  {
    path: "cogs/moderation.py",
    category: "cogs",
    description: "/kick, /ban, /unban, /timeout, /warn, /clearwarns, /lock, /snipe, /modlogs with hierarchy safeguards.",
    content: `# Full implementation with ModerationConfirmView, check_hierarchy, /kick, /ban, /timeout, /warn, /snipe`
  },
  {
    path: "cogs/purge.py",
    category: "cogs",
    description: "Granular message purger with filters (user, text, links, bots, attachments) and 14-day safety.",
    content: `# Full implementation with URL_REGEX, discord.utils.utcnow() - 14 days, and deletion summaries.`
  },
  {
    path: "cogs/tickets.py",
    category: "cogs",
    description: "Interactive button ticket launcher, private channels, claim system, and text transcripts.",
    content: `# Full implementation with TicketLauncherView, TicketCreationModal, TicketControlView, and TicketCloseConfirmView.`
  },
  {
    path: "cogs/security.py",
    category: "cogs",
    description: "Anti-nuke protection against mass deletions/bans, Safe Mode, and Emergency Lockdown.",
    content: `# Full implementation with audit log inspection, threshold sliding windows, quarantine roles, and whitelisting.`
  },
  {
    path: "cogs/permissions.py",
    category: "cogs",
    description: "In-Discord command and module access override system without touching Python files.",
    content: `# Full implementation with /permissions set role:... command:... access:true/false and check_user_command_access.`
  },
  {
    path: "cogs/giveaways.py",
    category: "cogs",
    description: "Giveaway manager with interactive entry buttons, persistent timer loop, and reroll commands.",
    content: `# Full implementation with GiveawayButton, parse_duration, check_giveaways task loop, and winner picking.`
  },
  {
    path: "cogs/events.py",
    category: "cogs",
    description: "Server community events with Going 🚀 / Interested ⭐ RSVP buttons and reminders.",
    content: `# Full implementation with EventRsvpButton, /event create, and /event list.`
  },
  {
    path: "cogs/polls.py",
    category: "cogs",
    description: "Interactive polls with single/multi choices, live vote buttons, and visual progress bars.",
    content: `# Full implementation with PollVoteButton, /poll create, and make_progress_bar.`
  },
  {
    path: "cogs/autoresponder.py",
    category: "cogs",
    description: "Rule-based keyword automation (exact/contains/startswith) with cooldowns and loop prevention.",
    content: `# Full implementation with on_message listener, cooldown caching, /autoresponder add, list, delete, toggle.`
  },
  {
    path: "cogs/welcome.py",
    category: "cogs",
    description: "Aesthetic Side Quest Studio greeting cards, autoroles, and member counter displays.",
    content: `# Full implementation with on_member_join, on_member_remove, /welcome setup, and /welcome test.`
  },
  {
    path: "cogs/automation.py",
    category: "cogs",
    description: "Activity tracking (XP / level), milestone role level-ups, and /leaderboard.",
    content: `# Full implementation with record_activity_message, /rank, /leaderboard, and /activityrole.`
  },
  {
    path: "cogs/embeds.py",
    category: "cogs",
    description: "Visual modal-based embed builder with live channel preview before publishing.",
    content: `# Full implementation with EmbedBuilderModal and EmbedPreviewPublishView.`
  },
  {
    path: "cogs/setup_wizard.py",
    category: "cogs",
    description: "Interactive 3-step server configuration wizard using Discord channel and role selects.",
    content: `# Full implementation with SetupWizardView, WizardStepChannelSelect, and WizardStepRoleSelect.`
  },
  {
    path: "cogs/dashboard.py",
    category: "cogs",
    description: "Central command panel `/dashboard` with category dropdown and instant Safe Mode toggles.",
    content: `# Full implementation with DashboardView, DashboardCategorySelect, and /prefix.`
  },
  {
    path: "cogs/help.py",
    category: "cogs",
    description: "Hybrid help system with interactive category select, usage examples, and required permissions.",
    content: `# Full implementation with HELP_CATEGORIES, HelpSelect, and dynamic prefix display.`
  },
  {
    path: "requirements.txt",
    category: "scripts",
    description: "Python package dependencies (discord.py, aiosqlite, python-dotenv).",
    content: `discord.py>=2.3.2
aiosqlite>=0.19.0
python-dotenv>=1.0.0
aiohttp>=3.9.0
typing-extensions>=4.8.0`
  },
  {
    path: "start.sh",
    category: "scripts",
    description: "One-line production launch script with auto-dependency installer and environment check.",
    content: `#!/usr/bin/env bash
set -e
echo "🌌 Initializing Cosmic ki baddie..."
cd "$(dirname "$0")"
mkdir -p data
python3 -m pip install -q -r requirements.txt || true
exec python3 main.py`
  },
  {
    path: ".env.example",
    category: "config",
    description: "Environment configuration template for tokens and server settings.",
    content: `DISCORD_TOKEN="YOUR_BOT_TOKEN_HERE"
DEFAULT_PREFIX="!"
MAIN_SERVER_NAME="Side Quest Studio"
DATABASE_PATH="data/cosmic_bot.db"
DEFAULT_ANTINUKE_THRESHOLD=3
ANTINUKE_TIME_WINDOW=60`
  },
  {
    path: "README.md",
    category: "docs",
    description: "Full production documentation, Developer Portal intents guide, and 24/7 VPS hosting steps.",
    content: `# Cosmic ki baddie - Production Discord Bot for Side Quest Studio`
  }
];
