"""
Cosmic ki baddie - Giveaway System Cog
Persistent giveaways with interactive button entries, automated drawing loops, and rerolls.
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import time
import json
import re
from typing import Optional, List
from config import COLOR_COSMIC_PURPLE, COLOR_SUCCESS, COLOR_WARNING, EMOJI_GIFT, EMOJI_CHECK, EMOJI_CROSS
from database import db_manager

def parse_duration(duration_str: str) -> Optional[int]:
    """Parse time string like 10m, 2h, 1d into total seconds."""
    match = re.match(r"^(\d+)([smhd])$", duration_str.lower().strip())
    if not match:
        return None
    val, unit = int(match.group(1)), match.group(2)
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return val * multipliers[unit]


class GiveawayButton(discord.ui.Button):
    def __init__(self, giveaway_id: int):
        super().__init__(
            label="Enter Giveaway 🎉",
            style=discord.ButtonStyle.primary,
            custom_id=f"cosmic_giveaway_btn_{giveaway_id}"
        )
        self.giveaway_id = giveaway_id

    async def callback(self, interaction: discord.Interaction):
        success = await db_manager.enter_giveaway(self.giveaway_id, interaction.user.id)
        if success:
            entries = await db_manager.get_giveaway_entries(self.giveaway_id)
            await interaction.response.send_message(f"🎉 You have entered the giveaway! Total entries: **{len(entries)}**", ephemeral=True)
        else:
            await interaction.response.send_message("You are already entered in this giveaway!", ephemeral=True)


class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id: int):
        super().__init__(timeout=None)
        self.add_item(GiveawayButton(giveaway_id))


class Giveaways(commands.Cog, name="Giveaways"):
    """Server giveaways with persistent timer loop, interactive entry buttons, and winner picking."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    @tasks.loop(seconds=15.0)
    async def check_giveaways(self):
        """Periodic background task that resolves ended giveaways."""
        now = time.time()
        import aiosqlite
        try:
            async with aiosqlite.connect(db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("SELECT * FROM giveaways WHERE ended = 0 AND end_time <= ?", (now,))
                ended_giveaways = [dict(r) for r in await cursor.fetchall()]

            for g in ended_giveaways:
                await self.resolve_giveaway(g)
        except Exception:
            pass

    async def resolve_giveaway(self, giveaway_data: dict):
        g_id = giveaway_data["id"]
        channel = self.bot.get_channel(giveaway_data["channel_id"])
        entries = await db_manager.get_giveaway_entries(g_id)
        winners_count = giveaway_data["winners_count"]
        prize = giveaway_data["prize"]

        winners = []
        if entries:
            chosen_ids = random.sample(entries, k=min(winners_count, len(entries)))
            winners = chosen_ids

        await db_manager.end_giveaway(g_id, winners)

        if channel:
            if winners:
                mentions = ", ".join([f"<@{uid}>" for uid in winners])
                embed = discord.Embed(
                    title=f"🎉 GIVEAWAY ENDED: {prize} 🎉",
                    description=f"**Winner(s):** {mentions}\n**Hosted by:** <@{giveaway_data['host_id']}>\n**Total Entries:** {len(entries)}",
                    color=COLOR_SUCCESS
                )
                await channel.send(content=f"Congratulations {mentions}!", embed=embed)
            else:
                embed = discord.Embed(
                    title=f"🎉 GIVEAWAY ENDED: {prize} 🎉",
                    description=f"Unfortunately, no one entered the giveaway for **{prize}**.\n**Hosted by:** <@{giveaway_data['host_id']}>",
                    color=COLOR_WARNING
                )
                await channel.send(embed=embed)

    giveaway_group = app_commands.Group(name="giveaway", description="Server giveaway commands")

    @giveaway_group.command(name="start", description="Start a new giveaway")
    @app_commands.describe(
        prize="Item or perk to giveaway",
        duration="Duration format: 10m, 2h, 1d",
        winners="Number of winners (default 1)",
        channel="Channel to host the giveaway in (default current)"
    )
    @commands.has_permissions(manage_guild=True)
    async def giveaway_start(
        self,
        interaction: discord.Interaction,
        prize: str,
        duration: str,
        winners: int = 1,
        channel: Optional[discord.TextChannel] = None
    ):
        target_ch = channel or interaction.channel
        sec = parse_duration(duration)
        if not sec or sec < 10 or sec > 2592000:
            return await interaction.response.send_message(f"{EMOJI_CROSS} Invalid duration. Examples: `30m`, `2h`, `7d`.", ephemeral=True)

        if winners < 1 or winners > 20:
            return await interaction.response.send_message(f"{EMOJI_CROSS} Winners count must be between 1 and 20.", ephemeral=True)

        end_ts = time.time() + sec

        embed = discord.Embed(
            title=f"🎉 GIVEAWAY: {prize}",
            description=f"Click the button below to participate!\n\n"
                        f"**Winners:** {winners}\n"
                        f"**Hosted by:** {interaction.user.mention}\n"
                        f"**Ends:** <t:{int(end_ts)}:R> (<t:{int(end_ts)}:F>)",
            color=COLOR_COSMIC_PURPLE
        )
        embed.set_footer(text="Side Quest Studio • Cosmic Giveaways")

        # Send initial placeholder message
        msg = await target_ch.send(embed=embed)
        g_id = await db_manager.create_giveaway(
            guild_id=interaction.guild_id,
            channel_id=target_ch.id,
            message_id=msg.id,
            prize=prize,
            winners_count=winners,
            end_time=end_ts,
            host_id=interaction.user.id
        )

        view = GiveawayView(g_id)
        await msg.edit(view=view)
        await interaction.response.send_message(f"{EMOJI_CHECK} Giveaway started in {target_ch.mention}!", ephemeral=True)

    @giveaway_group.command(name="reroll", description="Reroll winners for an existing giveaway")
    @app_commands.describe(giveaway_id="ID of the giveaway to reroll")
    @commands.has_permissions(manage_guild=True)
    async def giveaway_reroll(self, interaction: discord.Interaction, giveaway_id: int):
        entries = await db_manager.get_giveaway_entries(giveaway_id)
        if not entries:
            return await interaction.response.send_message(f"{EMOJI_CROSS} No entries found for giveaway #{giveaway_id}.", ephemeral=True)

        new_winner_id = random.choice(entries)
        embed = discord.Embed(
            title="🎉 Giveaway Rerolled!",
            description=f"The new lucky winner for Giveaway **#{giveaway_id}** is <@{new_winner_id}>! Congratulations!",
            color=COLOR_SUCCESS
        )
        await interaction.response.send_message(content=f"<@{new_winner_id}>", embed=embed)

async def setup(bot: commands.Bot):
    cog = Giveaways(bot)
    await bot.add_cog(cog)
