"""
Cosmic ki baddie - Automation & Activity System Cog
Activity leveling (messages/voice), automated role progression, milestone rewards, and automation rules.
"""

import discord
from discord.ext import commands
from discord import app_commands
import time
from typing import Optional
from config import COLOR_COSMIC_PURPLE, COLOR_SUCCESS, COLOR_STELLAR_CYAN, EMOJI_STAR, EMOJI_CHECK, EMOJI_CROSS
from database import db_manager

class Automation(commands.Cog, name="Automation"):
    """Activity tracking, milestone role leveling, and custom trigger-action automation."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Track message activity and calculate level progression
        count, level, leveled_up = await db_manager.record_activity_message(message.guild.id, message.author.id)

        # Check activity milestone roles
        if leveled_up:
            roles_cfg = await db_manager.get_activity_roles(message.guild.id)
            for r_cfg in roles_cfg:
                if r_cfg["threshold_type"] == "level" and level >= r_cfg["threshold_value"]:
                    role = message.guild.get_role(r_cfg["role_id"])
                    if role and role not in message.author.roles and role < message.guild.me.top_role:
                        try:
                            await message.author.add_roles(role, reason=f"Cosmic Milestone: Reached Level {level}")
                        except Exception:
                            pass

            # Optional level up announcement
            embed = discord.Embed(
                description=f"🎉 **Level Up!** {message.author.mention} reached **Level {level}** in Side Quest Studio! Keep questing! ⭐",
                color=COLOR_SUCCESS
            )
            await message.channel.send(embed=embed, delete_after=10.0)

    # ==========================
    # Activity & Leaderboard Commands
    # ==========================
    @commands.hybrid_command(name="rank", description="Check your current server level, XP, and message count")
    @app_commands.describe(user="Member to inspect")
    async def rank(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        target = user or ctx.author
        import aiosqlite
        async with aiosqlite.connect(db_manager.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM activity_stats WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, target.id))
            row = await cursor.fetchone()

        if not row:
            return await ctx.send(f"{target.display_name} has not gained any activity points yet.", ephemeral=True)

        level = row["level"]
        xp = row["xp"]
        msgs = row["message_count"]
        needed = level * 100

        embed = discord.Embed(
            title=f"⭐ Activity Profile • {target.display_name}",
            color=COLOR_COSMIC_PURPLE,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="XP", value=f"`{xp} / {needed}`", inline=True)
        embed.add_field(name="Messages", value=f"**{msgs}**", inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="leaderboard", description="View Side Quest Studio activity rankings")
    async def leaderboard(self, ctx: commands.Context):
        top_users = await db_manager.get_activity_leaderboard(ctx.guild.id, limit=10)
        if not top_users:
            return await ctx.send("No activity recorded on this server yet.", ephemeral=True)

        embed = discord.Embed(
            title="🏆 Side Quest Studio • Activity Leaderboard",
            color=COLOR_STELLAR_CYAN,
            timestamp=discord.utils.utcnow()
        )
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        lines = []
        for i, u in enumerate(top_users):
            member = ctx.guild.get_member(u["user_id"])
            name = member.display_name if member else f"User {u['user_id']}"
            lines.append(f"{medals[i]} **{name}** — Level `{u['level']}` | `{u['message_count']}` msgs | `{u['xp']}` XP")

        embed.description = "\n".join(lines)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="activityrole", description="Bind an automatic role reward to a level milestone")
    @app_commands.describe(role="Role to award", level="Required level threshold")
    @commands.has_permissions(administrator=True)
    async def activity_role(self, ctx: commands.Context, role: discord.Role, level: int):
        if level < 1:
            return await ctx.send(f"{EMOJI_CROSS} Level must be greater than 0.", ephemeral=True)

        await db_manager.set_activity_role(ctx.guild.id, role.id, "level", level)
        await ctx.send(f"{EMOJI_CHECK} Role {role.mention} will now be automatically awarded at **Level {level}**!")

async def setup(bot: commands.Bot):
    await bot.add_cog(Automation(bot))
