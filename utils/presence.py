import discord
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

main_guild_id = int(os.getenv("MAIN_GUILD_ID"))

presences = [
    {"type": "Playing", "name": "情報を更新中...", "status": "online"},
    {"type": "Playing", "name": "/joinで読み上げ開始","state": "最強可愛い読み上げBOT", "status": "online"},
]

async def update_presence(bot):
    index = 0
    while not bot.is_closed():
        guild = bot.guilds[0]
        member_count = sum(1 for _ in guild.members)
        guild_count = len(bot.guilds)
        vc_count = sum(1 for _ in bot.get_all_channels() if isinstance(_, discord.VoiceChannel))
        
        custom_presence = {"type": "Watching", "name": "スタッツ情報", "state": f"合計サーバー数:{guild_count}サーバー/ユーザー数:{member_count}人/VC数:{vc_count}チャンネル", "status": "online"}
        presences[-1] = custom_presence
        if presences[index].get("name") == "情報を更新中...":
            activity = discord.Activity(type=discord.ActivityType.watching, name=custom_presence["name"], state=custom_presence.get("state", None))
            status = custom_presence["status"]
        else:
            presence = presences[index]
            activity_type = getattr(discord.ActivityType, presence["type"].lower(), discord.ActivityType.playing)
            activity = discord.Activity(type=activity_type, name=presence["name"], state=presence.get("state", None))
            status = presence["status"]
        
        await bot.change_presence(activity=activity, status=discord.Status[status])
        
        await asyncio.sleep(60)

        index = (index + 1) % len(presences)
