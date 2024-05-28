import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import httpx
import logging
import os
import json
from utils.pagination import Paginator

load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

VOICE_DATA_PATH = "data/tts/v01/voice-data"
STATS_PATH = "data/tts/v00/stats"

class VoicePaginator(Paginator):
    def __init__(self, interaction):
        super().__init__(interaction, self.get_page)
        self.embeds = [
            discord.Embed(
                title="裏命(RIME)",
                description="彼女の声は、バーチャルシンガー**理芽(りめ)**をベースに制作されました。裏命は、ミステリアスで独特な雰囲気を持ち、彼女の声は優雅でありながらも力強い印象を与えます\n\n詳しくは、以下のリンクからご確認いただけます:\n• [音楽的同位体プロジェクト公式サイト](https://musical-isotope.kamitsubaki.jp/)\n• [裏命公式ページ](https://musical-isotope.kamitsubaki.jp/product/rimevoicepeak/)\n\n[音声を確認する](https://tts.k-aiwa.vip/api/v01/v_ex/?narrator=rime)\n\n音声の変更したい場合は</user setting voice:1243077141332230226>を使用してください。",
                color=discord.Color.from_rgb(255, 0, 0)).set_image(url="https://tts.k-aiwa.vip/img/embed/m-s-rime.webp").set_footer(text="image from KAMITUBAKI STUDIO\nページ1/4"),

            discord.Embed(
                title="星界(SEKAI)",
                description="彼女の声は、バーチャルシンガー**ヰ世界情緒(いせかいじょうちょ)**をベースに制作されました。星界は、独特な世界観とミステリアスな雰囲気を持ち、彼女の声は透明感がありながらも力強い印象を与えます\n\n詳しくは、以下のリンクからご確認いただけます:\n• [音楽的同位体プロジェクト公式サイト](https://musical-isotope.kamitsubaki.jp/)\n• [星界公式ページ](https://musical-isotope.kamitsubaki.jp/product/sekaivoicepeak/)\n\n[音声を確認する](https://tts.k-aiwa.vip/api/v01/v_ex/?narrator=sekai)\n\n音声の変更したい場合は</user setting voice:1243077141332230226>を使用してください。",
                color=discord.Color.from_rgb(128, 0, 128)).set_image(url="https://tts.k-aiwa.vip/img/embed/m-s-sekai.webp").set_footer(text="image from KAMITUBAKI STUDIO\nページ2/4"),

            discord.Embed(
                title="狐子(COKO)",
                description="彼女の声は、バーチャルシンガー**幸祜（ここ）**をベースに制作されました。狐子は、愛らしく活発な雰囲気を持ち、彼女の声は元気で明るい印象を与えます\n\n詳しくは、以下のリンクからご確認いただけます:\n• [音楽的同位体プロジェクト公式サイト](https://musical-isotope.kamitsubaki.jp/)\n• [狐子公式ページ](https://musical-isotope.kamitsubaki.jp/product/cokovoicepeak/)\n\n[音声を確認する](https://tts.k-aiwa.vip/api/v01/v_ex/?narrator=coko)\n\n音声の変更したい場合は</user setting voice:1243077141332230226>を使用してください。",
                color=discord.Color.from_rgb(0, 0, 255)).set_image(url="https://tts.k-aiwa.vip/img/embed/m-s-coko.webp").set_footer(text="image from KAMITUBAKI STUDIO\nページ3/4"),

            discord.Embed(
                title="羽累(HARU)",
                description="彼女の声は、バーチャルシンガー**春猿火（はるさるひ）**をベースに制作されました。羽累は、柔らかく親しみやすい雰囲気を持ち、彼女の声は明るく透き通った印象を与えます\n\n詳しくは、以下のリンクからご確認いただけます:\n• [音楽的同位体プロジェクト公式サイト](https://musical-isotope.kamitsubaki.jp/)\n• [羽累公式ページ](https://musical-isotope.kamitsubaki.jp/product/haruvoicepeak/)\n\n[音声を確認する](https://tts.k-aiwa.vip/api/v01/v_ex/?narrator=haru)\n\n音声の変更したい場合は</user setting voice:1243077141332230226>を使用してください。",
                color=discord.Color.from_rgb(0, 255, 0)).set_image(url="https://tts.k-aiwa.vip/img/embed/m-s-haru.webp").set_footer(text="image from KAMITUBAKI STUDIO\nページ4/4")
        ]

    async def get_page(self, index: int):
        if index < 0 or index >= len(self.embeds):
            raise IndexError("Index out of range")
        logging.info(self.embeds[index])
        return self.embeds[index], len(self.embeds)

class AboutCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.paginator = VoicePaginator(self.bot)

    def load_stats(self, filename):
        if not os.path.exists(STATS_PATH):
            os.makedirs(STATS_PATH, exist_ok=True)
        filepath = os.path.join(STATS_PATH, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return {"count": 0}
    
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

    @commands.hybrid_group(name="about")
    async def about(self, ctx: commands.Context):
        pass

    @about.command(name="bot", description="BOTの情報を表示します。")
    async def about_bot(self, ctx):
        vc_stats = self.load_stats("vc.json")
        message_stats = self.load_stats("message.json")
        error_stats = self.load_stats("error.json")
        eb = discord.Embed(
            title="K+AIWA",
            description="CeVIO AI 『音楽的同位体 星界(SEKAI)、裏命(RIME)、狐子(COKO)、羽累(HARU)』の音声波形を用いた読み上げBot「K+AIWA(カイワ)」です。\n現在利用可能な音声波形は以下の通りです：\n-	SEKAI\n-	COKO\n-	RIME\n-	HARU\n\n使用している音声波形：[音楽的同位体](https://musical-isotope.kamitsubaki.jp/)",
            color=discord.Color.from_rgb(255, 255, 255))
        eb.add_field(name="スタッツ", value=f"合計VC接続数: {vc_stats['count']}\n合計読み上げメッセージ数: {message_stats['count']}\n合計エラー数: {error_stats['count']}", inline=False)
        try:
            await ctx.send(embed=eb)
        except Exception as e:
            logging.error(e)

    @about.command(name="api", description="APIの情報を表示します。")
    async def about_api(self, ctx):
        API_URL = os.getenv('TTS_ISOTOPE_API_URL')
        about_api_url = API_URL + 'api/v01/api_info/'
        ping_api_url = API_URL + 'api/v01/ping/'

        f_m = await ctx.send("API情報を取得しています。しばらくお待ちください。")
        async with httpx.AsyncClient() as client:
            response = await client.get(about_api_url)
            api_info = response.json()
            logging.info(api_info)

        ea = discord.Embed(
            title="K+AIWA",
            description=f"**API Name:** {api_info['name']}\n**Version:** {api_info['version']}\n**Author:** {api_info['author']}\n**Description:** {api_info['description']}",
            color=discord.Color.from_rgb(100, 149, 237), url="https://tts.k-aiwa.vip/api/v01/about/")
        
        await f_m.edit(content="API情報を取得しました。API Pingを取得しています。しばらくお待ちください。")
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(ping_api_url)
            if response.status_code == 200:
                ea.add_field(name="API Ping", value=f"{round(response.elapsed.total_seconds() * 1000)}ms", inline=False)
            else:
                ea.add_field(name="API Ping", value=f"Failed to reach API: {response.status_code}", inline=False)
        
        await f_m.edit(content="", embed=ea)

    async def voice_autocomplete(self, interaction: discord.Interaction, current: str):
        voices = self.load_voice_data()
        return [app_commands.Choice(name=data['name'], value=vid) for vid, data in voices.items() if current.lower() in data['name'].lower()]


    @about.command(name="voices", aliases=['abv'], description="音声の一覧を表示します。")
    @app_commands.describe(voice="音声波形を選択します。")
    @app_commands.autocomplete(voice=voice_autocomplete)
    async def narration(self, ctx: commands.Context, voice: str = None):
        """利用可能な音声波形の紹介文を送信します"""
        if voice is None:
            try:
                paginator = VoicePaginator(ctx.interaction)
                await paginator.navigate()
            except Exception as e:
                await ctx.send("エラーが発生しました。もう一度お試しください。")
                logging.error("Error occurred: %s", e)
        else:
            embeds = {
                "RIME": discord.Embed(
                    title="裏命(RIME)",
                    description="彼女の声は、バーチャルシンガー**理芽(りめ)**をベースに制作されました。裏命は、ミステリアスで独特な雰囲気を持ち、彼女の声は優雅でありながらも力強い印象を与えます\n\n詳しくは、以下のリンクからご確認いただけます:\n• [音楽的同位体プロジェクト公式サイト](https://musical-isotope.kamitsubaki.jp/)\n• [裏命公式ページ](https://musical-isotope.kamitsubaki.jp/product/rimevoicepeak/)\n\n[音声を確認する](https://tts.k-aiwa.vip/api/v01/v_ex/?narrator=rime)\n\n音声の変更したい場合は</user setting voice:1243077141332230226>を使用してください。",
                    color=discord.Color.from_rgb(255, 0, 0)).set_image(url="https://tts.k-aiwa.vip/img/embed/m-s-rime.webp").set_footer(text="image from KAMITUBAKI STUDIO"),

                "SEKAI": discord.Embed(
                    title="星界(SEKAI)",
                    description="彼女の声は、バーチャルシンガー**ヰ世界情緒(いせかいじょうちょ)**をベースに制作されました。星界は、独特な世界観とミステリアスな雰囲気を持ち、彼女の声は透明感がありながらも力強い印象を与えます\n\n詳しくは、以下のリンクからご確認いただけます:\n• [音楽的同位体プロジェクト公式サイト](https://musical-isotope.kamitsubaki.jp/)\n• [星界公式ページ](https://musical-isotope.kamitsubaki.jp/product/sekaivoicepeak/)\n\n[音声を確認する](https://tts.k-aiwa.vip/api/v01/v_ex/?narrator=sekai)\n\n音声の変更したい場合は</user setting voice:1243077141332230226>を使用してください。",
                    color=discord.Color.from_rgb(128, 0, 128)).set_image(url="https://tts.k-aiwa.vip/img/embed/m-s-sekai.webp").set_footer(text="image from KAMITUBAKI STUDIO"),

                "COKO": discord.Embed(
                    title="狐子(COKO)",
                    description="彼女の声は、バーチャルシンガー**幸祜（ここ）**をベースに制作されました。狐子は、愛らしく活発な雰囲気を持ち、彼女の声は元気で明るい印象を与えます\n\n詳しくは、以下のリンクからご確認いただけます:\n• [音楽的同位体プロジェクト公式サイト](https://musical-isotope.kamitsubaki.jp/)\n• [狐子公式ページ](https://musical-isotope.kamitsubaki.jp/product/cokovoicepeak/)\n\n[音声を確認する](https://tts.k-aiwa.vip/api/v01/v_ex/?narrator=coko)\n\n音声の変更したい場合は</user setting voice:1243077141332230226>を使用してください。",
                    color=discord.Color.from_rgb(0, 0, 255)).set_image(url="https://tts.k-aiwa.vip/img/embed/m-s-coko.webp").set_footer(text="image from KAMITUBAKI STUDIO"),

                "HARU": discord.Embed(
                    title="羽累(HARU)",
                    description="彼女の声は、バーチャルシンガー**春猿火（はるさるひ）**をベースに制作されました。羽累は、柔らかく親しみやすい雰囲気を持ち、彼女の声は明るく透き通った印象を与えます\n\n詳しくは、以下のリンクからご確認いただけます:\n• [音楽的同位体プロジェクト公式サイト](https://musical-isotope.kamitsubaki.jp/)\n• [羽累公式ページ](https://musical-isotope.kamitsubaki.jp/product/haruvoicepeak/)\n\n[音声を確認する](https://tts.k-aiwa.vip/api/v01/v_ex/?narrator=haru)\n\n音声の変更したい場合は</user setting voice:1243077141332230226>を使用してください。",
                    color=discord.Color.from_rgb(0, 255, 0)).set_image(url="https://tts.k-aiwa.vip/img/embed/m-s-haru.webp").set_footer(text="image from KAMITUBAKI STUDIO")
            }

            embed = embeds.get(voice)
            if embed:
                await ctx.send(embed=embed)
            else:
                await ctx.send("エラーが発生しました。もう一度お試しください。")

async def setup(bot):
    await bot.add_cog(AboutCog(bot))
