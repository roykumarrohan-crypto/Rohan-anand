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

@commands.hybrid_command(name="purge", aliases=["clean", "delete"], help="Channel ke messages delete karna")
    @bot_permission("purge")
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, amount: int = 10):
        if amount < 1:
            return await ctx.send("❌ Amount kam se kam 1 hona chahiye.")
        if amount > 100:
            amount = 100

        await ctx.defer(ephemeral=True)
        deleted = await ctx.channel.purge(limit=amount + (1 if not ctx.interaction else 0))
        count = max(0, len(deleted) - (0 if ctx.interaction else 1))
        msg = f"🧹 **{count} messages** delete kar diye gaye hain."
        if ctx.interaction:
            await ctx.send(msg, ephemeral=True)
        else:
            await ctx.send(msg, delete_after=5)
            
        except discord.Forbidden:
            await ctx.send(f"{EMOJI_CROSS} I lack permissions to delete messages in this channel.", ephemeral=True)
        except Exception as e:
            await ctx.send(f"{EMOJI_CROSS} An error occurred while purging: {e}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Purge(bot))
