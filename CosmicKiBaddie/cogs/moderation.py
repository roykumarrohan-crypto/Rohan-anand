"""
Cosmic ki baddie - Moderation Cog
Comprehensive moderation system with confirmation views, hierarchy checks, and audit logging.
"""

import discord
from discord.ext import commands
from discord import app_commands
import datetime
from typing import Optional, Union
from config import COLOR_DANGER, COLOR_SUCCESS, COLOR_WARNING, COLOR_COSMIC_PURPLE, EMOJI_SHIELD, EMOJI_CHECK, EMOJI_CROSS
from database import db_manager

class ModerationConfirmView(discord.ui.View):
    def __init__(self, author: discord.Member, target: Union[discord.Member, discord.User], action: str, timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.author = author
        self.target = target
        self.action = action
        self.value: Optional[bool] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(f"{EMOJI_CROSS} Only {self.author.mention} can confirm this action.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm Action", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="✖️")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)


class Moderation(commands.Cog, name="Moderation"):
    """Server moderation commands with strict hierarchy safety and audit logging."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Snipe caches: guild_id -> channel_id -> message data
        self.snipes: dict = {}
        self.edit_snipes: dict = {}

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        g_id = message.guild.id
        if g_id not in self.snipes:
            self.snipes[g_id] = {}
        self.snipes[g_id][message.channel.id] = {
            "content": message.content,
            "author": message.author,
            "attachments": [a.url for a in message.attachments],
            "time": discord.utils.utcnow()
        }

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild or before.content == after.content:
            return
        g_id = before.guild.id
        if g_id not in self.edit_snipes:
            self.edit_snipes[g_id] = {}
        self.edit_snipes[g_id][before.channel.id] = {
            "before": before.content,
            "after": after.content,
            "author": before.author,
            "time": discord.utils.utcnow()
        }

    def check_hierarchy(self, moderator: discord.Member, target: discord.Member) -> Optional[str]:
        """Verify role hierarchy rules to avoid targeting equals/superiors or bots/self."""
        if moderator.id == target.id:
            return "You cannot moderate yourself."
        if target.id == self.bot.user.id:
            return "Cosmic ki baddie cannot moderate herself! ✨"
        if target.id == moderator.guild.owner_id:
            return "You cannot moderate the server owner."
        if moderator.id != moderator.guild.owner_id and target.top_role >= moderator.top_role:
            return f"Cannot target {target.mention}: their highest role is equal to or higher than yours."
        bot_member = moderator.guild.me
        if target.top_role >= bot_member.top_role:
            return f"Bot cannot moderate {target.mention}: their role is higher than the bot's highest role."
        return None

    async def log_to_modchannel(self, guild: discord.Guild, embed: discord.Embed):
        """Dispatch moderation event to configured mod-logs channel."""
        cfg = await db_manager.get_guild_config(guild.id)
        channel_id = cfg.get("mod_log_channel_id")
        if channel_id:
            ch = guild.get_channel(channel_id)
            if ch and isinstance(ch, discord.TextChannel):
                try:
                    await ch.send(embed=embed)
                except Exception:
                    pass

    # ==========================
    # /kick
    # ==========================
    @commands.hybrid_command(name="kick", description="Kick a member from Side Quest Studio")
    @app_commands.describe(member="Member to kick", reason="Reason for kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        err = self.check_hierarchy(ctx.author, member)
        if err:
            return await ctx.send(f"{EMOJI_CROSS} {err}", ephemeral=True)

        embed = discord.Embed(
            title="⚠️ Kick Confirmation",
            description=f"Are you sure you want to kick **{member}** (`{member.id}`)?\n**Reason:** {reason}",
            color=COLOR_WARNING,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        view = ModerationConfirmView(ctx.author, member, "kick")
        msg = await ctx.send(embed=embed, view=view, ephemeral=True)
        await view.wait()

        if view.value:
            try:
                # Attempt DM
                try:
                    dm_embed = discord.Embed(
                        title="You were kicked from Side Quest Studio",
                        description=f"**Reason:** {reason}\n**Moderator:** {ctx.author}",
                        color=COLOR_DANGER
                    )
                    await member.send(embed=dm_embed)
                except Exception:
                    pass

                await member.kick(reason=f"{ctx.author} ({ctx.author.id}): {reason}")
                await db_manager.add_mod_action(ctx.guild.id, member.id, str(member), ctx.author.id, str(ctx.author), "KICK", reason)

                success_embed = discord.Embed(
                    title=f"{EMOJI_CHECK} Member Kicked",
                    description=f"**Target:** {member.mention} (`{member.id}`)\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                    color=COLOR_SUCCESS,
                    timestamp=discord.utils.utcnow()
                )
                await ctx.send(embed=success_embed)
                await self.log_to_modchannel(ctx.guild, success_embed)
            except Exception as e:
                await ctx.send(f"{EMOJI_CROSS} Failed to kick {member}: {e}", ephemeral=True)
        else:
            await ctx.send(f"Kick action cancelled.", ephemeral=True)

    # ==========================
    # /ban
    # ==========================
    @commands.hybrid_command(name="ban", description="Ban a member from Side Quest Studio")
    @app_commands.describe(user="User to ban", delete_message_days="Days of messages to delete (0-7)", reason="Reason for ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, user: Union[discord.Member, discord.User], delete_message_days: int = 1, *, reason: str = "No reason provided"):
        if isinstance(user, discord.Member):
            err = self.check_hierarchy(ctx.author, user)
            if err:
                return await ctx.send(f"{EMOJI_CROSS} {err}", ephemeral=True)

        delete_days = max(0, min(7, delete_message_days))
        embed = discord.Embed(
            title="🚨 Ban Confirmation",
            description=f"Are you sure you want to ban **{user}** (`{user.id}`)?\n**Delete Message Days:** {delete_days}\n**Reason:** {reason}",
            color=COLOR_DANGER,
            timestamp=discord.utils.utcnow()
        )
        view = ModerationConfirmView(ctx.author, user, "ban")
        await ctx.send(embed=embed, view=view, ephemeral=True)
        await view.wait()

        if view.value:
            try:
                if isinstance(user, discord.Member):
                    try:
                        dm_embed = discord.Embed(
                            title="You were banned from Side Quest Studio",
                            description=f"**Reason:** {reason}\n**Moderator:** {ctx.author}",
                            color=COLOR_DANGER
                        )
                        await user.send(embed=dm_embed)
                    except Exception:
                        pass

                await ctx.guild.ban(user, reason=f"{ctx.author} ({ctx.author.id}): {reason}", delete_message_days=delete_days)
                await db_manager.add_mod_action(ctx.guild.id, user.id, str(user), ctx.author.id, str(ctx.author), "BAN", reason)

                success_embed = discord.Embed(
                    title=f"{EMOJI_CHECK} User Banned",
                    description=f"**Target:** {user} (`{user.id}`)\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                    color=COLOR_DANGER,
                    timestamp=discord.utils.utcnow()
                )
                await ctx.send(embed=success_embed)
                await self.log_to_modchannel(ctx.guild, success_embed)
            except Exception as e:
                await ctx.send(f"{EMOJI_CROSS} Failed to ban {user}: {e}", ephemeral=True)
        else:
            await ctx.send(f"Ban action cancelled.", ephemeral=True)

    # ==========================
    # /unban
    # ==========================
    @commands.hybrid_command(name="unban", description="Unban a user by User ID")
    @app_commands.describe(user_id="Discord ID of banned user", reason="Reason for unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, user_id: str, *, reason: str = "Pardoned by moderator"):
        try:
            uid = int(user_id.strip())
            user = await self.bot.fetch_user(uid)
            await ctx.guild.unban(user, reason=f"{ctx.author}: {reason}")
            await db_manager.add_mod_action(ctx.guild.id, uid, str(user), ctx.author.id, str(ctx.author), "UNBAN", reason)

            embed = discord.Embed(
                title=f"{EMOJI_CHECK} User Unbanned",
                description=f"**User:** {user} (`{uid}`)\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                color=COLOR_SUCCESS
            )
            await ctx.send(embed=embed)
            await self.log_to_modchannel(ctx.guild, embed)
        except discord.NotFound:
            await ctx.send(f"{EMOJI_CROSS} Ban record not found for user ID `{user_id}`.", ephemeral=True)
        except Exception as e:
            await ctx.send(f"{EMOJI_CROSS} Failed to unban: {e}", ephemeral=True)

    # ==========================
    # /timeout & /untimeout
    # ==========================
    @commands.hybrid_command(name="timeout", description="Timeout (mute) a member for a specified duration in minutes")
    @app_commands.describe(member="Target member", minutes="Duration in minutes (1 - 40320)", reason="Reason for timeout")
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx: commands.Context, member: discord.Member, minutes: int, *, reason: str = "Rule violation"):
        err = self.check_hierarchy(ctx.author, member)
        if err:
            return await ctx.send(f"{EMOJI_CROSS} {err}", ephemeral=True)

        if minutes <= 0 or minutes > 40320:
            return await ctx.send(f"{EMOJI_CROSS} Timeout duration must be between 1 minute and 28 days (40320 mins).", ephemeral=True)

        duration = datetime.timedelta(minutes=minutes)
        until = discord.utils.utcnow() + duration

        try:
            await member.timeout(duration, reason=f"{ctx.author}: {reason}")
            await db_manager.add_mod_action(ctx.guild.id, member.id, str(member), ctx.author.id, str(ctx.author), f"TIMEOUT ({minutes}m)", reason)

            embed = discord.Embed(
                title=f"{EMOJI_CHECK} Member Timed Out",
                description=f"**Target:** {member.mention}\n**Duration:** {minutes} minutes (until <t:{int(until.timestamp())}:R>)\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}",
                color=COLOR_WARNING,
                timestamp=discord.utils.utcnow()
            )
            await ctx.send(embed=embed)
            await self.log_to_modchannel(ctx.guild, embed)
        except Exception as e:
            await ctx.send(f"{EMOJI_CROSS} Failed to timeout {member}: {e}", ephemeral=True)

    @commands.hybrid_command(name="untimeout", description="Remove timeout from a member")
    @app_commands.describe(member="Member to untimeout", reason="Reason for removing timeout")
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Timeout cleared"):
        err = self.check_hierarchy(ctx.author, member)
        if err:
            return await ctx.send(f"{EMOJI_CROSS} {err}", ephemeral=True)

        try:
            await member.timeout(None, reason=f"{ctx.author}: {reason}")
            await db_manager.add_mod_action(ctx.guild.id, member.id, str(member), ctx.author.id, str(ctx.author), "UNTIMEOUT", reason)

            embed = discord.Embed(
                title=f"{EMOJI_CHECK} Timeout Removed",
                description=f"**Target:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                color=COLOR_SUCCESS
            )
            await ctx.send(embed=embed)
            await self.log_to_modchannel(ctx.guild, embed)
        except Exception as e:
            await ctx.send(f"{EMOJI_CROSS} Failed to remove timeout: {e}", ephemeral=True)

    # ==========================
    # /warn, /warnings, /clearwarns
    # ==========================
    @commands.hybrid_command(name="warn", description="Issue a formal warning to a member")
    @app_commands.describe(member="Member to warn", reason="Reason for warning")
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Rule violation"):
        err = self.check_hierarchy(ctx.author, member)
        if err:
            return await ctx.send(f"{EMOJI_CROSS} {err}", ephemeral=True)

        warn_id = await db_manager.add_warning(ctx.guild.id, member.id, ctx.author.id, reason)
        all_warns = await db_manager.get_warnings(ctx.guild.id, member.id)
        total_warns = len(all_warns)

        # Notify member via DM
        try:
            dm_embed = discord.Embed(
                title="⚠️ You Received a Warning in Side Quest Studio",
                description=f"**Reason:** {reason}\n**Warning #:** {total_warns}\n**Moderator:** {ctx.author}",
                color=COLOR_WARNING
            )
            await member.send(embed=dm_embed)
        except Exception:
            pass

        embed = discord.Embed(
            title=f"{EMOJI_SHIELD} Warning Issued (#{warn_id})",
            description=f"**Target:** {member.mention} (`{member.id}`)\n**Total Warnings:** {total_warns}\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}",
            color=COLOR_WARNING,
            timestamp=discord.utils.utcnow()
        )
        await ctx.send(embed=embed)
        await self.log_to_modchannel(ctx.guild, embed)

        # Auto-escalation check (e.g. 3 warnings -> 1h timeout)
        cfg = await db_manager.get_guild_config(ctx.guild.id)
        max_warns = cfg.get("max_warnings", 3)
        if total_warns >= max_warns:
            try:
                await member.timeout(datetime.timedelta(hours=1), reason=f"Auto-escalation: reached {total_warns} warnings.")
                auto_embed = discord.Embed(
                    title="🚨 Auto Escalation",
                    description=f"{member.mention} reached **{total_warns}** warnings and has been placed on 1-hour timeout.",
                    color=COLOR_DANGER
                )
                await ctx.send(embed=auto_embed)
            except Exception:
                pass

    @commands.hybrid_command(name="warnings", description="View warnings for a member")
    @app_commands.describe(member="Target member")
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx: commands.Context, member: discord.Member):
        warns = await db_manager.get_warnings(ctx.guild.id, member.id)
        if not warns:
            return await ctx.send(f"{member.mention} has a clean record with 0 warnings! ✨", ephemeral=True)

        embed = discord.Embed(
            title=f"⚠️ Warnings for {member} ({len(warns)})",
            color=COLOR_WARNING,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        for w in warns[:10]:
            mod = ctx.guild.get_member(w['moderator_id'])
            mod_str = mod.mention if mod else f"ID {w['moderator_id']}"
            embed.add_field(
                name=f"Warn #{w['id']} - <t:{int(w['timestamp'])}:d>",
                value=f"**Reason:** {w['reason']}\n**Mod:** {mod_str}",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="clearwarns", description="Clear all warnings for a member")
    @app_commands.describe(member="Target member")
    @commands.has_permissions(kick_members=True)
    async def clearwarns(self, ctx: commands.Context, member: discord.Member):
        count = await db_manager.clear_warnings(ctx.guild.id, member.id)
        embed = discord.Embed(
            title=f"{EMOJI_CHECK} Warnings Cleared",
            description=f"Cleared **{count}** warning(s) for {member.mention}.",
            color=COLOR_SUCCESS
        )
        await ctx.send(embed=embed)

    # ==========================
    # /slowmode, /lock, /unlock, /hide, /unhide
    # ==========================
    @commands.hybrid_command(name="slowmode", description="Set channel slowmode in seconds (0 to disable)")
    @app_commands.describe(seconds="Slowmode delay (0-21600 seconds)")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, seconds: int):
        secs = max(0, min(21600, seconds))
        await ctx.channel.edit(slowmode_delay=secs)
        status = f"set to **{secs}s**" if secs > 0 else "disabled"
        await ctx.send(f"{EMOJI_CHECK} Slowmode {status} in {ctx.channel.mention}.")

    @commands.hybrid_command(name="lock", description="Lock the current channel to prevent members from typing")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        target = channel or ctx.channel
        overwrite = target.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await target.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = discord.Embed(
            title="🔒 Channel Locked",
            description=f"{target.mention} has been locked by {ctx.author.mention}.",
            color=COLOR_DANGER
        )
        await target.send(embed=embed)
        if target != ctx.channel:
            await ctx.send(f"{EMOJI_CHECK} Locked {target.mention}.", ephemeral=True)

    @commands.hybrid_command(name="unlock", description="Unlock a channel allowing members to type again")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        target = channel or ctx.channel
        overwrite = target.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await target.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = discord.Embed(
            title="🔓 Channel Unlocked",
            description=f"{target.mention} has been unlocked by {ctx.author.mention}.",
            color=COLOR_SUCCESS
        )
        await target.send(embed=embed)
        if target != ctx.channel:
            await ctx.send(f"{EMOJI_CHECK} Unlocked {target.mention}.", ephemeral=True)

    @commands.hybrid_command(name="hide", description="Hide a channel from regular members")
    @commands.has_permissions(manage_channels=True)
    async def hide(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        target = channel or ctx.channel
        overwrite = target.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = False
        await target.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"{EMOJI_CHECK} Channel {target.mention} is now hidden from @everyone.", ephemeral=True)

    @commands.hybrid_command(name="unhide", description="Unhide a channel to make it visible again")
    @commands.has_permissions(manage_channels=True)
    async def unhide(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        target = channel or ctx.channel
        overwrite = target.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = True
        await target.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"{EMOJI_CHECK} Channel {target.mention} is now visible.", ephemeral=True)

    # ==========================
    # /nick, /role, /snipe, /editsnipe, /modlogs
    # ==========================
    @commands.hybrid_command(name="nick", description="Change a member's nickname")
    @app_commands.describe(member="Target member", nickname="New nickname (leave empty to reset)")
    @commands.has_permissions(manage_nicknames=True)
    async def nick(self, ctx: commands.Context, member: discord.Member, *, nickname: Optional[str] = None):
        err = self.check_hierarchy(ctx.author, member)
        if err:
            return await ctx.send(f"{EMOJI_CROSS} {err}", ephemeral=True)
        old_nick = member.display_name
        await member.edit(nick=nickname)
        await ctx.send(f"{EMOJI_CHECK} Changed {member.mention}'s nickname from `{old_nick}` to `{nickname or member.name}`.")

    @commands.hybrid_command(name="snipe", description="View the most recently deleted message in this channel")
    @commands.has_permissions(manage_messages=True)
    async def snipe(self, ctx: commands.Context):
        g_snipes = self.snipes.get(ctx.guild.id, {})
        data = g_snipes.get(ctx.channel.id)
        if not data:
            return await ctx.send(f"There's nothing to snipe in {ctx.channel.mention}!", ephemeral=True)

        embed = discord.Embed(
            description=data["content"] or "*[No text content]*",
            color=COLOR_COSMIC_PURPLE,
            timestamp=data["time"]
        )
        embed.set_author(name=str(data["author"]), icon_url=data["author"].display_avatar.url)
        if data["attachments"]:
            embed.add_field(name="Attachments", value="\n".join(data["attachments"]))
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="editsnipe", description="View the original text of the most recently edited message")
    @commands.has_permissions(manage_messages=True)
    async def editsnipe(self, ctx: commands.Context):
        g_snipes = self.edit_snipes.get(ctx.guild.id, {})
        data = g_snipes.get(ctx.channel.id)
        if not data:
            return await ctx.send(f"No recent edits recorded in {ctx.channel.mention}!", ephemeral=True)

        embed = discord.Embed(color=COLOR_COSMIC_PURPLE, timestamp=data["time"])
        embed.set_author(name=str(data["author"]), icon_url=data["author"].display_avatar.url)
        embed.add_field(name="Before", value=data["before"][:1024] or "*[Empty]*", inline=False)
        embed.add_field(name="After", value=data["after"][:1024] or "*[Empty]*", inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="modlogs", description="View recent moderation records for the server or a specific user")
    @app_commands.describe(user="Optional user to filter logs", limit="Number of records to show (1-25)")
    @commands.has_permissions(kick_members=True)
    async def modlogs(self, ctx: commands.Context, user: Optional[discord.User] = None, limit: int = 10):
        records = await db_manager.get_mod_logs(ctx.guild.id, limit=limit, target_id=user.id if user else None)
        if not records:
            return await ctx.send("No moderation records found.", ephemeral=True)

        embed = discord.Embed(
            title=f"🛡️ Moderation History ({'Global' if not user else user.name})",
            color=COLOR_COSMIC_PURPLE,
            timestamp=discord.utils.utcnow()
        )
        for r in records[:15]:
            embed.add_field(
                name=f"Case #{r['id']} | {r['action']} - <t:{int(r['timestamp'])}:d>",
                value=f"**Target:** {r['target_name']} (`{r['target_id']}`)\n**Mod:** {r['moderator_name']}\n**Reason:** {r['reason']}",
                inline=False
            )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
