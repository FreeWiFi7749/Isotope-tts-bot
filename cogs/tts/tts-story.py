import discord
from discord.ext import commands
import httpx
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

api_url = os.getenv('TTS_ISOTOPE_API_URL')

class TTSStory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="gs")
    @commands.is_owner()
    async def generate_story(self, ctx):
        async with httpx.AsyncClient() as client:
            first_msg = await ctx.send("ストーリーを生成しています。しばらくお待ちください。")
            response = await client.post(f"{api_url}api/v01/generate_speech/gpt/story/")
            if response.status_code != 200:
                await first_msg.edit(content="ストーリー生成に失敗しました。")
                return

            data = response.json()
            audio_url = data.get("audio_url")
            if not audio_url:
                await first_msg.edit(content="音声URLが見つかりませんでした。")
                return

            voice_channel = ctx.author.voice.channel
            if not voice_channel:
                await first_msg.edit(content="ボイスチャンネルに接続してください。")
                return
            await first_msg.edit(content="ストーリーが生成されました。再生します。")

            vc = await voice_channel.connect()
            vc.play(discord.FFmpegPCMAudio(audio_url))

            while vc.is_playing():
                await asyncio.sleep(1)
            await vc.disconnect()

async def setup(bot):
    await bot.add_cog(TTSStory(bot))

