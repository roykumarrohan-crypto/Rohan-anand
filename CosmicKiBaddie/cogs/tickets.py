"""
Cosmic ki baddie - Ticket System Cog
Production support ticket system with persistent buttons, transcripts, claiming, and private channels.
"""

import discord
from discord.ext import commands
from discord import app_commands
import io
import time
from typing import Optional
from config import COLOR_COSMIC_PURPLE, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, EMOJI_TICKET, EMOJI_CHECK, EMOJI_CROSS
from database import db_manager

class TicketCreationModal(discord.ui.Modal, title="Open a Support Ticket"):
    subject = discord.ui.TextInput(
        label="Ticket Subject / Issue",
        placeholder="Brief description of what you need help with...",
        min_length=3,
        max_length=100
    )
    details = discord.ui.TextInput(
        label="Detailed Explanation",
        style=discord.TextStyle.paragraph,
        placeholder="Provide all relevant details so our Side Quest team can assist you...",
        min_length=10,
        max_length=1000
    )

    def __init__(self, category_name: str):
        super().__init__()
        self.category_name = category_name

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        # Check maximum open tickets per user (limit = 2)
        open_tickets = await db_manager.get_user_open_tickets(guild.id, user.id)
        if len(open_tickets) >= 2:
            return await interaction.response.send_message(
                f"{EMOJI_CROSS} You already have **{len(open_tickets)}** open ticket(s). Please close your active ticket before opening a new one.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        cfg = await db_manager.get_guild_config(guild.id)
        category_id = cfg.get("ticket_category_id")
        category = guild.get_channel(category_id) if category_id else None

        # Build permission overwrites for the private ticket channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_messages=True)
        }

        # Add support role if configured
        support_role_id = cfg.get("ticket_support_role_id")
        if support_role_id:
            support_role = guild.get_role(support_role_id)
            if support_role:
                overwrites[support_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        channel_name = f"ticket-{user.name[:10]}-{int(time.time()) % 10000}"
        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Support Ticket for {user} | Subject: {self.subject.value}"
        )

        ticket_id = await db_manager.create_ticket(guild.id, channel.id, user.id, str(user), self.category_name)

        welcome_embed = discord.Embed(
            title=f"🎫 Support Ticket #{ticket_id}",
            description=f"Welcome {user.mention}! Our Side Quest Studio support staff has been notified.\n\n"
                        f"**Category:** {self.category_name}\n"
                        f"**Subject:** {self.subject.value}\n"
                        f"**Details:**\n> {self.details.value}\n\n"
                        "Please use the controls below to manage this ticket.",
            color=COLOR_COSMIC_PURPLE,
            timestamp=discord.utils.utcnow()
        )
        welcome_embed.set_footer(text="Cosmic ki baddie • Ticket Manager", icon_url=guild.me.display_avatar.url)

        view = TicketControlView()
        ticket_msg = await channel.send(content=f"{user.mention} | <@&{support_role_id}>" if support_role_id else user.mention, embed=welcome_embed, view=view)
        await ticket_msg.pin()

        await interaction.followup.send(f"{EMOJI_CHECK} Your ticket has been created: {channel.mention}", ephemeral=True)

        # Log to ticket logs channel
        log_channel_id = cfg.get("ticket_log_channel_id")
        if log_channel_id:
            log_ch = guild.get_channel(log_channel_id)
            if log_ch:
                log_embed = discord.Embed(
                    title="🎫 Ticket Created",
                    description=f"**Ticket:** {channel.mention} (`#{ticket_id}`)\n**User:** {user.mention} (`{user.id}`)\n**Subject:** {self.subject.value}",
                    color=COLOR_SUCCESS
                )
                await log_ch.send(embed=log_embed)


class TicketLauncherView(discord.ui.View):
    """Persistent view for the server ticket creation panel."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Support Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="cosmic_ticket_open_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketCreationModal(category_name="General Support"))

    @discord.ui.button(label="Report Player / Issue", style=discord.ButtonStyle.danger, emoji="🚨", custom_id="cosmic_ticket_report_btn")
    async def open_report(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketCreationModal(category_name="Player Report"))


class TicketControlView(discord.ui.View):
    """Controls inside an active ticket channel."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.success, emoji="🙋‍♂️", custom_id="cosmic_ticket_claim_btn")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket = await db_manager.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            return await interaction.response.send_message(f"{EMOJI_CROSS} This is not an active ticket channel.", ephemeral=True)

        if ticket.get("claimer_id"):
            return await interaction.response.send_message(f"{EMOJI_CROSS} This ticket has already been claimed by <@{ticket['claimer_id']}>.", ephemeral=True)

        await db_manager.claim_ticket(interaction.channel.id, interaction.user.id, str(interaction.user))
        button.disabled = True
        button.label = f"Claimed by {interaction.user.name}"
        await interaction.response.edit_message(view=self)

        embed = discord.Embed(
            description=f"🙋‍♂️ **{interaction.user.mention}** has claimed this ticket and will be handling your request.",
            color=COLOR_SUCCESS
        )
        await interaction.channel.send(embed=embed)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.secondary, emoji="🔒", custom_id="cosmic_ticket_close_btn")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket = await db_manager.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            return await interaction.response.send_message(f"{EMOJI_CROSS} Not an active ticket.", ephemeral=True)

        # Confirm close
        confirm_view = TicketCloseConfirmView(interaction.user)
        await interaction.response.send_message("Are you sure you want to close this ticket and generate the transcript?", view=confirm_view)


class TicketCloseConfirmView(discord.ui.View):
    def __init__(self, requester: discord.Member):
        super().__init__(timeout=30)
        self.requester = requester

    @discord.ui.button(label="Confirm Close", style=discord.ButtonStyle.danger, emoji="🔒")
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        guild = interaction.guild

        await interaction.response.send_message("Generating transcript and locking ticket...", ephemeral=False)

        # Generate transcript from message history
        messages = []
        async for msg in channel.history(limit=500, oldest_first=True):
            ts = msg.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            messages.append(f"[{ts}] {msg.author} ({msg.author.id}): {msg.content}")

        transcript_str = "\n".join(messages)
        await db_manager.close_ticket(channel.id, transcript_text=transcript_str)

        # Lock channel permissions
        for target, overwrite in channel.overwrites.items():
            if isinstance(target, discord.Member) and target != guild.me:
                overwrite.send_messages = False
                await channel.set_permissions(target, overwrite=overwrite)

        file = discord.File(io.BytesIO(transcript_str.encode("utf-8")), filename=f"transcript-{channel.name}.txt")

        # Send transcript to channel
        embed = discord.Embed(
            title="🔒 Ticket Closed",
            description=f"Closed by {interaction.user.mention}. Use `/ticket reopen` to restore or wait for deletion.",
            color=COLOR_WARNING
        )
        await channel.send(embed=embed, file=file)

        # Log transcript to ticket log channel
        cfg = await db_manager.get_guild_config(guild.id)
        log_id = cfg.get("ticket_log_channel_id")
        if log_id:
            log_ch = guild.get_channel(log_id)
            if log_ch:
                file_copy = discord.File(io.BytesIO(transcript_str.encode("utf-8")), filename=f"transcript-{channel.name}.txt")
                log_embed = discord.Embed(
                    title="🔒 Ticket Closed & Archived",
                    description=f"**Ticket:** `#{channel.name}`\n**Closed by:** {interaction.user.mention}",
                    color=COLOR_WARNING
                )
                await log_ch.send(embed=log_embed, file=file_copy)


class Tickets(commands.Cog, name="Tickets"):
    """Support ticket system for Side Quest Studio."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ticket_group = app_commands.Group(name="ticket", description="Manage the support ticket system")

    @ticket_group.command(name="setup", description="Configure ticket categories and support roles")
    @app_commands.describe(
        category="Category channel to create tickets under",
        support_role="Role that has access to tickets",
        log_channel="Channel where ticket transcripts and events are logged"
    )
    @commands.has_permissions(administrator=True)
    async def ticket_setup(
        self,
        interaction: discord.Interaction,
        category: Optional[discord.CategoryChannel] = None,
        support_role: Optional[discord.Role] = None,
        log_channel: Optional[discord.TextChannel] = None
    ):
        updates = {}
        if category:
            updates["ticket_category_id"] = category.id
        if support_role:
            updates["ticket_support_role_id"] = support_role.id
        if log_channel:
            updates["ticket_log_channel_id"] = log_channel.id

        await db_manager.update_guild_config(interaction.guild_id, **updates)

        embed = discord.Embed(
            title=f"{EMOJI_CHECK} Ticket System Configured",
            description="Ticket configuration successfully updated for Side Quest Studio.",
            color=COLOR_SUCCESS
        )
        if category:
            embed.add_field(name="Category", value=category.name, inline=True)
        if support_role:
            embed.add_field(name="Support Role", value=support_role.mention, inline=True)
        if log_channel:
            embed.add_field(name="Log Channel", value=log_channel.mention, inline=True)

        await interaction.response.send_message(embed=embed)

    @ticket_group.command(name="panel", description="Send the interactive ticket creation panel to a channel")
    @app_commands.describe(channel="Channel to deploy the panel in")
    @commands.has_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        target_channel = channel or interaction.channel
        embed = discord.Embed(
            title="🌌 Side Quest Studio • Support Hub",
            description="Need assistance with server perks, questions, or reporting a rule violation?\n\n"
                        "Click the button below to start a private ticket with our staff team.",
            color=COLOR_COSMIC_PURPLE
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.add_field(name="📜 Guidelines", value="• Be respectful and patient.\n• State your issue clearly with screenshots if applicable.\n• Do not spam multiple tickets.", inline=False)
        embed.set_footer(text="Cosmic ki baddie • Support System", icon_url=self.bot.user.display_avatar.url)

        view = TicketLauncherView()
        await target_channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"{EMOJI_CHECK} Ticket panel deployed in {target_channel.mention}!", ephemeral=True)

    @ticket_group.command(name="add", description="Add a user to the current ticket")
    @app_commands.describe(user="User to add")
    @commands.has_permissions(manage_channels=True)
    async def ticket_add(self, interaction: discord.Interaction, user: discord.Member):
        ticket = await db_manager.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            return await interaction.response.send_message(f"{EMOJI_CROSS} This command can only be used inside a ticket channel.", ephemeral=True)

        await interaction.channel.set_permissions(user, view_channel=True, send_messages=True, read_message_history=True)
        await interaction.response.send_message(f"{EMOJI_CHECK} Added {user.mention} to this ticket.")

    @ticket_group.command(name="remove", description="Remove a user from the current ticket")
    @app_commands.describe(user="User to remove")
    @commands.has_permissions(manage_channels=True)
    async def ticket_remove(self, interaction: discord.Interaction, user: discord.Member):
        ticket = await db_manager.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            return await interaction.response.send_message(f"{EMOJI_CROSS} This command can only be used inside a ticket channel.", ephemeral=True)

        if user.id == ticket["creator_id"]:
            return await interaction.response.send_message(f"{EMOJI_CROSS} You cannot remove the ticket creator from their own ticket.", ephemeral=True)

        await interaction.channel.set_permissions(user, overwrite=None)
        await interaction.response.send_message(f"{EMOJI_CHECK} Removed {user.mention} from this ticket.")

    @ticket_group.command(name="claim", description="Claim the current ticket")
    @commands.has_permissions(manage_channels=True)
    async def ticket_claim(self, interaction: discord.Interaction):
        ticket = await db_manager.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            return await interaction.response.send_message(f"{EMOJI_CROSS} Not a ticket channel.", ephemeral=True)

        await db_manager.claim_ticket(interaction.channel.id, interaction.user.id, str(interaction.user))
        await interaction.response.send_message(f"🙋‍♂️ {interaction.user.mention} has claimed this ticket!")

    @ticket_group.command(name="close", description="Close the current ticket")
    async def ticket_close(self, interaction: discord.Interaction):
        ticket = await db_manager.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            return await interaction.response.send_message(f"{EMOJI_CROSS} This command can only be used inside a ticket channel.", ephemeral=True)

        view = TicketCloseConfirmView(interaction.user)
        await interaction.response.send_message("Are you sure you want to close this ticket?", view=view)

    @ticket_group.command(name="reopen", description="Reopen a closed ticket")
    @commands.has_permissions(manage_channels=True)
    async def ticket_reopen(self, interaction: discord.Interaction):
        ticket = await db_manager.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            return await interaction.response.send_message(f"{EMOJI_CROSS} Not a ticket channel.", ephemeral=True)

        await db_manager.reopen_ticket(interaction.channel.id)
        creator = interaction.guild.get_member(ticket["creator_id"])
        if creator:
            await interaction.channel.set_permissions(creator, view_channel=True, send_messages=True)

        await interaction.response.send_message(f"{EMOJI_CHECK} Ticket reopened by {interaction.user.mention}.")

    @ticket_group.command(name="transcript", description="Download the current ticket transcript")
    async def ticket_transcript(self, interaction: discord.Interaction):
        ticket = await db_manager.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            return await interaction.response.send_message(f"{EMOJI_CROSS} Not a ticket channel.", ephemeral=True)

        await interaction.response.defer()
        messages = []
        async for msg in interaction.channel.history(limit=500, oldest_first=True):
            ts = msg.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            messages.append(f"[{ts}] {msg.author} ({msg.author.id}): {msg.content}")

        text = "\n".join(messages)
        file = discord.File(io.BytesIO(text.encode("utf-8")), filename=f"transcript-{interaction.channel.name}.txt")
        await interaction.followup.send("Here is the generated transcript:", file=file)

    @ticket_group.command(name="settings", description="View ticket system settings")
    @commands.has_permissions(manage_channels=True)
    async def ticket_settings(self, interaction: discord.Interaction):
        cfg = await db_manager.get_guild_config(interaction.guild_id)
        cat = interaction.guild.get_channel(cfg.get("ticket_category_id")) if cfg.get("ticket_category_id") else None
        role = interaction.guild.get_role(cfg.get("ticket_support_role_id")) if cfg.get("ticket_support_role_id") else None
        log_ch = interaction.guild.get_channel(cfg.get("ticket_log_channel_id")) if cfg.get("ticket_log_channel_id") else None

        embed = discord.Embed(
            title="🎫 Ticket System Configuration",
            color=COLOR_COSMIC_PURPLE,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Category", value=cat.name if cat else "*Not Set*", inline=True)
        embed.add_field(name="Support Role", value=role.mention if role else "*Not Set*", inline=True)
        embed.add_field(name="Log Channel", value=log_ch.mention if log_ch else "*Not Set*", inline=True)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    cog = Tickets(bot)
    await bot.add_cog(cog)
    # Register persistent views so buttons work after restart
    bot.add_view(TicketLauncherView())
    bot.add_view(TicketControlView())
