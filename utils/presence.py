import discord
import asyncio
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timezone
import pytz
import logging

load_dotenv()

STATS_PATH = "data/tts/v00/stats"
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def load_stats(filename):
    if not os.path.exists(STATS_PATH):
        os.makedirs(STATS_PATH, exist_ok=True)
    filepath = os.path.join(STATS_PATH, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return {"count": 0}

presences = [
    {"type": "Playing", "name": "BOT情報を更新中...", "state": "", "status": "online"},
    {"type": "Playing", "name": "TTS情報を更新中...", "state": "", "status": "online"},
]

async def update_presence(bot):
    index = 0
    while not bot.is_closed():
        total_member_count = sum(guild.member_count for guild in bot.guilds)
        total_guild_count = len(bot.guilds)
        total_vc_count = sum(1 for channel in bot.get_all_channels() if isinstance(channel, discord.VoiceChannel))

        vc_stats = load_stats("vc.json")
        message_stats = load_stats("message.json")
        error_stats = load_stats("error.json")

        jst = pytz.timezone('Asia/Tokyo')
        now = datetime.now(timezone.utc).astimezone(jst)
        last_update = now.strftime("%Y/%m/%d %H:%M")

        custom_presence_bot = {
            "type": "Playing",
            "name": f"BOT情報: {last_update}時点",
            "state": f"合計参加サーバー数:{total_guild_count}サーバー / ユーザー数:{total_member_count}人 / VC数:{total_vc_count}チャンネル",
            "status": "online"
        }
        custom_presence_tts = {
            "type": "Playing",
            "name": f"読み上げ情報: {last_update}時点",
            "state": f"通算接続VC数:{vc_stats['count']}チャンネル / メッセージ数:{message_stats['count']}メッセージ / エラー数:{error_stats['count']}エラー",
            "status": "online"
        }
        presences[-1] = custom_presence_bot
        presences[-2] = custom_presence_tts

        presence = presences[index]
        activity_type = getattr(discord.ActivityType, presence["type"].lower(), discord.ActivityType.playing)

        #logging.debug(f"Setting presence: {presence}, activity_type: {activity_type}")

        activity = discord.Activity(
            type=activity_type,
            name=presence["name"],
            state=presence["state"]
        )

        await bot.change_presence(activity=activity, status=discord.Status[presence["status"]])
        #logging.info(f"Presenceを更新しました: {presence}")

        await asyncio.sleep(120)

        index = (index + 1) % len(presences)
        if index == len(presences):
            index = 0
            index = 0