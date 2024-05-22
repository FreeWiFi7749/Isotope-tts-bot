import discord
import random
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

main_guild_id = int(os.getenv("MAIN_GUILD_ID"))

presences = [
    {"type": "Playing", "name": "サーバー人数を更新中...", "status": "online"},
    {"type": "Playing", "name": "/joinで読み上げ開始","state": "最強可愛い読み上げBOT", "status": "online"},

]

async def update_presence(bot):
    index = 0
    while not bot.is_closed():
        guild = bot.guilds[0]
        member_count = sum(1 for _ in guild.members)
        guild_count = len(bot.guilds)
        vc_count = sum(1 for _ in bot.get_all_channels() if isinstance(_, discord.VoiceChannel))
        
        custom_presence = {"type": "Watching", "name": "情報", "state": f"合計サーバー数:{guild_count}サーバー/ユーザー数:{member_count}人/VC数:{vc_count}チャンネル", "status": "online"}
        presences[-1] = custom_presence
        
        presence = presences[index]
        if index != 0:
            if presence["type"] == "Playing":
                activity_type = getattr(discord.ActivityType, presence["type"].lower(), discord.ActivityType.playing)
                activity = discord.Activity(type=activity_type, name=presence["name"], state=presence.get("state", None), status=presence.get("status", None))
            else:
                activity = None  # Added: default value for activity if not initialized

            if activity:  # Added: only change presence if activity is not None
                await bot.change_presence(activity=activity)
        
        await asyncio.sleep(60)

        index = (index + 1) % len(presences)