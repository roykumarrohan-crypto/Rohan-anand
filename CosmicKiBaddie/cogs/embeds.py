"""
Cosmic ki baddie - Embed Builder Cog
Interactive modal-driven embed creator, template saver, previewer, and publisher.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from config import COLOR_COSMIC_PURPLE, COLOR_SUCCESS, EMOJI_CHECK, EMOJI_CROSS
from database import db_manager

class EmbedBuilderModal(discord.ui.Modal, title="Cosmic Embed Designer"):
    embed_title = discord.ui.TextInput(
        label="Embed Title",
        placeholder="Enter headline...",
        max_length=256,
        required=True
    )
    embed_description = discord.ui.TextInput(
        label="Description / Body Text",
        style=discord.TextStyle.paragraph,
        placeholder="Supports markdown formatting (**bold**, *italic*, [links](url))...",
        max_length=4000,
        required=True
    )
    color_hex = discord.ui.TextInput(
        label="Hex Color Code",
        placeholder="#8A2BE2 (Cosmic Purple)",
        default="#8A2BE2",
        max_length=7,
        required=False
    )
    thumbnail_url = discord.ui.TextInput(
        label="Thumbnail Image URL",
        placeholder="https://example.com/icon.png",
        required=False
    )
    footer_text = discord.ui.TextInput(
        label="Footer Text",
        placeholder="Side Quest Studio • Official Announcement",
        max_length=150,
        required=False
    )

    def __init__(self, target_channel: discord.TextChannel):
        super().__init__()
        self.target_channel = target_channel

    async def on_submit(self, interaction: discord.Interaction):
        # Parse color
        color_val = COLOR_COSMIC_PURPLE
        if self.color_hex.value:
            try:
                cleaned = self.color_hex.value.lstrip("#")
                color_val = int(cleaned, 16)
            except ValueError:
                pass

        embed = discord.Embed(
            title=self.embed_title.value,
            description=self.embed_description.value,
            color=color_val,
            timestamp=discord.utils.utcnow()
        )
        if self.thumbnail_url.value and self.thumbnail_url.value.startswith("http"):
            embed.set_thumbnail(url=self.thumbnail_url.value)
        if self.footer_text.value:
            embed.set_footer(text=self.footer_text.value)

        view = EmbedPreviewPublishView(embed, self.target_channel)
        await interaction.response.send_message(
            f"👀 **Embed Preview** (Target: {self.target_channel.mention}):\nClick **Publish** to send it directly to the channel.",
            embed=embed,
            view=view,
            ephemeral=True
        )


class EmbedPreviewPublishView(discord.ui.View):
    def __init__(self, embed: discord.Embed, target_channel: discord.TextChannel):
        super().__init__(timeout=120)
        self.embed = embed
        self.target_channel = target_channel

    @discord.ui.button(label="Publish to Channel", style=discord.ButtonStyle.success, emoji="🚀")
    async def publish(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.target_channel.send(embed=self.embed)
            button.disabled = True
            button.label = "Published!"
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"{EMOJI_CHECK} Embed published to {self.target_channel.mention}!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"{EMOJI_CROSS} Failed to publish: {e}", ephemeral=True)


class Embeds(commands.Cog, name="Embeds"):
    """Visual embed composer with modal forms, previews, and templates."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    embed_group = app_commands.Group(name="embed", description="Design and publish custom embeds")

    @embed_group.command(name="create", description="Open interactive modal to design an embed")
    @app_commands.describe(channel="Channel where the embed will be posted")
    @commands.has_permissions(manage_messages=True)
    async def embed_create(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        target_ch = channel or interaction.channel
        await interaction.response.send_modal(EmbedBuilderModal(target_channel=target_ch))

    @embed_group.command(name="template", description="Save current embed configuration as a reusable template")
    @app_commands.describe(name="Template identifier name", title="Title", description="Body description")
    @commands.has_permissions(manage_messages=True)
    async def embed_template(self, interaction: discord.Interaction, name: str, title: str, description: str):
        await db_manager.save_embed_template(
            guild_id=interaction.guild_id,
            name=name,
            title=title,
            description=description,
            color=COLOR_COSMIC_PURPLE,
            thumbnail="",
            image="",
            author="",
            footer="Side Quest Studio",
            fields=[]
        )
        await interaction.response.send_message(f"{EMOJI_CHECK} Saved embed template as **`{name}`**.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Embeds(bot))
