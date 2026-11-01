"""
Cosmic ki baddie - Polling System Cog
Interactive voting system with live percentage bars, single/multi choice, and anonymous polls.
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import time
from typing import Optional, List
from config import COLOR_COSMIC_PURPLE, COLOR_SUCCESS, COLOR_STELLAR_CYAN, EMOJI_POLL, EMOJI_CHECK, EMOJI_CROSS
from database import db_manager

def make_progress_bar(percentage: float, length: int = 10) -> str:
    filled = int(round(length * (percentage / 100.0)))
    empty = length - filled
    return "█" * filled + "░" * empty

class PollVoteButton(discord.ui.Button):
    def __init__(self, poll_id: int, option_idx: int, option_label: str):
        super().__init__(
            label=f"{option_idx+1}. {option_label[:40]}",
            style=discord.ButtonStyle.secondary,
            custom_id=f"cosmic_poll_{poll_id}_{option_idx}"
        )
        self.poll_id = poll_id
        self.option_idx = option_idx

    async def callback(self, interaction: discord.Interaction):
        success = await db_manager.vote_poll(self.poll_id, interaction.user.id, self.option_idx)
        if success:
            await interaction.response.send_message(f"{EMOJI_CHECK} Your vote has been recorded!", ephemeral=True)
        else:
            await interaction.response.send_message("Could not record vote. The poll may be closed or you already selected this option.", ephemeral=True)


class PollView(discord.ui.View):
    def __init__(self, poll_id: int, options: List[str]):
        super().__init__(timeout=None)
        for idx, opt in enumerate(options[:5]):
            self.add_item(PollVoteButton(poll_id, idx, opt))


class Polls(commands.Cog, name="Polls"):
    """Create interactive server polls with live vote tracking."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    poll_group = app_commands.Group(name="poll", description="Server polling commands")

    @poll_group.command(name="create", description="Create a poll with up to 5 options")
    @app_commands.describe(
        question="The question to ask",
        option1="Option 1",
        option2="Option 2",
        option3="Option 3 (optional)",
        option4="Option 4 (optional)",
        option5="Option 5 (optional)",
        multiple_choice="Allow members to vote on more than one option",
        anonymous="Hide user vote history"
    )
    @commands.has_permissions(manage_messages=True)
    async def poll_create(
        self,
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: Optional[str] = None,
        option4: Optional[str] = None,
        option5: Optional[str] = None,
        multiple_choice: bool = False,
        anonymous: bool = False
    ):
        raw_options = [option1, option2, option3, option4, option5]
        options = [o for o in raw_options if o is not None and o.strip() != ""]

        if len(options) < 2:
            return await interaction.response.send_message(f"{EMOJI_CROSS} You must provide at least 2 options.", ephemeral=True)

        embed = discord.Embed(
            title=f"📊 Community Poll: {question}",
            description="Cast your vote by clicking the buttons below!\n\n" +
                        "\n".join([f"**{i+1}.** {opt}" for i, opt in enumerate(options)]),
            color=COLOR_COSMIC_PURPLE,
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Created by {interaction.user.name} • {'Multiple Choice' if multiple_choice else 'Single Choice'}")

        msg = await interaction.channel.send(embed=embed)
        poll_id = await db_manager.create_poll(
            guild_id=interaction.guild_id,
            channel_id=interaction.channel.id,
            message_id=msg.id,
            question=question,
            options=options,
            multiple_choice=multiple_choice,
            anonymous=anonymous,
            end_time=time.time() + 86400 * 7
        )

        view = PollView(poll_id, options)
        await msg.edit(view=view)
        await interaction.response.send_message(f"{EMOJI_CHECK} Poll published!", ephemeral=True)

    @poll_group.command(name="results", description="Display current tally for a poll")
    @app_commands.describe(poll_id="Poll ID")
    async def poll_results(self, interaction: discord.Interaction, poll_id: int):
        import aiosqlite
        async with aiosqlite.connect(db_manager.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM polls WHERE id = ?", (poll_id,))
            poll = await cursor.fetchone()

        if not poll:
            return await interaction.response.send_message(f"{EMOJI_CROSS} Poll not found.", ephemeral=True)

        options = json.loads(poll["options_json"])
        results = await db_manager.get_poll_results(poll_id)
        total_votes = sum(results.values())

        embed = discord.Embed(
            title=f"📊 Results: {poll['question']}",
            description=f"Total Votes: **{total_votes}**",
            color=COLOR_STELLAR_CYAN
        )
        for idx, opt in enumerate(options):
            votes = results.get(idx, 0)
            pct = (votes / total_votes * 100) if total_votes > 0 else 0
            bar = make_progress_bar(pct, length=12)
            embed.add_field(
                name=f"{idx+1}. {opt} ({votes} votes • {pct:.1f}%)",
                value=f"`{bar}`",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Polls(bot))
