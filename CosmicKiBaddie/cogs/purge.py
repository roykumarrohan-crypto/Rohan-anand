"""
Cosmic ki baddie - Purge System Cog
Advanced message cleaning with filters (user, text, links, bots, attachments) and safety checks.
"""

import discord
from discord.ext import commands
from discord import app_commands
import re
import datetime
from typing import Optional
from config import COLOR_SUCCESS, COLOR_WARNING, EMOJI_CHECK, EMOJI_CROSS

URL_REGEX = re.compile(r'https?://[^\s]+')

class Purge(commands.Cog, name="Purge"):
    """Advanced message-clearing system with granular filters and summaries."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="purge", description="Purge messages with granular filters")
    @app_commands.describe(
        amount="Number of messages to check/delete (1-100)",
        user="Only delete messages from this user",
        contains="Only delete messages containing this phrase",
        links_only="Only delete messages containing URLs",
        bots_only="Only delete messages sent by bots",
        has_attachment="Only delete messages with file attachments"
    )
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    async def purge(
        self,
        ctx: commands.Context,
        amount: int = 10,
        user: Optional[discord.Member] = None,
        contains: Optional[str] = None,
        links_only: bool = False,
        bots_only: bool = False,
        has_attachment: bool = False
    ):
        if amount < 1 or amount > 100:
            return await ctx.send(f"{EMOJI_CROSS} Please specify an amount between 1 and 100.", ephemeral=True)

        # Defer so we have enough time to inspect and purge
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)

        fourteen_days_ago = discord.utils.utcnow() - datetime.timedelta(days=14)

        def check(m: discord.Message) -> bool:
            # Skip the command message itself if prefix command
            if ctx.message and m.id == ctx.message.id:
                return False
            if user and m.author.id != user.id:
                return False
            if contains and contains.lower() not in m.content.lower():
                return False
            if links_only and not URL_REGEX.search(m.content):
                return False
            if bots_only and not m.author.bot:
                return False
            if has_attachment and len(m.attachments) == 0:
                return False
            return True

        try:
            # We fetch up to amount messages matching the check
            deleted = await ctx.channel.purge(limit=amount, check=check, after=fourteen_days_ago)
            count = len(deleted)

            # Build summary
            filters = []
            if user:
                filters.append(f"User: {user.mention}")
            if contains:
                filters.append(f'Contains: "{contains}"')
            if links_only:
                filters.append("Links Only")
            if bots_only:
                filters.append("Bots Only")
            if has_attachment:
                filters.append("Has Attachments")

            filter_str = ", ".join(filters) if filters else "None (all matching)"

            embed = discord.Embed(
                title=f"{EMOJI_CHECK} Purge Completed",
                description=f"Successfully deleted **{count}** message(s) from {ctx.channel.mention}.",
                color=COLOR_SUCCESS,
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Filters Applied", value=filter_str, inline=False)
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

            if ctx.interaction:
                await ctx.interaction.followup.send(embed=embed, ephemeral=True)
            else:
                msg = await ctx.send(embed=embed)
                # auto delete confirmation after 5 seconds to keep chat clean
                await msg.delete(delay=5.0)

        except discord.Forbidden:
            await ctx.send(f"{EMOJI_CROSS} I lack permissions to delete messages in this channel.", ephemeral=True)
        except Exception as e:
            await ctx.send(f"{EMOJI_CROSS} An error occurred while purging: {e}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Purge(bot))
