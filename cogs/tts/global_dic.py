import discord
import os
import json
import re
import logging

from discord.ext import commands
from discord import app_commands

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class GlobalDicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def save_golodbal_url_dic(self, value):
        BASE_PATH = "data/tts/v00/global/dic/"
        if not os.path.exists(BASE_PATH):
            os.makedirs(BASE_PATH, exist_ok=True)
        user_path = os.path.join(BASE_PATH, "url")
        os.makedirs(user_path, exist_ok=True)
        setting_file = os.path.join(user_path, "url.json")
        
        with open(setting_file, 'w') as f:
            json.dump({value}, f)
        logging.info(f"URL辞書を保存しました: {setting_file}")

    async def load_golodbal_url_dic(self):
        BASE_PATH = "data/tts/v00/global/dic/url"
        setting_file = os.path.join(BASE_PATH, "url.json")
        if os.path.exists(setting_file):
            with open(setting_file, 'r') as f:
                logging.info(f"URL辞書を読み込みました: {setting_file}")
                return json.load(f)
        logging.warning(f"URL辞書が見つかりません: {setting_file}")
        return None
    
    async def save_golodbal_text_dic(self, user_id, voice_id, setting_name, value):
        BASE_PATH = "data/tts/v00/global/dic/text"
        if not os.path.exists(BASE_PATH):
            os.makedirs(BASE_PATH, exist_ok=True)
        user_path = os.path.join(BASE_PATH, str(user_id), str(voice_id))
        os.makedirs(user_path, exist_ok=True)
        setting_file = os.path.join(user_path, f"{setting_name}.json")
        
        with open(setting_file, 'w') as f:
            json.dump({setting_name: value}, f)
        logging.info(f"テキスト辞書を保存しました: {setting_file}")

    async def load_golodbal_text_dic(self, user_id, voice_id, setting_name):
        BASE_PATH = "data/tts/v00/global/dic/text"
        setting_file = os.path.join(BASE_PATH, str(user_id), str(voice_id), f"{setting_name}.json")
        if os.path.exists(setting_file):
            with open(setting_file, 'r') as f:
                logging.info(f"テキスト辞書を読み込みました: {setting_file}")
                return json.load(f).get(setting_name)
        logging.warning(f"テキスト辞書が見つかりません: {setting_file}")
        return None
    
    @commands.hybrid_group()
    async def global_dic(self, ctx):
        pass

    @global_dic.command(name='add_url', aliases=['au'], description='Add url to global dic')
    @app_commands.describe(url='指定した読み方にするURL', 読み方='読み方')
    @commands.is_owner()
    async def add_url(self, ctx, url: str, 読み方: str):
        if url.startswith('https://') or url.startswith('http://'): 
            domain = f"{url.replace('https://', '').replace('http://', '').split('/')[0]}"
        else:
            domain = url
        if domain.endswith('.'):
            domain = domain[:-1]

        await self.save_golodbal_url_dic(domain, 読み方)
        await ctx.send(f'Added {url} to global dic')
        logging.info(f"URLをグローバル辞書に追加しました: {url} -> {domain}")

    @global_dic.command(name='add_text', aliases=['at'], description='Add text to global dic')
    @app_commands.describe(text='指定した読み方にする単語', 読み方='読み方')
    @commands.is_owner()
    async def add_text(self, ctx, text: str, 読み方: str):
        text = re.sub(r'\s+', '', text.lower())

        await self.save_golodbal_text_dic(ctx.author.id, ctx.voice_client.channel.id, text, 読み方)
        await ctx.send(f'Added {text} to global dic')
        logging.info(f"テキストをグローバル辞書に追加しました: {text} -> {読み方}")

async def setup(bot):
    await bot.add_cog(GlobalDicCog(bot))
    #logging.info("GlobalDicCogがセットアップされました")