"""
Cosmic ki baddie - Server Logging Cog
Comprehensive audit logging: messages, members, roles, channels, voice, and administrative events.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from config import COLOR_DANGER, COLOR_SUCCESS, COLOR_WARNING, COLOR_COSMIC_PURPLE, COLOR_STELLAR_CYAN, EMOJI_CHECK
from database import db_manager

class Logging(commands.Cog, name="Logging"):
    """Tracks server events and logs formatted embeds to configured audit channels."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_log_channel(self, guild: discord.Guild, log_type: str = "general") -> Optional[discord.TextChannel]:
        cfg = await db_manager.get_guild_config(guild.id)
        if log_type == "mod":
            ch_id = cfg.get("mod_log_channel_id")
        elif log_type == "ticket":
            ch_id = cfg.get("ticket_log_channel_id")
        else:
            ch_id = cfg.get("general_log_channel_id") or cfg.get("mod_log_channel_id")

        if ch_id:
            ch = guild.get_channel(ch_id)
            if ch and isinstance(ch, discord.TextChannel):
                return ch
        return None

    # ==========================
    # Message Events
    # ==========================
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        log_ch = await self.get_log_channel(message.guild, "general")
        if not log_ch or log_ch.id == message.channel.id:
            return

        embed = discord.Embed(
            title="🗑️ Message Deleted",
            description=f"**Author:** {message.author.mention} (`{message.author.id}`)\n"
                        f"**Channel:** {message.channel.mention}\n\n"
                        f"**Content:**\n{message.content or '*[No text/Embed/Attachment]*'}",
            color=COLOR_DANGER,
            timestamp=discord.utils.utcnow()
        )
        if message.attachments:
            embed.add_field(name="Attachments", value="\n".join([a.url for a in message.attachments]))
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
        await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not before.guild or before.author.bot or before.content == after.content:
            return
        log_ch = await self.get_log_channel(before.guild, "general")
        if not log_ch or log_ch.id == before.channel.id:
            return

        embed = discord.Embed(
            title="✏️ Message Edited",
            description=f"**Author:** {before.author.mention} (`{before.author.id}`)\n"
                        f"**Channel:** {before.channel.mention}\n"
                        f"[Jump to Message]({after.jump_url})",
            color=COLOR_WARNING,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Before", value=before.content[:1024] or "*[Empty]*", inline=False)
        embed.add_field(name="After", value=after.content[:1024] or "*[Empty]*", inline=False)
        embed.set_author(name=str(before.author), icon_url=before.author.display_avatar.url)
        await log_ch.send(embed=embed)

    # ==========================
    # Member Events
    # ==========================
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        log_ch = await self.get_log_channel(member.guild, "general")
        if not log_ch:
            return

        embed = discord.Embed(
            title="📥 Member Joined",
            description=f"{member.mention} (`{member.id}`)\n"
                        f"**Account Created:** <t:{int(member.created_at.timestamp())}:R>\n"
                        f"**Total Members:** {member.guild.member_count}",
            color=COLOR_SUCCESS,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        log_ch = await self.get_log_channel(member.guild, "general")
        if not log_ch:
            return

        embed = discord.Embed(
            title="📤 Member Left",
            description=f"{member.mention} (`{member.id}`)\n"
                        f"**Roles:** {', '.join([r.mention for r in member.roles[1:]]) or 'None'}\n"
                        f"**Total Members:** {member.guild.member_count}",
            color=COLOR_DANGER,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        log_ch = await self.get_log_channel(before.guild, "general")
        if not log_ch:
            return

        # Nickname change
        if before.nick != after.nick:
            embed = discord.Embed(
                title="🏷️ Nickname Changed",
                description=f"**Member:** {after.mention} (`{after.id}`)\n"
                            f"**Before:** `{before.nick or before.name}`\n"
                            f"**After:** `{after.nick or after.name}`",
                color=COLOR_STELLAR_CYAN,
                timestamp=discord.utils.utcnow()
            )
            embed.set_author(name=str(after), icon_url=after.display_avatar.url)
            await log_ch.send(embed=embed)

        # Role updates
        if before.roles != after.roles:
            added = [r for r in after.roles if r not in before.roles]
            removed = [r for r in before.roles if r not in after.roles]

            if added or removed:
                embed = discord.Embed(
                    title="🎭 Member Roles Updated",
                    description=f"**Member:** {after.mention} (`{after.id}`)",
                    color=COLOR_COSMIC_PURPLE,
                    timestamp=discord.utils.utcnow()
                )
                if added:
                    embed.add_field(name="Roles Added", value=" ".join([r.mention for r in added]))
                if removed:
                    embed.add_field(name="Roles Removed", value=" ".join([r.mention for r in removed]))
                embed.set_author(name=str(after), icon_url=after.display_avatar.url)
                await log_ch.send(embed=embed)

    # ==========================
    # Role Events
    # ==========================
    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        log_ch = await self.get_log_channel(role.guild, "mod")
        if not log_ch:
            return
        embed = discord.Embed(
            title="🛡️ Role Created",
            description=f"**Role:** {role.mention} (`{role.id}`)\n**Color:** {role.color}",
            color=COLOR_SUCCESS,
            timestamp=discord.utils.utcnow()
        )
        await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        log_ch = await self.get_log_channel(role.guild, "mod")
        if not log_ch:
            return
        embed = discord.Embed(
            title="🛡️ Role Deleted",
            description=f"**Name:** {role.name}\n**ID:** `{role.id}`",
            color=COLOR_DANGER,
            timestamp=discord.utils.utcnow()
        )
        await log_ch.send(embed=embed)

    # ==========================
    # Channel Events
    # ==========================
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        log_ch = await self.get_log_channel(channel.guild, "mod")
        if not log_ch:
            return
        embed = discord.Embed(
            title="📁 Channel Created",
            description=f"**Name:** {channel.name}\n**Type:** {str(channel.type).capitalize()}\n**ID:** `{channel.id}`",
            color=COLOR_SUCCESS,
            timestamp=discord.utils.utcnow()
        )
        await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        log_ch = await self.get_log_channel(channel.guild, "mod")
        if not log_ch:
            return
        embed = discord.Embed(
            title="📁 Channel Deleted",
            description=f"**Name:** {channel.name}\n**Type:** {str(channel.type).capitalize()}\n**ID:** `{channel.id}`",
            color=COLOR_DANGER,
            timestamp=discord.utils.utcnow()
        )
        await log_ch.send(embed=embed)

    # ==========================
    # Voice Events
    # ==========================
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if before.channel == after.channel:
            return
        log_ch = await self.get_log_channel(member.guild, "general")
        if not log_ch:
            return

        if before.channel is None and after.channel is not None:
            # Joined voice
            embed = discord.Embed(
                title="🔊 Voice Channel Joined",
                description=f"{member.mention} joined {after.channel.mention}",
                color=COLOR_SUCCESS,
                timestamp=discord.utils.utcnow()
            )
        elif before.channel is not None and after.channel is None:
            # Left voice
            embed = discord.Embed(
                title="🔇 Voice Channel Left",
                description=f"{member.mention} left {before.channel.mention}",
                color=COLOR_WARNING,
                timestamp=discord.utils.utcnow()
            )
        else:
            # Moved
            embed = discord.Embed(
                title="🔀 Voice Channel Moved",
                description=f"{member.mention} moved from {before.channel.mention} to {after.channel.mention}",
                color=COLOR_STELLAR_CYAN,
                timestamp=discord.utils.utcnow()
            )
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        await log_ch.send(embed=embed)

    # ==========================
    # Slash Command Configuration
    # ==========================
    @commands.hybrid_command(name="setlogs", description="Set log channels for Side Quest Studio")
    @app_commands.describe(
        general_channel="Channel for general events (messages, voice, joins)",
        mod_channel="Channel for moderation and security events",
        ticket_channel="Channel for ticket creation and transcripts"
    )
    @commands.has_permissions(administrator=True)
    async def setlogs(
        self,
        ctx: commands.Context,
        general_channel: Optional[discord.TextChannel] = None,
        mod_channel: Optional[discord.TextChannel] = None,
        ticket_channel: Optional[discord.TextChannel] = None
    ):
        updates = {}
        if general_channel:
            updates["general_log_channel_id"] = general_channel.id
        if mod_channel:
            updates["mod_log_channel_id"] = mod_channel.id
        if ticket_channel:
            updates["ticket_log_channel_id"] = ticket_channel.id

        await db_manager.update_guild_config(ctx.guild.id, **updates)

        embed = discord.Embed(
            title=f"{EMOJI_CHECK} Logging Channels Configured",
            color=COLOR_SUCCESS,
            timestamp=discord.utils.utcnow()
        )
        if general_channel:
            embed.add_field(name="General Logs", value=general_channel.mention)
        if mod_channel:
            embed.add_field(name="Mod Logs", value=mod_channel.mention)
        if ticket_channel:
            embed.add_field(name="Ticket Logs", value=ticket_channel.mention)
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Logging(bot))
