import discord
from discord import Webhook
from discord import app_commands
from discord.ext import commands

import json
import os
import aiohttp

from dotenv import load_dotenv

from utils.error import handle_command_error, handle_application_command_error

load_dotenv()
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

if not os.path.exists('data/tts/h_s/tester/active'):
    os.makedirs('data/tts/h_s/tester/active')
if not os.path.exists('data/tts/h_s/tester/inactive'):
    os.makedirs('data/tts/h_s/tester/inactive')

def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class TesterRecruitmentCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_users = [123456789012345678, 987654321098765432]
        self.bot.tree.on_error = handle_application_command_error

    @app_commands.command(name="tester_recruitment", description="テスター募集を開始します")
    async def tester_recruitment(self, interaction: discord.Interaction, 人数: int, ch: discord.TextChannel):
        if interaction.user.id not in self.allowed_users:
            await interaction.response.send_message("このコマンドを使用する権限がありません。", ephemeral=True)
            return

        embed = discord.Embed(
            title="テスター募集",
            description="テスター募集を開始します。参加希望の方はリアクションを追加してください。",
            color=discord.Color.blue()
        )
        embed.add_field(name="募集人数", value=str(人数))
        embed.set_thumbnail(url="https://tts.k-aiwa.vip/img/help_s/tester_icon.png")

        channel = await self.bot.fetch_channel(ch.id)
        message = await channel.send(embed=embed)

        await message.add_reaction("✅")

        save_json({"message_id": message.id, "channel_id": ch.id, "募集人数": 人数}, 'data/tts/h_s/tester/active/msg.json')

        await interaction.response.send_message("テスター募集を開始しました。", ephemeral=True)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        message_id = reaction.message.id
        active_msg = load_json('data/tts/h_s/tester/active/msg.json')

        if isinstance(active_msg, list):
            active_msg = active_msg[0] if active_msg else {}

        if message_id == active_msg.get("message_id"):
            channel = reaction.message.channel
            人数 = active_msg.get("募集人数")

            # 特定のロールを付与
            role = discord.utils.get(reaction.message.guild.roles, name="Tester")
            await user.add_roles(role)

            # ユーザー名をtest_user.jsonに追加
            test_users = load_json('data/tts/h_s/tester/test_user.json')
            test_users.append({"username": user.name, "id": user.id})
            save_json(test_users, 'data/tts/h_s/tester/test_user.json')

            # メッセージの更新
            if len(test_users) >= 人数:
                embed = reaction.message.embeds[0]
                embed.description = "募集は終了しました。ありがとうございました。"
                embed.add_field(name="参加者", value="\n".join([f"{user['username']} ({user['id']})" for user in test_users]))
                embed.set_footer(text="次のテスター募集をお待ちください。")
                await reaction.message.edit(embed=embed)

                # メッセージをinactiveに移動
                save_json(active_msg, 'data/tts/h_s/tester/inactive/msg.json')
                os.remove('data/tts/h_s/tester/active/msg.json')

    @tester_recruitment.error
    async def tester_recruitment_error(self, interaction, error):
        await handle_application_command_error(self.bot, interaction, error)

async def setup(bot):
    await bot.add_cog(TesterRecruitmentCog(bot))
