from discord.ext import commands, tasks
from pypresence import Presence
import os
import json
import logging
import asyncio
from cogs.tts.user_setting import TTSUserSettingsCog
import pytz
from datetime import datetime

class RichPresence(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_rpc = {}
        self.presence_update_task.start()
        self.asset_dir = 'resource/image/rp'
        self.default_images = {
            'large_image': 'k-aiwa.png',
            'small_image': 'sekai.png'
        }
        self.owner_id = 707320830387814531
        logging.info("RichPresence cog initialized.")

    def load_config(self, user_id):
        config_path = f'data/tts/rp/{user_id}/config.json'
        if os.path.isfile(config_path):
            with open(config_path, 'r') as f:
                # logging.info(f"Loading config for user {user_id} from {config_path}.")
                return json.load(f)
        else:
            # logging.warning(f"No config found for user {user_id}. Using default config.")
            return {'client_id': None, 'enabled': False}

    def save_config(self, user_id, config):
        config_path = f'data/tts/rp/{user_id}/config.json'
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f)
        #logging.info(f"Config for user {user_id} saved to {config_path}.")

    def load_rp(self, user_id):
        rp_path = f'data/tts/rp/{user_id}/rp.json'
        if os.path.isfile(rp_path):
            with open(rp_path, 'r') as f:
                # logging.info(f"Loading Rich Presence data for user {user_id} from {rp_path}.")
                return json.load(f)
        else:
            # logging.warning(f"No Rich Presence data found for user {user_id}. Using default data.")
            return {}

    def save_rp(self, user_id, rp_data):
        rp_path = f'data/tts/rp/{user_id}/rp.json'
        os.makedirs(os.path.dirname(rp_path), exist_ok=True)
        with open(rp_path, 'w') as f:
            # json.dump(rp_data, f)
            json.dump(rp_data, f, indent=4)
        # logging.info(f"Rich Presence data for user {user_id} saved to {rp_path}.")

    def get_image_key(self, image_name):
        image_path = os.path.join(self.asset_dir, image_name)
        if os.path.isfile(image_path):
            # logging.info(f"Image {image_path} found.")
            return image_path
        else:
            # logging.warning(f"Image {image_path} not found. Using default.")
            return os.path.join(self.asset_dir, self.default_images['small_image'])

    async def connect_rpc(self, user_id, client_id, retries=3):
        if user_id not in self.user_rpc:
            rpc = Presence(client_id)
            for attempt in range(retries):
                try:
                    await self.bot.loop.run_in_executor(None, rpc.connect)
                    self.user_rpc[user_id] = rpc
                    # logging.info(f"Connected to Rich Presence for user {user_id} with client ID {client_id}.")
                    return self.user_rpc[user_id]
                except ConnectionRefusedError as e:
                    # logging.error(f"Connection to Rich Presence for user {user_id} with client ID {client_id} was refused. Attempt {attempt + 1} of {retries}. Error: {e}")
                    if attempt < retries - 1:
                        await asyncio.sleep(2)  # 再試行前に少し待つ
                    else:
                        # logging.error(f"Failed to connect to Rich Presence for user {user_id} after {retries} attempts.")
                        return None
                except Exception as e:
                    # logging.error(f"Unexpected error occurred while connecting to Rich Presence for user {user_id}: {e}")
                    return None
        return self.user_rpc[user_id]

    async def update_presence(self, user_id, small_image_key=None, vc_member_count=None):
        if user_id != self.owner_id:
            # logging.info(f"Rich Presence update ignored for user {user_id}. Only owner is allowed.")
            return

        config = self.load_config(user_id)
        if not config.get('enabled'):
            # logging.info(f"Rich Presence for user {user_id} is disabled.")
            return

        client_id = config.get('client_id')
        if not client_id:
            # logging.error(f"No client ID found for user {user_id}.")
            return

        rpc = await self.connect_rpc(user_id, client_id)
        if rpc is None:
            # logging.error(f"Failed to connect to Rich Presence for user {user_id}.")
            return
        
        user_voice = TTSUserSettingsCog.load_user_voice(self, user_id).lower()
        small_image_key = user_voice if user_voice else small_image_key
        if small_image_key == "RIME":
            small_image_key = 'rime'
            small_image_path = '/Users/freewifi/Isotope-tts-bot/resource/image/rp/rime.png'
        elif small_image_key == "SEKAI":
            small_image_key = 'sekai'
            small_image_path = '/Users/freewifi/Isotope-tts-bot/resource/image/rp/sekai.png'
        elif small_image_key == "COKO":
            small_image_key = 'coko'
            small_image_path = '/Users/freewifi/Isotope-tts-bot/resource/image/rp/coko.png'
        elif small_image_key == "HARU":
            small_image_key = 'haru'
            small_image_path = '/Users/freewifi/Isotope-tts-bot/resource/image/rp/haru.png'

        details = f"Using {small_image_key}'s voice" if small_image_key else "Using voice"
        if vc_member_count is not None:
            details += f" | VC Members: {vc_member_count}"

        small_image_path = self.get_image_key(f"{small_image_key}.png") if small_image_key else self.get_image_key(self.default_images['small_image'])

        now = datetime.now(pytz.timezone('Asia/Tokyo'))
        start_time = now.timestamp()
        await self.bot.loop.run_in_executor(None, lambda: rpc.update(
            state="可愛すぎる読み上げボット",
            details=details,
            large_image='k-aiwa',
            large_text="K+AIWA",
            small_image=small_image_key if small_image_key else 'sekai',
            small_text=f"Using {small_image_key}" if small_image_key else "Using voice",
            pid=os.getpid(),
            party_size=[vc_member_count if vc_member_count is not None else 1, 99],
            start=start_time
        ))
        
        rp_data = {
            'state': "可愛すぎる読み上げボット",
            'details': details,
            'large_image': 'k-aiwa',
            'small_image': small_image_key or 'sekai',
            'party_id': f'{user_id}',
            'party_size': [vc_member_count if vc_member_count is not None else 1, 99],
        }
        self.save_rp(user_id, rp_data)
        # logging.info(f"Rich Presence updated for user {user_id}!")

    @commands.hybrid_group()
    async def rp(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid RP command passed...')
            # logging.warning("Invalid RP command passed.")

    @rp.command()
    async def set_client_id(self, ctx, client_id: str):
        user_id = ctx.author.id
        if user_id != self.owner_id:
            await ctx.send("You are not authorized to set the client ID.")
            return
        config = self.load_config(user_id)
        config['client_id'] = client_id
        config['enabled'] = True
        self.save_config(user_id, config)
        await ctx.send(f"Client ID set and Rich Presence enabled for user {user_id}!")
        # logging.info(f"Client ID set and Rich Presence enabled for user {user_id}.")

    @rp.command()
    async def set_presence(self, ctx, small_image_key: str = None):
        await self.update_presence(ctx.author.id, small_image_key)
        await ctx.send(f"Rich Presence updated for user {ctx.author.id}!")
        # logging.info(f"Rich Presence updated for user {ctx.author.id}.")

    @tasks.loop(minutes=1)
    async def presence_update_task(self):
        for user_id in self.user_rpc.keys():
            config = self.load_config(user_id)
            if not config.get('enabled'):
                continue

            guild = self.bot.get_guild(self.bot.guilds[0].id)
            # logging.info(f"Guild: {guild}")
            member = guild.get_member(user_id)
            # logging.info(f"Member: {member}")
            if member and member.voice and member.voice.channel:
                vc_member_count = len(member.voice.channel.members)
                # logging.info(f"VC Member Count: {vc_member_count}")
            else:
                vc_member_count = None

            small_image_key = self.default_images['small_image']
            # logging.info(f"Small Image Key: {small_image_key}")
            await self.update_presence(user_id, small_image_key, vc_member_count)
            # logging.info(f"Presence updated for user {user_id}.")

    @presence_update_task.before_loop
    async def before_presence_update_task(self):
        await self.bot.wait_until_ready()
        # logging.info("Presence update task is starting.")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel != after.channel:
            user_id = member.id
            config = self.load_config(user_id)
            if not config.get('enabled'):
                return

            guild = member.guild
            if after.channel:
                vc_member_count = len(after.channel.members)
            else:
                vc_member_count = None

            small_image_key = self.default_images['small_image']
            await self.update_presence(user_id, small_image_key, vc_member_count)
            # logging.info(f"Presence updated for user {user_id} due to voice state change.")

async def setup(bot):
    await bot.add_cog(RichPresence(bot))
    # logging.info("RichPresence cog setup complete.")
