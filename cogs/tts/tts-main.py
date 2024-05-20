import os
import json
from dotenv import load_dotenv
import discord
from discord.ext import commands
import httpx

load_dotenv()

api_url = os.getenv('TTS_MAIN_API_URL')

BASE_PATH = "data/tts/v00/user-data"

class TTS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_channel = None

    def load_user_setting(self, user_id, voice_id, setting_name):
        setting_file = os.path.join(BASE_PATH, str(user_id), str(voice_id), f"{setting_name}.json")
        if os.path.exists(setting_file):
            with open(setting_file, 'r') as f:
                return json.load(f).get(setting_name)
        return None

    async def join_vc(self, ctx):
        if ctx.author.voice:
            self.voice_channel = await ctx.author.voice.channel.connect()
            await ctx.send(f"{ctx.author.voice.channel} に接続しました。")
        else:
            await ctx.send("ボイスチャンネルに接続してからコマンドを実行してください。")

    async def leave_vc(self, ctx):
        if self.voice_channel:
            await self.voice_channel.disconnect()
            self.voice_channel = None
            await ctx.send("ボイスチャンネルから切断しました。")
        else:
            await ctx.send("現在接続しているボイスチャンネルがありません。")

    async def synthesize_and_play(self, message):
        user_id = message.author.id
        voice_id = "rime-v00"
        speed = self.load_user_setting(user_id, voice_id, 'speed') or 100
        pitch = self.load_user_setting(user_id, voice_id, 'pitch') or 0
        voice = self.load_user_setting(user_id, voice_id, 'voice') or "RIME v00"
        text = message.content

        async with httpx.AsyncClient() as client:
            response = await client.post(
                api_url + '/speak',
                json={
                    'text': text,
                    'voice': voice,
                    'speed': speed,
                    'pitch': pitch
                }
            )

        if response.status_code == 200:
            with open('output.wav', 'wb') as f:
                f.write(response.content)
            self.voice_channel.play(discord.FFmpegPCMAudio('output.wav'))
        else:
            await message.channel.send(f"音声合成に失敗しました: {response.json().get('error', 'Unknown error')}")

    @commands.hybrid_command()
    async def join(self, ctx):
        """ボイスチャンネルに接続します。"""
        await self.join_vc(ctx)
        if ctx.guild and ctx.guild.me:
            await ctx.guild.me.edit(deafen=True)

    @commands.hybrid_command()
    async def leave(self, ctx):
        """ボイスチャンネルから切断します。"""
        await self.leave_vc(ctx)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if self.voice_channel and message.guild and message.guild.voice_client and message.guild.voice_client.is_connected():
            await self.synthesize_and_play(message)

async def setup(bot):
    await bot.add_cog(TTS(bot))

