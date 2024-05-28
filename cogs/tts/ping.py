import discord
from discord.ext import commands
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

api_url = os.getenv('TTS_ISOTOPE_API_URL')

class PingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ttsping')
    async def ping(self, ctx):
        API_URL = api_url + 'api/v01/ping/'
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(API_URL)
                if response.status_code == 200:
                    await ctx.send("API is online!")
                else:
                    await ctx.send(f"API responded with status code {response.status_code}")
        except Exception as e:
            await ctx.send(f"Failed to reach API: {e}")

async def setup(bot):
    await bot.add_cog(PingCog(bot))