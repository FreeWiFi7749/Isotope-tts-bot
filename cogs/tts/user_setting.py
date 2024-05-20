import os
import json
import discord
from discord.ext import commands
from discord import app_commands

BASE_PATH = "data/tts/v00/user-data"
VOICE_DATA_PATH = "data/tts/v00/voice-data"

class UserSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_data = self.load_voice_data()

    def save_user_setting(self, user_id, voice_id, setting_name, value):
        if not os.path.exists(BASE_PATH):
            os.makedirs(BASE_PATH, exist_ok=True)
        user_path = os.path.join(BASE_PATH, str(user_id), str(voice_id))
        os.makedirs(user_path, exist_ok=True)
        setting_file = os.path.join(user_path, f"{setting_name}.json")
        
        with open(setting_file, 'w') as f:
            json.dump({setting_name: value}, f)
    
    def load_user_setting(self, user_id, voice_id, setting_name):
        setting_file = os.path.join(BASE_PATH, str(user_id), str(voice_id), f"{setting_name}.json")
        if os.path.exists(setting_file):
            with open(setting_file, 'r') as f:
                return json.load(f).get(setting_name)
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
            await ctx.send('Invalid user command passed...')

    @user.group()
    async def setting(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid setting command passed...')

    async def voice_autocomplete(self, interaction: discord.Interaction, current: str):
        voices = self.load_voice_data()
        return [app_commands.Choice(name=data['name'], value=vid) for vid, data in voices.items() if current.lower() in data['name'].lower()]

    @setting.command(name='speed')
    @app_commands.autocomplete(voice_id=voice_autocomplete)
    @app_commands.describe(voice_id="The voice to set the speed for", speed="The speed to set")
    async def set_speed(self, ctx, voice_id: str, speed: int):
        self.save_user_setting(ctx.author.id, voice_id, 'speed', speed)
        await ctx.send(f"Speed setting for voice {voice_id} set to {speed}")

    @setting.command(name='pitch')
    @app_commands.autocomplete(voice_id=voice_autocomplete)
    @app_commands.describe(voice_id="The voice to set the pitch for", pitch="The pitch to set")
    async def set_pitch(self, ctx, voice_id: str, pitch: int):
        self.save_user_setting(ctx.author.id, voice_id, 'pitch', pitch)
        await ctx.send(f"Pitch setting for voice {voice_id} set to {pitch}")

    @setting.command(name='emotion')
    @app_commands.autocomplete(voice_id=voice_autocomplete)
    @app_commands.describe(voice_id="The voice to set the emotion for", emotion="The emotion to set")
    async def set_emotion(self, ctx, voice_id: str, emotion: str):
        self.save_user_setting(ctx.author.id, voice_id, 'emotion', emotion)
        await ctx.send(f"Emotion setting for voice {voice_id} set to {emotion}")

    @setting.command(name='voice')
    @app_commands.autocomplete(voice_id=voice_autocomplete)
    @app_commands.describe(voice_id="The voice to set the voice for", voice="The voice to set")
    async def set_voice(self, ctx, voice_id: str, voice: str):
        self.save_user_setting(ctx.author.id, voice_id, 'voice', voice)
        await ctx.send(f"Voice setting for voice {voice_id} set to {voice}")

    @commands.command()
    async def voices(self, ctx):
        voice_list = [f"{vid}: {data['name']}" for vid, data in self.voice_data.items()]
        await ctx.send("\n".join(voice_list))


async def setup(bot):
    await bot.add_cog(UserSettings(bot))