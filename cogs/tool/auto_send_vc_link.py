from discord.ext import commands
import json
import os
from utils.error import handle_command_error, handle_application_command_error

data_path = "data/tool/auto_s_vcl"

class AutoSendVCLinkCog(commands.Cog):
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
        if message.author.bot:
            return

        if message.content.endswith('!sl'):
            if message.author.voice and message.author.voice.channel:
                vc_url = f"https://discord.com/channels/{message.guild.id}/{message.author.voice.channel.id}"
                av_msg = f"[{message.author.mention}のVC]({vc_url})"
                await message.channel.send(av_msg)
            else:
                pass

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def set_auto_send_vc_link(self, ctx, enabled: bool):
        guild_settings = self.get_guild_settings(ctx.guild.id)
        guild_settings["enabled"] = enabled
        self.save_guild_settings(ctx.guild.id, guild_settings)
        await ctx.send(f"自動VCリンク送信は{'有効' if enabled else '無効'}になりました。")

    @set_auto_send_vc_link.error
    async def set_auto_send_vc_link_error(self, ctx, error):
        await handle_command_error(self.bot, ctx, error)

async def setup(bot):
    await bot.add_cog(AutoSendVCLinkCog(bot))
