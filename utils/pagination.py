import discord
from typing import Callable, Optional

class Paginator(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, get_page: Callable):
        self.interaction = interaction
        self.get_page = get_page
        self.total_pages: Optional[int] = None
        self.index = 0
        super().__init__(timeout=100)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.interaction.user:
            return True
        else:
            emb = discord.Embed(
                description=f"このページネーションは{self.interaction.user.mention}専用です。",
                color=16711680
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            return False

    async def navigate(self):
        try:
            emb, self.total_pages = await self.get_page(self.index)
            if self.total_pages == 1:
                await self.interaction.response.send_message(embed=emb)
            elif self.total_pages > 1:
                self.update_buttons()
                await self.interaction.response.send_message(embed=emb, view=self)
        except IndexError:
            await self.interaction.response.send_message("ページが見つかりません。", ephemeral=True)

    async def edit_page(self, interaction: discord.Interaction):
        try:
            emb, _ = await self.get_page(self.index)
            self.update_buttons()
            await interaction.response.edit_message(embed=emb, view=self)
        except IndexError:
            await interaction.response.send_message("ページが見つかりません。", ephemeral=True)

    def update_buttons(self):
        self.children[0].disabled = self.index == 0
        self.children[1].disabled = self.index == self.total_pages - 1

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: discord.Button):
        self.index -= 1
        if self.index < 0:
            self.index = self.total_pages - 1
        await self.edit_page(interaction)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.Button):
        self.index += 1
        if self.index >= self.total_pages:
            self.index = 0
        await self.edit_page(interaction)

    async def on_timeout(self):
        message = await self.interaction.original_response()
        await message.edit(view=None)

    @staticmethod
    def compute_total_pages(total_results: int, results_per_page: int) -> int:
        total_pages = ((total_results - 1) // results_per_page) + 1
        return total_pages
