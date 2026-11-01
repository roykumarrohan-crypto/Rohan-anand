"""
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
        # Request all privileged intents for audit logging, member onboarding, and activity
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
        # Unpack wrapped errors
        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        if isinstance(error, commands.CommandNotFound):
            return  # Silently ignore unregistered prefix commands

        elif isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed = discord.Embed(
                title=f"{EMOJI_CROSS} Missing Permissions",
                description=f"You need the following Discord permission(s) to use this command:\n`{perms}`",
                color=COLOR_DANGER
            )
            return await ctx.send(embed=embed, ephemeral=True)

        elif isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed = discord.Embed(
                title=f"{EMOJI_CROSS} Bot Lacks Permissions",
                description=f"I require the following permission(s) on this server:\n`{perms}`",
                color=COLOR_DANGER
            )
            return await ctx.send(embed=embed, ephemeral=True)

        elif isinstance(error, commands.BadArgument):
            return await ctx.send(f"{EMOJI_CROSS} Invalid argument provided: {error}", ephemeral=True)

        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"{EMOJI_CROSS} Missing required argument: `{error.param.name}`. Run `/help` for usage.", ephemeral=True)

        logger.error(f"Unhandled command error in {ctx.command}: {error}", exc_info=True)


def main():
    if not DISCORD_TOKEN or DISCORD_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("""
[!] WARNING: DISCORD_TOKEN is missing or still set to default placeholder.
Please set your DISCORD_TOKEN in .env or the environment before launching the bot:
    export DISCORD_TOKEN="your-bot-token"
    python3 main.py
        """)
        # We exit gracefully with informative message
        sys.exit(1)

    bot = CosmicBot()
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
