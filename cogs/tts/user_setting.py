import os
import json
import discord
from discord.ext import commands
from discord import app_commands

from utils.error import handle_command_error, handle_application_command_error

BASE_PATH = "data/tts/v00/user-data"
VOICE_DATA_PATH = "data/tts/v01/voice-data"

class TTSUserSettingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_data = self.load_voice_data()
        self.bot.tree.on_error = handle_application_command_error

    def save_user_setting(self, user_id, voice_id, setting_name, value):
        if not os.path.exists(BASE_PATH):
            os.makedirs(BASE_PATH, exist_ok=True)
        user_path = os.path.join(BASE_PATH, str(user_id), str(voice_id))
        os.makedirs(user_path, exist_ok=True)
        setting_file = os.path.join(user_path, f"{setting_name}.json")
        
        with open(setting_file, 'w') as f:
            json.dump({setting_name: value}, f)

    def save_user_voice(self, user_id, voice):
        if not os.path.exists(BASE_PATH):
            os.makedirs(BASE_PATH, exist_ok=True)
        user_path = os.path.join(BASE_PATH, str(user_id))
        os.makedirs(user_path, exist_ok=True)
        setting_file = os.path.join(user_path, "voice.json")
        
        with open(setting_file, 'w') as f:
            json.dump({"voice": voice}, f)
    
    def load_user_setting(self, user_id, voice_id, setting_name):
        setting_file = os.path.join(BASE_PATH, str(user_id), str(voice_id), f"{setting_name}.json")
        if os.path.exists(setting_file):
            with open(setting_file, 'r') as f:
                return json.load(f).get(setting_name)
        return None
    
    def load_user_voice(self, user_id):
        setting_file = os.path.join(BASE_PATH, str(user_id), "voice.json")
        if os.path.exists(setting_file):
            with open(setting_file, 'r') as f:
                return json.load(f).get('voice')
        return None

    def load_voice_data(self):
        if not os.path.exists(VOICE_DATA_PATH):
            os.makedirs(VOICE_DATA_PATH, exist_ok=True)
        voice_files = [f for f in os.listdir(VOICE_DATA_PATH) if f.endswith('.json')]
        voices = {}
        for file in voice_files:
            with open(os.path.join(VOICE_DATA_PATH, file), 'r') as f:
                voice_data = json.load(f)
                voices[file.replace('.json', '')] = voice_data
        return voices

    @commands.hybrid_group()
    async def user(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('無効なユーザーコマンドが渡されました...')

    @user.group()
    async def setting(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('無効な設定コマンドが渡されました...')

    async def voice_autocomplete(self, interaction: discord.Interaction, current: str):
        voices = self.load_voice_data()
        return [app_commands.Choice(name=data['name'], value=vid) for vid, data in voices.items() if current.lower() in data['name'].lower()]

    @setting.command(name='speed')
    @app_commands.autocomplete(voice_id=voice_autocomplete)
    @app_commands.describe(voice_id="速度を設定する音声", speed="設定する速度")
    async def set_speed(self, ctx, voice_id: str, speed: int):
        self.save_user_setting(ctx.author.id, voice_id, 'speed', speed)
        await ctx.send(f"音声 {voice_id} の速度設定が {speed} に設定されました")

    @setting.command(name='pitch')
    @app_commands.autocomplete(voice_id=voice_autocomplete)
    @app_commands.describe(voice_id="ピッチを設定する音声", pitch="設定するピッチ")
    async def set_pitch(self, ctx, voice_id: str, pitch: int):
        self.save_user_setting(ctx.author.id, voice_id, 'pitch', pitch)
        await ctx.send(f"音声 {voice_id} のピッチ設定が {pitch} に設定されました")

    @setting.command(name='voice')
    @app_commands.autocomplete(voice=voice_autocomplete)
    @app_commands.describe(voice="設定する音声")
    async def set_voice(self, ctx, voice: str):
        self.save_user_voice(ctx.author.id, voice)
        await ctx.send(f"音声設定が {voice} に設定されました")

    @commands.hybrid_command(name="voices", aliases=['v'], description="音声の一覧を表示します。")
    async def voices(self, ctx):
        e = discord.Embed(title="利用可能な音声一覧")
        for vid, data in self.voice_data.items():
            e.add_field(name=data['name'], value=data['description'], inline=False)
        e.set_footer(text="音声を設定するには /user setting voice コマンドを使用してください。")
        e.set_author(name="Powered by VOICEPEAK")
        await ctx.send(embed=e)

    @voices.error
    async def voices_error(self, ctx, error):
        if ctx.command_failed:
            await handle_command_error(self.bot, ctx, error)
        else:
            await handle_application_command_error(self.bot, ctx, error)

    @set_speed.error
    async def set_speed_error(self, ctx, error):
        if ctx.command_failed:
            await handle_command_error(self.bot, ctx, error)
        else:
            await handle_application_command_error(self.bot, ctx, error)

    @set_pitch.error
    async def set_pitch_error(self, ctx, error):
        if ctx.command_failed:
            await handle_command_error(self.bot, ctx, error)
        else:
            await handle_application_command_error(self.bot, ctx, error)

    @set_voice.error
    async def set_voice_error(self, ctx, error):
        if ctx.command_failed:
            await handle_command_error(self.bot, ctx, error)
        else:
            await handle_application_command_error(self.bot, ctx, error)

async def setup(bot):
    await bot.add_cog(TTSUserSettingsCog(bot))