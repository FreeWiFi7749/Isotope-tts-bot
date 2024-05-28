import discord
import os
import json
import re
import logging

from discord.ext import commands
from discord import app_commands

from utils.error import handle_command_error, handle_application_command_error

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class GlobalDicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.tree.on_error = handle_application_command_error

    async def save_golodbal_url_dic(self, domain, 読み方):
        BASE_PATH = "data/tts/v00/global/dic/"
        if not os.path.exists(BASE_PATH):
            os.makedirs(BASE_PATH, exist_ok=True)
        user_path = os.path.join(BASE_PATH, "url")
        os.makedirs(user_path, exist_ok=True)
        setting_file = os.path.join(user_path, "url.json")
        
        if os.path.exists(setting_file):
            with open(setting_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}

        data[domain] = 読み方

        with open(setting_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        logging.info(f"URL辞書を保存しました: {setting_file}")

    async def load_golodbal_url_dic(self) -> dict:
        BASE_PATH = "data/tts/v00/global/dic/url"
        setting_file = os.path.join(BASE_PATH, "url.json")
        if os.path.exists(setting_file):
            with open(setting_file, 'r', encoding='utf-8') as f:
                logging.info(f"URL辞書を読み込みました: {setting_file}")
                return json.load(f)
        logging.warning(f"URL辞書が見つかりません: {setting_file}")
        return {}
    
    async def save_golodbal_text_dic(self, text, 読み方):
        BASE_PATH = "data/tts/v00/global/dic/text"
        if not os.path.exists(BASE_PATH):
            os.makedirs(BASE_PATH, exist_ok=True)
        setting_file = os.path.join(BASE_PATH, "text.json")
        
        if os.path.exists(setting_file):
            with open(setting_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}

        data[text] = 読み方

        with open(setting_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        logging.info(f"テキスト辞書を保存しました: {setting_file}")

    async def load_golodbal_text_dic(self) -> dict:
        BASE_PATH = "data/tts/v00/global/dic/text"
        setting_file = os.path.join(BASE_PATH, "text.json")
        if os.path.exists(setting_file):
            with open(setting_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logging.info(f"テキスト辞書を読み込みました: {setting_file}")
                return data
        logging.warning(f"テキスト辞書が見つかりません: {setting_file}")
        return {}
    
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

        await self.save_golodbal_text_dic(text, 読み方)
        await ctx.send(f'Added {text} to global dic')
        logging.info(f"テキストをグローバル辞書に追加しました: {text} -> {読み方}")

    @global_dic.error
    async def global_dic_error(self, ctx, error):
        await handle_command_error(self.bot, ctx, error)

async def setup(bot):
    await bot.add_cog(GlobalDicCog(bot))