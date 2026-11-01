"""
Cosmic ki baddie - Configuration Module
Tailored for Side Quest Studio
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Bot Identity
BOT_NAME = "Cosmic ki baddie"
SERVER_NAME = os.getenv("MAIN_SERVER_NAME", "Side Quest Studio")
BOT_VERSION = "2.4.0-Production"
BOT_AUTHOR = "Cosmic Engineering"

# Discord Credentials & Settings
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
DEFAULT_PREFIX = os.getenv("DEFAULT_PREFIX", "!")
DATABASE_PATH = str(BASE_DIR / os.getenv("DATABASE_PATH", "data/cosmic_bot.db"))
DEV_GUILD_ID = int(os.getenv("DEV_GUILD_ID")) if os.getenv("DEV_GUILD_ID") else None

# Aesthetic Theme Colors (Discord Hex Int)
COLOR_COSMIC_PURPLE = 0x8A2BE2   # BlueViolet / Cosmic Signature
COLOR_STELLAR_CYAN = 0x00E5FF    # Glowing Cyan / Info
COLOR_SUCCESS = 0x00FF88         # Emerald Neon / Success
COLOR_WARNING = 0xFFB300         # Amber / Warning
COLOR_DANGER = 0xFF3366          # Crimson / Danger & Anti-Nuke
COLOR_SIDE_QUEST = 0x7289DA      # Side Quest Blurple
COLOR_DARK = 0x1E1F29            # Slate Dark / Embed Base

# Standard Bot Emojis
EMOJI_SPARKLE = "✨"
EMOJI_SHIELD = "🛡️"
EMOJI_TICKET = "🎫"
EMOJI_SWORD = "⚔️"
EMOJI_QUEST = "🗺️"
EMOJI_STAR = "⭐"
EMOJI_WARN = "⚠️"
EMOJI_CHECK = "✅"
EMOJI_CROSS = "❌"
EMOJI_LOADING = "⏳"
EMOJI_GIFT = "🎉"
EMOJI_POLL = "📊"
EMOJI_LOCK = "🔒"

# Anti-Nuke Defaults
ANTINUKE_DEFAULT_THRESHOLD = int(os.getenv("DEFAULT_ANTINUKE_THRESHOLD", "3"))
ANTINUKE_DEFAULT_WINDOW = int(os.getenv("ANTINUKE_TIME_WINDOW", "60"))

# Ticket Defaults
DEFAULT_TICKET_CATEGORY_NAME = "Cosmic Tickets"
DEFAULT_TICKET_ROLE_NAME = "Support Team"

# Cog Extensions to Load
INITIAL_COGS = [
    "cogs.moderation",
    "cogs.purge",
    "cogs.automation",
    "cogs.tickets",
    "cogs.logging",
    "cogs.roles",
    "cogs.permissions",
    "cogs.security",
    "cogs.giveaways",
    "cogs.events",
    "cogs.polls",
    "cogs.autoresponder",
    "cogs.welcome",
    "cogs.embeds",
    "cogs.setup_wizard",
    "cogs.dashboard",
    "cogs.help",
]
