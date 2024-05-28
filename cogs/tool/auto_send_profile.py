import discord
from discord.ext import commands
import json
import os
from utils.error import handle_command_error, handle_application_command_error

data_path = "data/tool/auto_s_p"

class AutoSendProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.tree.on_error = handle_application_command_error

    def get_guild_settings(self, guild_id):
        if not os.path.exists(data_path):
            os.makedirs(data_path, exist_ok=True)
        settings_path = f"{data_path}/{guild_id}/settings.json"
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                return json.load(f)
        return {"enabled": False}
    
    def save_guild_settings(self, guild_id, settings):
        if not os.path.exists(data_path):
            os.makedirs(data_path, exist_ok=True)
        settings_path = f"{data_path}/{guild_id}/settings.json"
        if not os.path.exists(os.path.dirname(settings_path)):
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        with open(settings_path, 'w') as f:
            json.dump(settings, f)

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.bot.user.mentioned_in(message):
            guild_settings = self.get_guild_settings(message.guild.id)
            if guild_settings.get("enabled", False):
                embed = discord.Embed(
                    title=self.bot.user.name,
                    description="CeVIO AI 『音楽的同位体 星界(SEKAI)、裏命(RIME)、狐子(COKO)、羽累(HARU)』の音声波形を用いた読み上げBot「K+AIWA(カイワ)」です。\n\n現在利用可能な音声波形は4つ：\n•	SEKAI(ヰ世界情緒の音楽的同位体)\n•	COKO(幸祜の音楽的同位体)\n•	RIME(理芽の音楽的同位体)\n•	HARU(春猿火の音楽的同位体)\n\nまたこのBOTはCeVIO AI 『音楽的同位体』のガイドラインにしたがって運営しております。\nhttps://musical-isotope.kamitsubaki.jp/terms/",
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=self.bot.user.avatar.url)
                embed.set_image(url="https://tts.k-aiwa.vip/img/embed/_m-s-vip.webp")
                await message.channel.send(embed=embed)

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def set_auto_send(self, ctx, enabled: bool):
        guild_settings = self.get_guild_settings(ctx.guild.id)
        guild_settings["enabled"] = enabled
        self.save_guild_settings(ctx.guild.id, guild_settings)
        await ctx.send(f"自動自己紹介は{'有効' if enabled else '無効'}になりました。")

    @set_auto_send.error
    async def set_auto_send_error(self, ctx, error):
        await handle_command_error(self.bot, ctx, error)

async def setup(bot):
    await bot.add_cog(AutoSendProfileCog(bot))
