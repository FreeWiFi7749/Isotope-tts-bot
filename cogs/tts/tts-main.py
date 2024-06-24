import os
import json
import discord
import httpx
import pykakasi
import tempfile
import asyncio
import logging
import platform
import ctypes.util
import re
import alkana
import time
import shutil
from discord.utils import get
from collections import deque

from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

from cogs.tts.user_setting import TTSUserSettingsCog
from utils.join_message import join_message, leave_message
from cogs.tts.global_dic import GlobalDicCog
from utils.error import handle_command_error, handle_application_command_error
from cogs.tts.rp import RichPresence

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %Y-%m-%d %H:%M:%S - %(message)s')

load_dotenv()

BASE_PATH = "data/tts/v00/user-data"
STATS_PATH = "data/tts/v00/stats"

api_url = os.getenv('TTS_ISOTOPE_API_URL')

class TTSMainCog(commands.Cog):
    def __init__(self, bot, user_settings):
        self.bot = bot
        self.user_settings = user_settings
        self.voice_channels = {}
        self.currently_playing = {}
        self.queues = {}
        self.active_channels = {}
        self.whitelist_file = "data/tts/v01/whitelist.json"
        self.whitelisted_users = self.load_whitelist()
        self.whitelisted_roles = self.load_whitelist_roles()
        self.kakasi = pykakasi.kakasi()
        self.kakasi.setMode("K", "K")
        self.kakasi.setMode("J", "K")
        self.converter = self.kakasi.getConverter()
        self.bot.tree.on_error = handle_application_command_error

        if not discord.opus.is_loaded():
            opus_path = None
            if platform.system() == 'Darwin':
                opus_path = ctypes.util.find_library('opus') or '/opt/homebrew/lib/libopus.dylib'
            elif platform.system() == 'Linux':
                opus_path = ctypes.util.find_library('opus') or 'libopus.so'
            
            if opus_path:
                discord.opus.load_opus(opus_path)
            else:
                raise RuntimeError('Opus library not found')

        if not shutil.which("ffmpeg"):
            raise RuntimeError("ffmpeg was not found. Please install ffmpeg and ensure it is in your PATH.")

        self.stats = {
            "command": self.load_stats("command.json"),
            "vc": self.load_stats("vc.json"),
            "message": self.load_stats("message.json"),
            "error": self.load_stats("error.json")
        }

    def load_stats(self, filename):
        if not os.path.exists(STATS_PATH):
            os.makedirs(STATS_PATH, exist_ok=True)
        filepath = os.path.join(STATS_PATH, filename)
        if (os.path.exists(filepath)):
            with open(filepath, 'r') as f:
                return json.load(f)
        return {"count": 0}

    def save_stats(self, filename, data):
        logging.debug(f"Saving stats to file: {filename}")
        filepath = os.path.join(STATS_PATH, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f)

    def increment_stat(self, stat_type):
        logging.debug(f"Incrementing stat: {stat_type}")
        self.stats[stat_type]["count"] += 1
        self.save_stats(f"{stat_type}.json", self.stats[stat_type])

    def load_whitelist(self):
        if os.path.exists(self.whitelist_file):
            with open(self.whitelist_file, 'r') as f:
                return set(json.load(f))
        return set()

    def save_whitelist(self):
        with open(self.whitelist_file, 'w') as f:
            json.dump(list(self.whitelisted_users), f)

    def load_whitelist_roles(self):
        whitelist_roles_file = "data/tts/v01/whitelist_roles.json"
        if os.path.exists(whitelist_roles_file):
            with open(whitelist_roles_file, 'r') as f:
                return set(json.load(f))
        return set()

    def save_whitelist_roles(self):
        whitelist_roles_file = "data/tts/v01/whitelist_roles.json"
        with open(whitelist_roles_file, 'w') as f:
            json.dump(list(self.whitelisted_roles), f)

    def is_whitelisted(self, user):
        if isinstance(user, discord.Member):
            if user.id in self.whitelisted_users:
                return True
            for role in user.roles:
                if role.id in self.whitelisted_roles:
                    return True
        return False

    async def process_queue(self, guild_id):
        while True:
            if self.queues[guild_id]:
                logging.debug(f"Queue size before processing: {len(self.queues[guild_id])}")
                message = self.queues[guild_id].popleft()
                logging.debug(f"Processing message: {message.content if isinstance(message, discord.Message) else message}")
                await self.process_message(message)
                logging.debug(f"Queue size after processing: {len(self.queues[guild_id])}")
            await asyncio.sleep(1)

    async def play_next_in_queue(self, guild_id, item=None):
        if item:
            self.queues[guild_id].append(item)
        
        if len(self.queues[guild_id]) > 0:
            next_item = self.queues[guild_id].popleft()
            if isinstance(next_item, str) and os.path.exists(next_item):
                self.voice_channels[guild_id].play(discord.FFmpegPCMAudio(next_item), after=lambda e: self.bot.loop.create_task(self.play_next_in_queue(guild_id)))
                self.currently_playing[guild_id] = True
            elif isinstance(next_item, discord.Message):
                await self.process_message(next_item)
            else:
                self.currently_playing[guild_id] = False
        else:
            self.currently_playing[guild_id] = False

    def load_user_setting(self, user_id, voice_id, setting_name):
        setting_file = os.path.join(BASE_PATH, str(user_id), str(voice_id), f"{setting_name}.json")
        if os.path.exists(setting_file):
            with open(setting_file, 'r') as f:
                return json.load(f).get(setting_name)
        return None
    
    def load_global_url_dic(self, user_id, voice_id, setting_name):
        BASE_PATH = "data/tts/v00/global/dic/url"
        setting_file = os.path.join(BASE_PATH, str(user_id), str(voice_id), f"{setting_name}.json")
        if os.path.exists(setting_file):
            with open(setting_file, 'r') as f:
                return json.load(f).get(setting_name)
        return None
    
    async def leave_vc(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in self.voice_channels:
            vc = self.voice_channels[guild_id].channel
            logging.info(f"Attempting to disconnect from voice channel: {vc}")
            eff = discord.Embed(title="切断中", description=f"{vc} から切断します。")
            msgGG = await ctx.send(embed=eff)
            leave_msg = f"{vc}から切断します。"
            payload = {
                'narrator': self.user_settings.load_user_voice(ctx.author.id),
                'text': leave_msg,
                'temperature': 0
            }
            await leave_message(api_url, payload, ctx, self)
            while self.voice_channels[guild_id].is_playing():
                logging.debug("Waiting for current playback to finish before disconnecting.")
                await asyncio.sleep(1)
            await self.voice_channels[guild_id].disconnect(force=True)
            logging.info(f"Disconnected from voice channel: {vc}")
            del self.voice_channels[guild_id]
            del self.active_channels[guild_id]
            del self.queues[guild_id]
            del self.currently_playing[guild_id]
            es = discord.Embed(title="切断しました", description=f"{vc} から切断しました。")
            await msgGG.edit(embed=es)

            # リッチプレゼンスをクリア
            rich_presence = self.bot.get_cog("RichPresence")
            if rich_presence:
                for member in vc.members:
                    await rich_presence.clear_presence(member.id)
        else:
            logging.warning("No voice channel to disconnect from.")
            await ctx.send("現在接続しているボイスチャンネルがありません。")

    async def join_vc(self, ctx: commands.Context):
        if ctx.guild is None:
            await ctx.send("このコマンドはサーバー内でのみ使用できます。")
            return

        guild_id = ctx.guild.id
        if ctx.author.voice:
            vc = ctx.author.voice.channel
            if guild_id in self.voice_channels and self.voice_channels[guild_id].channel == vc:
                await ctx.send("すでにこのボイスチャンネルに接続しています。")
                return

            self.voice_channels[guild_id] = await vc.connect(self_deaf=True)
            self.active_channels[guild_id] = ctx.channel
            self.queues[guild_id] = deque()
            self.currently_playing[guild_id] = False

            logging.info(f"Joined voice channel: {vc.name}")
            ef = discord.Embed(title="接続中", description=f"{vc.name} に接続しています。")
            msg_j = await ctx.send(embed=ef)
            join_msg = f"{vc.name}に接続しました。"
            payload = {
                'narrator': self.user_settings.load_user_voice(ctx.author.id),
                'text': join_msg,
                'temperature': 0
            }
            self.bot.loop.create_task(join_message(api_url, payload, ctx, self))
            tts_api_url = api_url + 'api/v01/ping/'
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

            es = discord.Embed(title="接続しました", description=f"- 接続したボイスチャンネル: {vc.mention}\n\n- 接続状況: {tts_api_ping}ms")
            await msg_j.edit(embed=es)
            self.increment_stat("vc")

            rich_presence = self.bot.get_cog("RichPresence")
            if rich_presence:
                for member in vc.members:
                    await rich_presence.update_presence(member.id, vc_member_count=len(vc.members))
        else:
            await ctx.send("ボイスチャンネルに接続している必要があります。")
            logging.warning("Attempted to join voice channel without being in a voice channel.")

    async def synthesize_and_play(self, message, channel=None, author=None):
        guild_id = message.guild.id
        self.queues[guild_id].append(message)
        logging.debug(f"Added message to queue: {message.content if isinstance(message, discord.Message) else message}")
        if message.channel:
            await message.channel.send("現在の読み上げをキューに追加しました。")
        logging.info("Added to queue.")
        
        if not self.currently_playing[guild_id]:
            await self.play_next_in_queue(guild_id)

    async def process_message(self, message):
        logging.info("process_message called")
        if isinstance(message, str):
            if message.author:
                user_id = message.author.id
                voice_id = self.user_settings.load_user_voice(user_id)
                text = message.content
            else:
                user_id = None
                voice_id = "SEKAI"
                text = message
        else:
            user_id = message.author.id
            voice_id = self.user_settings.load_user_voice(user_id)
            text = message.content

        if text is None:
            logging.error("Message content is None.")
            return
        
        if voice_id == None:
            voice_id = "SEKAI"

        kana_text = alkana.get_kana(text)
        
        if kana_text:
            result = self.kakasi.convert(kana_text)
            kana_text = "".join([item['kana'] for item in result])
        else:
            kana_text = text
        
        if not kana_text:
            logging.error("Failed to convert text to kana.")
            kana_text = text

        payload = {
            'text': kana_text,
            'narrator': voice_id,
            'temperature': 0
        }

        timeout = None
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            try:
                response = await client.post(
                    f"{api_url}api/v01/generate_speech/",
                    json=payload
                )

                if response.status_code == 200:
                    response_data = response.json()
                    audio_url = response_data.get('audio_url')
                    if (audio_url):
                        dl_response = await client.get(f"{api_url}{audio_url}")
                        if dl_response.status_code == 200:
                            fd, tmp_path = tempfile.mkstemp()
                            with os.fdopen(fd, 'wb') as tmp:
                                tmp.write(dl_response.content)

                            if os.path.exists(tmp_path):
                                guild_id = message.guild.id
                                self.queues[guild_id].append(tmp_path)
                                logging.debug(f"Added synthesized audio to queue: {tmp_path}")
                                if not self.currently_playing[guild_id]:
                                    await self.play_next_in_queue(guild_id)
                                self.increment_stat("message")
                            else:
                                logging.error(f"File not found: {tmp_path}")
                                if message.channel:
                                    await message.channel.send("ダウンロードしたファイルが見つかりませんでした。")
                        else:
                            logging.error(f"Failed to download file: {dl_response.status_code}")
                            if message.channel:
                                await message.channel.send("ファイルのダウンロードに失敗しました。")
                    else:
                        logging.error("Audio URL is missing in the response.")
                        if message.channel:
                            await message.channel.send("レスポンスにAudio URLが含まれていません。")
                else:
                    logging.error(f"Failed to synthesize: {response.status_code}")
                    error_message = response.json().get('message')
                    if message.channel:
                        await message.channel.send(f"音声合成に失敗しました: {str(response.status_code)} {error_message}")
                    self.increment_stat("error")
            except httpx.ReadTimeout:
                logging.error("Request timed out")
                if message.channel:
                    await message.channel.send("リクエストがタイムアウトしました。")
                self.increment_stat("error")
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                if message.channel:
                    await message.channel.send("エラーが発生しました。")
                self.increment_stat("error")
            finally:
                pass

    def reset_playing_state(self):
        self.currently_playing = False
        logging.info("Reset playing state.")

    @commands.hybrid_command(name="join", aliases=['j'], description="ボイスチャンネルに接続します。")
    async def join(self, ctx):
        await self.join_vc(ctx)

    @commands.hybrid_command(name="leave", aliases=['l'], description="ボイスチャンルから切断します。")
    async def leave(self, ctx):
        await self.leave_vc(ctx)

    @commands.hybrid_command(name="skip", aliases=['s'], description="テキストを読み上げます。")
    async def skip(self, ctx):
        if self.voice_channel and self.voice_channel.is_playing():
            self.voice_channel.stop()
            self.reset_playing_state()
            await ctx.send("現在の読み上げをスキップしました。")
            logging.info("Skipped current playback.")
            await self.play_next_in_queue()
        else:
            await ctx.send("現在再生中の音声はありません。")
            logging.warning("Attempted to skip playback when nothing is playing.")

    @commands.hybrid_command(name="stats", aliases=['st'], description="統計情報を表示します。")
    async def stats(self, ctx):
        e = discord.Embed(title="統計情報")
        for stat_type, data in self.stats.items():
            e.add_field(name=stat_type, value=data["count"], inline=False)
        await ctx.send(embed=e)

    @join.error
    async def join_error(self, ctx, error):
        if ctx.command_failed:
            await handle_command_error(ctx, error)
        else:
            await handle_application_command_error(ctx, error)

    @leave.error
    async def leave_error(self, ctx, error):
        if ctx.command_failed:
            await handle_command_error(ctx, error)
        else:
            await handle_application_command_error(ctx, error)

    @skip.error
    async def skip_error(self, ctx, error):
        if ctx.command_failed:
            await handle_command_error(ctx, error)
        else:
            await handle_application_command_error(ctx, error)

    @commands.group(name="whitelist", aliases=['wl'], description="ホワイトリスト管理します。")
    async def whitelist(self, ctx):
        pass

    @whitelist.command(name="add", aliases=['a'], description="ユーザーをホワイトリストに追加します。")
    @app_commands.describe(user="ユーザーをホワイトリストに追加します。")
    @commands.is_owner()
    async def add(self, ctx, user: discord.User):
        self.whitelisted_users.add(user.id)
        self.save_whitelist()
        await ctx.send(f"{user.name} をホワイトリストに追加しました。")

    @whitelist.command(name="remove", aliases=['r'], description="ユーザーをホワイトリストから削除します。")
    @app_commands.describe(user="ユーザーをホワイトリストから削除します。")
    @commands.is_owner()
    async def remove(self, ctx, user: discord.User):
        self.whitelisted_users.discard(user.id)
        self.save_whitelist()
        await ctx.send(f"{user.name} をホワイトリストから削除しました。")

    @whitelist.command(name="list", aliases=['l'], description="ホワイトリストのユーザーを一覧表示します。")
    @commands.is_owner()
    async def list(self, ctx):
        if self.whitelisted_users:
            users = [self.bot.get_user(user_id) for user_id in self.whitelisted_users]
            user_names = ", ".join(user.name for user in users if user)
            e = discord.Embed(title="ホワイトリスト", description=user_names)
            await ctx.send(embed=e)
        else:
            await ctx.send("ホワイトリストに登録されているユーザーはいません。")

    @whitelist.command(name="add_role", aliases=['ar'], description="ロールをホワイトリストに追加します。")
    @app_commands.describe(role="ホワイトリストに追加するロール")
    @commands.is_owner()
    async def add_role(self, ctx, role: discord.Role or str):
        if isinstance(role, str):
            role = get(ctx.guild.roles, name=role)
        self.whitelisted_roles.add(role.id)
        self.save_whitelist_roles()
        await ctx.send(f"{role.name} ロールをホワイトリストに追加しました。")

    @whitelist.command(name="remove_role", aliases=['rr'], description="ロールをホワイトリストから削除します。")
    @app_commands.describe(role="ホワイトリストから削除するロール")
    @commands.is_owner()
    async def remove_role(self, ctx, role: discord.Role):
        self.whitelisted_roles.discard(role.id)
        self.save_whitelist_roles()
        await ctx.send(f"{role.name} ロールをホワイトリストから削除しました。")

    @whitelist.command(name="list_roles", aliases=['lr'], description="ホワイトリストのロールを一覧表示します。")
    @commands.is_owner()
    async def list_roles(self, ctx):
        if self.whitelisted_roles:
            guild_roles = {}
            for role_id in self.whitelisted_roles:
                for guild in self.bot.guilds:
                    role = get(guild.roles, id=role_id)
                    if role:
                        if guild.name not in guild_roles:
                            guild_roles[guild.name] = []
                        guild_roles[guild.name].append(role.name)
                        break

            e = discord.Embed(title="ホワイトリストロール")
            for guild_name, roles in guild_roles.items():
                role_names = ", ".join(roles)
                e.add_field(name=guild_name, value=role_names, inline=False)
            await ctx.send(embed=e)
        else:
            await ctx.send("ホワイトリストに登録されているロールはありません。")

    @whitelist.error
    async def whitelist_error(self, ctx, error):
        if ctx.command_failed:
            await handle_command_error(ctx, error)
        else:
            await handle_application_command_error(ctx, error)

    @add.error
    async def add_error(self, ctx, error):
        await handle_command_error(ctx, error)

    @remove.error
    async def remove_error(self, ctx, error):
        await handle_command_error(ctx, error)

    @add_role.error
    async def add_role_error(self, ctx, error):
        await handle_command_error(ctx, error)
    
    @remove_role.error
    async def remove_role_error(self, ctx, error):
        await handle_command_error(ctx, error)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        if not self.is_whitelisted(message.author):
            return
        if message.content.startswith("cb/"):
            return

        if isinstance(message.author, discord.Member):
            guild_id = message.guild.id
            if guild_id in self.active_channels and message.channel == self.active_channels[guild_id]:
                if message.author.voice and message.author.voice.channel:
                    if guild_id not in self.voice_channels or not self.voice_channels[guild_id].is_connected():
                        self.voice_channels[guild_id] = await message.author.voice.channel.connect()

                    global_dic_cog = GlobalDicCog(self.bot)
                    modified_message = message

                    domain_list = await global_dic_cog.load_golodbal_url_dic()
                    while re.search(r"http(s)?:\/\/([a-zA-Z0-9-]+\.)+[a-zA-Z0-9-]+(\/[a-zA-Z0-9-./?%&=~]*)?", modified_message.content):
                        url = re.search(r"http(s)?:\/\/([a-zA-Z0-9-]+\.)+[a-zA-Z0-9-]+(\/[a-zA-Z0-9-./?%&=~]*)?", modified_message.content).group()
                        domain = f"{url[0].replace('https://', '').replace('http://', '').split('/')[0]}"
                        print(domain)
                        if domain.endswith('.'):
                            domain = domain[:-1]
                        domainHit = False
                        for dict_domain, dict_hiragana in domain_list.items(): # {"test.com": "てすとどっとこむ"}
                            if domain.endswith(dict_domain): # "sub.test.com" == "test.com" -> False
                                modified_message.content = modified_message.content.replace(url, dict_hiragana)
                                domainHit = True
                                break
                        if not domainHit:
                            modified_message.content = modified_message.content.replace(url, "URL省略")

                    text_dict = await global_dic_cog.load_golodbal_text_dic()
                    if text_dict:
                        for word, hiragana in text_dict.items():
                            modified_message.content = modified_message.content.replace(word, hiragana)

                    if message.attachments:
                        msg_ = message.content if message.content else ""
                        for attachment in message.attachments:
                            audio_file_dic = {
                                "mp3": "エムピースリー",
                                "wav": "ワブ",
                                "m4a": "エムフォーエー",
                                "mp4": "エムピースフォー",
                                "mov": "エムオーブイ",
                                "webm": "ウェブエム",
                            }
                            img_file_dic = {
                                "png": "ピング",
                                "jpg": "ジェイペグ",
                                "jpeg": "ジェイペグ",
                                "gif": "ジフ",
                                "svg": "ベクター",
                                "webp": "ウェブピー",
                                "bmp": "ビットマップ",
                            }
                            code_file_dic = {
                                "py": "パイソン",
                                "js": "ジャバスクリプト",
                                "ts": "タイプスクリプト",
                                "html": "エイチティーエムエル",
                                "css": "シーエスエス",
                                "json": "ジェイソン",
                                "yaml": "ヤムル",
                                "yml": "ヤムル",
                                "toml": "トムル",
                                "xml": "エックスエムエル",
                                "ini": "アイエヌアイ",
                                "log": "ログ",
                                "sh": "シェル",
                                "bash": "バッシュ",
                                "bat": "バッチ",
                                "cmd": "コマンド",
                                "ps1": "パワーシェル",
                                "c": "シー",
                                "h": "エイチ",
                                "cpp": "シープラスプラス",
                                "hpp": "エイチプラスプラス",
                                "cs": "シーシャープ",
                                "java": "ジャバ",
                                "lisp": "リスプ",
                                "swift": "スウィフト",
                                "dart": "ダート",
                                "go": "ゴー",
                                "rs": "ラスト",
                                "rb": "ルビー",
                                "php": "ピーエイチピー",
                                "lua": "ルア",
                                "perl": "パール",
                                "pl": "パール",
                                "sql": "エスキューエル",
                                "tsql": "ティーエスキューエル",
                                "mysql": "マイエスキューエル",
                                "pgsql": "ピージーエスキューエル",
                                "sqlite": "スキューライト",
                                "gradle": "グレードル",
                                "conf": "コンフィグ",
                                "cfg": "コンフィグ",
                            }
                            doc_file_dic = {
                                "txt": "テキスト",
                                "pdf": "ピーディーエフ",
                                "doc": "ワード",
                                "docx": "ワード",
                                "docm": "ワード",
                                "ppt": "パワーポイント",
                                "pptx": "パワーポイント",
                                "pptm": "パワーポイント",
                                "xls": "エクセル",
                                "xlsx": "エクセル",
                                "xlsm": "エクセル",
                                "csv": "シーレスブイ",
                                "rtf": "アールティーエフ",
                                "md": "マークダウン",
                                "bin": "バイナリ",
                                "exe": "ウィンドウズアプリ",
                                "jar": "ジャー",
                                "apk": "アンドロイドアプリ",
                                "ipa": "アイオーエスアプリ",
                                "deb": "デビアン",
                                "rpm": "アールピーエム",
                                "zip": "ジップ",
                                "rar": "ラー",
                                "tar": "ター",
                                "gz": "ジージップ",
                                "7z": "セブンジップ",
                                "bz2": "ビージップツー",
                                "xz": "エックスジップ",
                                "iso": "アイエスオー",
                                "img": "イメージ",
                                "vhd": "バーチャルハードディスク",
                                "vhdx": "バーチャルハードディスク",
                                "vmdk": "バーチャルマシンディスク",
                                "dmg": "ディーエムジー",
                                "pkg": "パッケージ",
                                "crt": "ショウメイショ",
                                "key": "キー",
                                "pem": "ピーイーエム",
                            }
                            full_filename_dic = {
                                "dockerfile": "ドッカーファイル",
                                "makefile": "メイクファイル",
                                ".gitignore": "ギットイグノア",
                                ".gitattributes": "ギットアトリビュート",
                                "LICENSE": "ライセンス",
                            }
                            filename: str = attachment.filename.lower()
                            if filename.endswith(audio_file_dic.keys()):
                                attachment_type = audio_file_dic[filename.split('.')[-1]]
                            elif filename.endswith(img_file_dic.keys()):
                                attachment_type = img_file_dic[filename.split('.')[-1]]
                            elif filename.endswith(code_file_dic.keys()):
                                attachment_type = code_file_dic[filename.split('.')[-1]]
                            elif filename.endswith(doc_file_dic.keys()):
                                attachment_type = doc_file_dic[filename.split('.')[-1]]
                            elif filename in full_filename_dic.keys():
                                attachment_type = full_filename_dic[filename]
                            else:
                                attachment_type = "ファイル"

                            if msg_ == "":
                                modified_message.content = f"{attachment_type}が添付されました"
                            else:
                                modified_message.content = f"{msg_}と{attachment_type}ファイルが添付されました"

                    while re.search(r'`{3}[^\n`]*\n([^`]|\n)*`{3}', modified_message.content):
                        codeBlock = re.search(r'`{3}[^\n`]*\n([^`]|\n)*`{3}', modified_message.content).group()
                        modified_message.content = modified_message.content.replace(codeBlock, "コードブロック")
                    while re.search(r'`{1}[^`]*`{1}', modified_message.content):
                        codeBlock = re.search(r'`{1}[^`]*`{1}', modified_message.content).group()
                        modified_message.content = modified_message.content.replace(codeBlock, "コードブロック")

                    self.queues[guild_id].append(modified_message)
                    logging.debug(f"Added modified message to queue: {modified_message.content}")

                    if not self.currently_playing[guild_id]:
                        await self.play_next_in_queue(guild_id)
                else:
                    pass
            else:
                pass

async def setup(bot):
    user_settings = TTSUserSettingsCog(bot)
    await bot.add_cog(TTSMainCog(bot, user_settings))