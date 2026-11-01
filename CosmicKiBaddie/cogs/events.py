"""
Cosmic ki baddie - Events System Cog
Community events management with RSVPs (Going/Interested), persistent state, and reminders.
"""

import discord
from discord.ext import commands
from discord import app_commands
import time
from typing import Optional
from config import COLOR_COSMIC_PURPLE, COLOR_SUCCESS, COLOR_WARNING, EMOJI_QUEST, EMOJI_CHECK, EMOJI_CROSS
from database import db_manager

class EventRsvpButton(discord.ui.Button):
    def __init__(self, event_id: int, status: str, label: str, emoji: str, style: discord.ButtonStyle):
        super().__init__(
            label=label,
            style=style,
            emoji=emoji,
            custom_id=f"cosmic_rsvp_{event_id}_{status}"
        )
        self.event_id = event_id
        self.rsvp_status = status

    async def callback(self, interaction: discord.Interaction):
        await db_manager.rsvp_event(self.event_id, interaction.user.id, self.rsvp_status)
        rsvps = await db_manager.get_event_rsvps(self.event_id)
        going_count = len(rsvps["going"])
        interested_count = len(rsvps["interested"])

        status_text = "Going! 🚀" if self.rsvp_status == "going" else "Interested! ⭐"
        await interaction.response.send_message(
            f"{EMOJI_CHECK} Marked you as **{status_text}** (Total Going: {going_count}, Interested: {interested_count})",
            ephemeral=True
        )


class EventView(discord.ui.View):
    def __init__(self, event_id: int):
        super().__init__(timeout=None)
        self.add_item(EventRsvpButton(event_id, "going", "Going 🚀", "🚀", discord.ButtonStyle.success))
        self.add_item(EventRsvpButton(event_id, "interested", "Interested ⭐", "⭐", discord.ButtonStyle.secondary))


class Events(commands.Cog, name="Events"):
    """Server events management with interactive RSVPs and participant rosters."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    event_group = app_commands.Group(name="event", description="Community event management")

    @event_group.command(name="create", description="Schedule a new server event")
    @app_commands.describe(
        title="Event name / title",
        description="Event description, location, or voice channel",
        in_hours="Hours from now until event starts"
    )
    @commands.has_permissions(manage_events=True)
    async def event_create(self, interaction: discord.Interaction, title: str, description: str, in_hours: float):
        if in_hours <= 0 or in_hours > 720:
            return await interaction.response.send_message(f"{EMOJI_CROSS} Hours must be between 0.1 and 720 (30 days).", ephemeral=True)

        event_ts = time.time() + (in_hours * 3600)

        event_id = await db_manager.create_event(
            guild_id=interaction.guild_id,
            channel_id=interaction.channel.id,
            title=title,
            description=description,
            event_time=event_ts,
            creator_id=interaction.user.id
        )

        embed = discord.Embed(
            title=f"🗺️ Community Event: {title}",
            description=f"{description}\n\n"
                        f"**Event Time:** <t:{int(event_ts)}:F> (<t:{int(event_ts)}:R>)\n"
                        f"**Organized by:** {interaction.user.mention}\n\n"
                        "Click below to RSVP!",
            color=COLOR_COSMIC_PURPLE,
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Event #{event_id} • Side Quest Studio")

        view = EventView(event_id)
        msg = await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"{EMOJI_CHECK} Event **{title}** scheduled successfully!", ephemeral=True)

    @event_group.command(name="list", description="List upcoming server events")
    async def event_list(self, interaction: discord.Interaction):
        import aiosqlite
        now = time.time()
        async with aiosqlite.connect(db_manager.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM events WHERE guild_id = ? AND status = 'active' AND event_time >= ? ORDER BY event_time ASC LIMIT 10",
                                     (interaction.guild_id, now))
            events = [dict(r) for r in await cursor.fetchall()]

        if not events:
            return await interaction.response.send_message("No upcoming events currently scheduled for Side Quest Studio.", ephemeral=True)

        embed = discord.Embed(
            title="🗺️ Upcoming Side Quest Studio Events",
            color=COLOR_COSMIC_PURPLE
        )
        for ev in events:
            rsvps = await db_manager.get_event_rsvps(ev["id"])
            embed.add_field(
                name=f"#{ev['id']} {ev['title']} - <t:{int(ev['event_time'])}:R>",
                value=f"{ev['description'][:100]}\nGoing: **{len(rsvps['going'])}** | Interested: **{len(rsvps['interested'])}**",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
