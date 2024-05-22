import discord
from discord.ext import commands
import sys
import subprocess
import platform
import asyncio
import time
import httpx
from dotenv import load_dotenv
import os

from utils import api

load_dotenv()

api_url = os.getenv('TTS_MAIN_API_URL')

class ManagementBotCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def rstart_bot(self):
        try:
            if platform.system() == "Linux":
                subprocess.Popen(["sudo", "systemctl", "restart", "nijiiro_yume.service"])
            elif platform.system() == "Darwin":
                subprocess.Popen(["/bin/sh", "-c", "sleep 1; exec python3 " + " ".join(sys.argv)])
            else:
                print("このOSはサポートされていません。")
                return
            await self.bot.close()
        except Exception as e:
            print(f"再起動中にエラーが発生しました: {e}")


    @commands.hybrid_command(name='restart', hidden=True)
    async def restart(self, ctx):
        """Botを再起動する"""
        msg = await ctx.send('10秒後にBotを再起動します')
        for i in range(9, 0, -1):
            await asyncio.sleep(1)
            await msg.edit(content=f"{i}秒後にBotを再起動します")
            if i == 1:
                await msg.edit(content="Botの再起動を開始します...")
                
        await self.rstart_bot()

    @commands.hybrid_command(name='ping', hidden=True)
    async def ping(self, ctx):
        """BotのPingを表示します"""
        start_time = time.monotonic()
        api_ping = await api.measure_api_ping()

        if not api_ping:
            color = discord.Color.red()
        else:
            color = discord.Color.green()

        e = discord.Embed(title="Pong!", color=color)
        e.add_field(name="API Ping", value=f"{round(api_ping)}ms" if api_ping else "測定失敗", inline=True)
        e.add_field(name="WebSocket Ping", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        sent_message = await ctx.send(embed=e)
        end_time = time.monotonic()

        bot_ping = round((end_time - start_time) * 1000)

        e.add_field(name="Bot Ping", value=f"{bot_ping}ms", inline=True)

        # TTS API Ping
        tts_api_url = api_url + '/ping'
        try:
            tts_start_time = time.monotonic()
            async with httpx.AsyncClient() as client:
                response = await client.get(tts_api_url)
            tts_end_time = time.monotonic()
            tts_api_ping = round((tts_end_time - tts_start_time) * 1000)
            if response.status_code == 200:
                tts_api_status = "API is online!"
            else:
                tts_api_status = f"API responded with status code {response.status_code}"
        except Exception as e:
            tts_api_status = f"Failed to reach API: {e}"

        e.add_field(name="TTS API Ping", value=f"{tts_api_ping}ms", inline=True)
        e.add_field(name="TTS API Status", value=tts_api_status, inline=True)
        await sent_message.edit(embed=e)

async def setup(bot):
    await bot.add_cog(ManagementBotCog(bot))
