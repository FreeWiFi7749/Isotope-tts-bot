import os
import json
import discord
from discord.ext import commands
import httpx
import alkana
import tempfile
import asyncio
import logging
import platform
import ctypes.util

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_PATH = "data/tts/v00/user-data"

class TTS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_channel = None
        self.currently_playing = False
        self.queue = asyncio.Queue()  # キューを追加
        self.bot.loop.create_task(self.process_queue())  # キューを処理するタスクを開始
        if not discord.opus.is_loaded():
            opus_path = None
            if platform.system() == 'Darwin':  # macOS
                opus_path = ctypes.util.find_library('opus') or '/opt/homebrew/lib/libopus.dylib'
            elif platform.system() == 'Linux':
                opus_path = ctypes.util.find_library('opus') or 'libopus.so'
            
            if opus_path:
                discord.opus.load_opus(opus_path)
            else:
                raise RuntimeError('Opus library not found')

    async def process_queue(self):
        while True:
            message = await self.queue.get()
            await self.process_message(message)

    async def play_next_in_queue(self, item=None):
        if item:
            await self.queue.put(item)
        
        if not self.queue.empty():
            next_item = await self.queue.get()
            if isinstance(next_item, str) and os.path.exists(next_item):
                self.voice_channel.play(discord.FFmpegPCMAudio(next_item), after=lambda e: self.bot.loop.create_task(self.play_next_in_queue()))
                self.currently_playing = True
            elif isinstance(next_item, discord.Message):
                await self.process_message(next_item)
            else:
                logging.error("Queue item is neither a file path nor a message object.")
                self.currently_playing = False
        else:
            self.currently_playing = False

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
            logging.info(f"Joined voice channel: {ctx.author.voice.channel}")
        else:
            await ctx.send("ボイスチャンネルに接続してからコマンドを実行してください。")
            logging.warning("Attempted to join voice channel without being in one.")

    async def leave_vc(self, ctx):
        if self.voice_channel:
            await self.voice_channel.disconnect()
            self.voice_channel = None
            await ctx.send("ボイスチャンネルから切断しました。")
            logging.info("Disconnected from voice channel.")
        else:
            await ctx.send("現在接続しているボイスチャンネルがありません。")
            logging.warning("Attempted to leave voice channel without being connected.")

    async def synthesize_and_play(self, message):
        await self.queue.put(message)
        await message.channel.send("現在の読み上げをキューに追加しました。")
        logging.info("Added to queue.")
        
        if not self.currently_playing:
            await self.play_next_in_queue()

    async def process_message(self, message):
        user_id = message.author.id
        voice_id = "SEKAI"
        speed = self.load_user_setting(user_id, voice_id, 'speed') or 100
        pitch = self.load_user_setting(user_id, voice_id, 'pitch') or 0
        voice = self.load_user_setting(user_id, voice_id, 'voice') or "SEKAI"
        emotion = self.load_user_setting(user_id, voice_id, 'emotion') or "neutral"
        text = message.content

        # テキストをカナ変換
        kana_text = alkana.get_kana(text) or text

        # デバッグメッセージを追加
        logging.debug(f"Original text: {text}")
        logging.debug(f"Kana text: {kana_text}")

        payload = {
            'text': kana_text,
            'narrator': voice,
            'temperature': 0  # 必要に応じて変更
        }

        # ペイロードをログに出力
        logging.debug(f"Sending payload: {payload}")

        timeout = None  # タイムアウトを無効に設定
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            try:
                response = await client.post(
                    'http://localhost:5050/generate_speech/',
                    json=payload
                )

                if response.status_code == 200:
                    response_data = response.json()
                    download_url = response_data.get('output_file')
                    
                    if not download_url.startswith(('http://', 'https://')):
                        # ローカルパスの場合、ホスト名とプロトコルを追加
                        download_url = f"http://localhost:5050{download_url}"
                        logging.debug(f"Modified download URL: {download_url}")
                    
                    logging.debug(f"Download URL: {download_url}")
                    
                    dl_response = await client.get(download_url)
                    if dl_response.status_code == 200:
                        fd, tmp_path = tempfile.mkstemp()
                        with os.fdopen(fd, 'wb') as tmp:
                            tmp.write(dl_response.content)
                        logging.debug(f"Downloaded file path: {tmp_path}")

                        if os.path.exists(tmp_path):
                            await self.queue.put(tmp_path)
                            if not self.currently_playing:
                                await self.play_next_in_queue()
                        else:
                            logging.error(f"File not found: {tmp_path}")
                            await message.channel.send("ダウンロードしたファイルが見つかりまんでした。")
                    else:
                        logging.error(f"Failed to download file: {dl_response.status_code}")
                        await message.channel.send("ファイルのダウンロードに失敗しました。")
                else:
                    logging.error(f"Failed to synthesize: {response.status_code}")
                    await message.channel.send(f"音声合成に失敗しました: {response.status_code}")
            except httpx.ReadTimeout:
                logging.error("Request timed out")
                await message.channel.send("リクエストがタイムアウトしました。")
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                await message.channel.send("エラーが発生しました。")

    def reset_playing_state(self):
        self.currently_playing = False
        logging.info("Reset playing state.")

    @commands.hybrid_command()
    async def join(self, ctx):
        await self.join_vc(ctx)

    @commands.hybrid_command()
    async def leave(self, ctx):
        await self.leave_vc(ctx)

    @commands.hybrid_command()
    async def skip(self, ctx):
        if self.voice_channel and self.voice_channel.is_playing():
            self.voice_channel.stop()
            self.reset_playing_state()
            await ctx.send("現在の読み上げをスキップしました。")
            logging.info("Skipped current playback.")
            await self.play_next_in_queue()  # 次のキューを再生
        else:
            await ctx.send("現在再生中の音声はありません。")
            logging.warning("Attempted to skip playback when nothing is playing.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.author.voice and message.author.voice.channel:
            if not self.voice_channel or not self.voice_channel.is_connected():
                self.voice_channel = await message.author.voice.channel.connect()
            
            if message.attachments:
                for attachment in message.attachments:
                    modified_message = message
                    modified_message.content = "添付ファイル"
                    await self.queue.put(modified_message)

            elif any(url in message.content for url in ["http://", "https://"]):
                if "https://youtu.be" or "https://www.youtube.com" in message.content:
                    modified_message = message
                    modified_message.content = "YouTubeのURL"
                    await self.queue.put(modified_message)
                if "http://www.youtube.com" or "http://youtu.be" in message.content:
                    modified_message = message
                    modified_message.content = "YouTubeのURL"
                    await self.queue.put(modified_message)
                if "https://twitter.com" in message.content:
                    modified_message = message
                    modified_message.content = "TwitterのURL"
                    await self.queue.put(modified_message)
                if "https://www.pixiv.net" in message.content:
                    modified_message = message
                    modified_message.content = "PixivのURL"
                    await self.queue.put(modified_message)
                if "https://www.nicovideo.jp" in message.content:
                    modified_message = message
                    modified_message.content = "ニコニコ動画のURL"
                    await self.queue.put(modified_message)
                if "https://discord" in message.content:
                    modified_message = message
                    modified_message.content = "DiscordのURL"
                    await self.queue.put(modified_message)
                else:
                    modified_message = message
                    modified_message.content = "URL省略"
                    await self.queue.put(modified_message)
            else:
                await self.queue.put(message)
            
            if not self.currently_playing:
                await self.play_next_in_queue()
        else:
            await message.channel.send("ボイスチャンネルに接続している必要があります。")

async def setup(bot):
    await bot.add_cog(TTS(bot))
