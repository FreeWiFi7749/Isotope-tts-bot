import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Select, Modal
from discord import SelectOption
import pytz
from datetime import datetime
import os
from dotenv import load_dotenv

dotenv_path = '/Users/freewifi/yo-chan_bot/.env'
load_dotenv(dotenv_path)

help_channel_id_env = os.getenv("HELP_CHANNEL_ID", "0")
help_command_id_env = os.getenv("HELP_COMMAND_ID", "0")

jst = pytz.timezone('Asia/Tokyo')
now = datetime.now(jst)

class HelpView(View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpSelect())
        self.add_item(HelpButton())

class HelpReplyView(View):
    def __init__(self, user: discord.User, help_embed: discord.Message):
        super().__init__()
        self.add_item(HelpReplyButton(user, help_embed))

class HelpReplyEditView(View):
    def __init__(self, user: discord.User, help_embed: discord.Message, reply_msg: discord.Message):
        super().__init__()
        self.add_item(HelpReplyEditButton(user, help_embed, reply_msg))
        
class HelpModal(Modal):
    def __init__(self):
        self.help_channel_id = help_channel_id_env
        try:
            self.help_channel_id = int(help_channel_id_env)
        except ValueError:
            self.help_channel_id = 1244178951056658476

        super().__init__(title="質問を入力してください.")
        self.add_item(discord.ui.TextInput(label="コマンド名", placeholder="募集コマンド", style=discord.TextStyle.short))
        self.add_item(discord.ui.TextInput(label="質問内容", placeholder="〇〇がわからない。", style=discord.TextStyle.long))

    async def on_submit(self, interaction: discord.Interaction):
        command_name = self.children[0].value
        question_content = self.children[1].value

        await interaction.response.send_message("質問を送信しました！", ephemeral=True)
        channel = interaction.client.get_channel(self.help_channel_id)
        if channel is None:
            return
        e = discord.Embed(title="質問", description=f"{command_name}\n{question_content}", color=discord.Color.blurple())
        e.set_footer(text=f"{interaction.user}", icon_url=interaction.user.avatar.url)
        help_embed = await channel.send(embed=e)
        await help_embed.edit(view=HelpReplyView(interaction.user, help_embed))

class HelpReplyModal(Modal):
    def __init__(self, user: discord.User, help_embed: discord.Message):
        self.help_channel_id = help_channel_id_env
        self.help_embed = help_embed
        try:
            self.help_channel_id = int(help_channel_id_env)
        except ValueError:
            self.help_channel_id = 1244178951056658476

        super().__init__(title="質問に返信してください。")
        self.add_item(discord.ui.TextInput(label="返信内容", placeholder="〇〇です。", style=discord.TextStyle.long))
        self.user = user

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("質問に返信しました！", ephemeral=True)
        user = self.user
        if user is None:
            return
        e = discord.Embed(title="質問に対しての回答", description="", color=discord.Color.blurple())
        e.add_field(name="質問内容", value=f"{interaction.message.embeds[0].description}", inline=False)
        e.add_field(name="返信内容", value=f"{self.children[0].value}", inline=False)
        e.set_footer(text=f"{interaction.user}", icon_url=interaction.user.avatar.url)
        reply_msg = await user.send(embed=e)
        await self.help_embed.delete()

        button = discord.ui.Button(label="返信を編集", style=discord.ButtonStyle.primary)
        async def button_callback(interaction: discord.Interaction):
            modal = HelpReplyEditModal(self.user, self.help_embed, reply_msg)
            await interaction.response.send_modal(modal)
        button.callback = button_callback
        view = discord.ui.View()
        view.add_item(button)
        await interaction.response.send_message("質問に返信しました！返信を編集するには以下のボタンをクリックしてください。", view=view)

class HelpReplyEditModal(Modal):
    def __init__(self, user: discord.User, help_embed: discord.Message, reply_msg: discord.Message):
        super().__init__(title="質問に返信してください。")
        self.user = user
        self.help_embed = help_embed
        self.reply_msg = reply_msg
        self.add_item(discord.ui.TextInput(label="返信内容", placeholder="〇〇です。", style=discord.TextStyle.long))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("質問に返信しました！", ephemeral=True)
        e = discord.Embed(title="質問に対しての回答", description="", color=discord.Color.blurple())
        e.add_field(name="質問内容", value=f"{interaction.message.embeds[0].description}", inline=False)
        e.add_field(name="返信内容", value=f"{self.children[0].value}", inline=False)
        e.set_footer(text=f"{interaction.user}", icon_url=interaction.user.avatar.url)
        reply_msg = await interaction.user.send(embed=e)
        await self.help_embed.edit(embed=self.help_embed.embeds[0].add_field(name="返信内容", value=f"{self.children[0].value}", inline=False), view=None)

        button = discord.ui.Button(label="返信を編集", style=discord.ButtonStyle.primary)
        async def button_callback(interaction: discord.Interaction):
            modal = HelpReplyEditModal(self.user, self.help_embed, reply_msg)
            await interaction.response.send_modal(modal)
        button.callback = button_callback
        view = discord.ui.View()
        view.add_item(button)
        await interaction.followup.send("返信を編集するには以下のボタンをクリックしてください。", view=view, ephemeral=True)

class HelpReplyButton(Button):
    def __init__(self, user: discord.User, help_embed: discord.Message):
        super().__init__(style=discord.ButtonStyle.primary, label="返信", emoji="📩")
        self.user = user
        self.help_embed = help_embed

    async def callback(self, interaction: discord.Interaction):
        modal = HelpReplyModal(self.user, self.help_embed)
        await interaction.response.send_modal(modal)

class HelpReplyEditButton(Button):
    def __init__(self, user: discord.User, help_embed: discord.Message, reply_msg: discord.Message):
        super().__init__(style=discord.ButtonStyle.primary, label="返信を編集", emoji="📩")
        self.user = user
        self.help_embed = help_embed
        self.reply_msg = reply_msg

    async def callback(self, interaction: discord.Interaction):
        modal = HelpReplyEditModal(self.user, self.help_embed, self.reply_msg)
        await interaction.response.send_modal(modal)

class HelpSelect(Select):
    def __init__(self):
        self.help_command_id = help_command_id_env
        try:
            self.help_command_id = int(help_command_id_env)
        except ValueError:
            self.help_command_id = 1244175490571436125

        options = [
            SelectOption(label="Home", value="home", emoji="🏠"),
            SelectOption(label="読み上げ", value="tts", emoji="🔊"),
            SelectOption(label="設定", value="settings", emoji="⚙️"),
            SelectOption(label="about", value="about", emoji="ℹ️")
        ]
        super().__init__(placeholder="詳しいヘルプを表示します。", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]
        if interaction.guild:
            member = interaction.guild.get_member(interaction.user.id)
            if member:
                color = member.color
            else:
                color = discord.Color.blurple()
        else:
            color = discord.Color.blurple()

        if selected_value == "home":
            e = discord.Embed(title='ヘルプ', colour=color, timestamp=now)
            e.add_field(name='読み上げコマンド', value='</join:1244780272872984636>\n</leave:1244780272872984637>\n</skip:1244780272872984638>', inline=False)
            e.add_field(name='設定コマンド', value='</user setting voice:1243077141332230226>\n</user setting speed:1243077141332230226>\n</user setting pitch:1243077141332230226>', inline=False)
            e.add_field(name='Aboutコマンド', value='</about bot:1243804233627729950>\n</about api:1243804233627729950>\n</about voices:1243804233627729950>', inline=False)
            e.set_footer(text="ヘルプメニュー")
            e.set_thumbnail(url=interaction.client.user.avatar.url)
            e.set_author(name=f"{interaction.client.user.name}のヘルプ", icon_url=interaction.client.user.avatar.url)

        elif selected_value == "tts":
            e = discord.Embed(title='読み上げコマンド', colour=color, timestamp=now)
            e.add_field(name='/join', value='ボイスチャンネルに接続します。\n> </join:1244780272872984636>を使ってみる', inline=False)
            e.add_field(name='/leave', value='ボイスチャンネルから切断します。\n> </leave:1244780272872984637>を使ってみる', inline=False)
            e.add_field(name='/skip', value='現在の読み上げをスキップします。\n> </skip:1244780272872984638>を使ってみる', inline=False)
            e.set_footer(text="読み上げコマンドの説明")
            e.set_thumbnail(url=interaction.client.user.avatar.url)
            e.set_author(name=f"{interaction.client.user.name}のヘルプ", icon_url=interaction.client.user.avatar.url)

        elif selected_value == "settings":
            e = discord.Embed(title='設定コマンド', colour=color, timestamp=now)
            e.add_field(name='/user setting voice', value='音声を設定します。\n> </user setting voice:1243077141332230226>を使ってみる', inline=False)
            e.add_field(name='/user setting speed', value='音声の速度を設定します。\n> </user setting speed:1243077141332230226>を使ってみる', inline=False)
            e.add_field(name='/user setting pitch', value='音声のピッチを設定します。\n> </user setting pitch:1243077141332230226>を使ってみる', inline=False)
            e.set_footer(text="設定コマンドの説明")
            e.set_thumbnail(url=interaction.client.user.avatar.url)
            e.set_author(name=f"{interaction.client.user.name}のヘルプ", icon_url=interaction.client.user.avatar.url)

        elif selected_value == "about":
            e = discord.Embed(title='Aboutコマンド', colour=color, timestamp=now)
            e.add_field(name='/about bot', value='BOTの情報を表示します。\n> </about bot:1243804233627729950>を使ってみる', inline=False)
            e.add_field(name='/about api', value='APIの情報を表示します。\n> </about api:1243804233627729950>を使ってみる', inline=False)
            e.add_field(name='/about voices', value='音声の一覧を表示します。\n> </about voices:1243804233627729950>を使ってみる', inline=False)
            e.set_footer(text="Aboutコマンドの説明")
            e.set_thumbnail(url=interaction.client.user.avatar.url)
            e.set_author(name=f"{interaction.client.user.name}のヘルプ", icon_url=interaction.client.user.avatar.url)

        else:
            e = discord.Embed(title="エラー", description="不明なカテゴリが選択されました。", color=discord.Color.red())

        await interaction.response.edit_message(embed=e, view=HelpView())

class HelpButton(Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="直接質問", emoji="❓")

    async def callback(self, interaction: discord.Interaction):
        modal = HelpModal()
        await interaction.response.send_modal(modal)

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        help_command_id_env = os.getenv("HELP_COMMAND_ID", "0")
        try:
            self.help_command_id = int(help_command_id_env)
        except ValueError:
            self.help_command_id = 1244175490571436125

    @commands.command(name="help", description="ヘルプを表示します")
    async def help_s(self, ctx):
        await ctx.send("</help:1244175490571436125>をクリックしてヘルプを表示してください。")

    @app_commands.command(name="help", description="ヘルプを表示します")
    @app_commands.describe(option="ヘルプを表示するカテゴリ名")
    @app_commands.choices(option=[
        app_commands.Choice(name="Home", value="home"),
        app_commands.Choice(name="読み上げ", value="tts"),
        app_commands.Choice(name="設定", value="settings"),
        app_commands.Choice(name="about", value="about")
    ])
    async def help(self, interaction: discord.Interaction, option: app_commands.Choice[str] = None):
        if option is None:
            if interaction.guild:
                member = interaction.guild.get_member(interaction.user.id)
                if member:
                    color = member.color
                else:
                    color = discord.Color.blurple()
            else:
                color = discord.Color.blurple()
            e = discord.Embed(title='ヘルプ', colour=color, timestamp=now)
            e.add_field(name='読み上げコマンド', value='</join:1244780272872984636>\n</leave:1244780272872984637>\n</skip:1244780272872984638>', inline=False)
            e.add_field(name='設定コマンド', value='</user setting voice:1243077141332230226>\n</user setting speed:1243077141332230226>\n</user setting pitch:1243077141332230226>', inline=False)
            e.add_field(name='Aboutコマンド', value='</about bot:1243804233627729950>\n</about api:1243804233627729950>\n</about voices:1243804233627729950>', inline=False)
            e.set_footer(text="ヘルプメニュー")
            e.set_thumbnail(url=interaction.client.user.avatar.url)
            e.set_author(name=f"{interaction.client.user.name}のヘルプ", icon_url=interaction.client.user.avatar.url)

            await interaction.response.send_message(embed=e, view=HelpView(), ephemeral=True)

        else:
            selected_value = option.value
            if interaction.guild:
                member = interaction.guild.get_member(interaction.user.id)
                if member:
                    color = member.color
                else:
                    color = discord.Color.blurple()
            else:
                color = discord.Color.blurple()

            if selected_value == "home":
                e = discord.Embed(title='ヘルプ', colour=color, timestamp=now)
                e.add_field(name='読み上げコマンド', value='/join, /leave, /skip', inline=False)
                e.add_field(name='設定コマンド', value='/user setting voice, /user setting speed, /user setting pitch', inline=False)
                e.add_field(name='Aboutコマンド', value='/about bot, /about api, /about voices', inline=False)
                e.set_footer(text="ヘルプメニュー")
                e.set_thumbnail(url=interaction.client.user.avatar.url)
                e.set_author(name=f"{interaction.client.user.name}のヘルプ", icon_url=interaction.client.user.avatar.url)

            elif selected_value == "tts":
                e = discord.Embed(title='読み上げコマンド', colour=color, timestamp=now)
                e.add_field(name='/join', value='ボイスチャンネルに接続します。\n> </join:1244780272872984636>を使ってみる', inline=False)
                e.add_field(name='/leave', value='ボイスチャンネルから切断します。\n> </leave:1244780272872984637>を使ってみる', inline=False)
                e.add_field(name='/skip', value='現在の読み上げをスキップします。\n> </skip:1244780272872984638>を使ってみる', inline=False)
                e.set_footer(text="読み上げコマンドの説明")
                e.set_thumbnail(url=interaction.client.user.avatar.url)
                e.set_author(name=f"{interaction.client.user.name}のヘルプ", icon_url=interaction.client.user.avatar.url)

            elif selected_value == "settings":
                e = discord.Embed(title='設定コマンド', colour=color, timestamp=now)
                e.add_field(name='/user setting voice', value='音声を設定します。\n> </user setting voice:1243077141332230226>を使ってみる', inline=False)
                e.add_field(name='/user setting speed', value='音声の速度を設定します。\n> </user setting speed:1243077141332230226>を使ってみる', inline=False)
                e.add_field(name='/user setting pitch', value='音声のピッチを設定します。\n> </user setting pitch:1243077141332230226>を使ってみる', inline=False)
                e.set_footer(text="設定コマンドの説明")
                e.set_thumbnail(url=interaction.client.user.avatar.url)
                e.set_author(name=f"{interaction.client.user.name}のヘルプ", icon_url=interaction.client.user.avatar.url)

            elif selected_value == "about":
                e = discord.Embed(title='Aboutコマンド', colour=color, timestamp=now)
                e.add_field(name='/about bot', value='BOTの情報を表示します。\n> </about bot:1243804233627729950>を使ってみる', inline=False)
                e.add_field(name='/about api', value='APIの情報を表示します。\n> </about api:1243804233627729950>を使ってみる', inline=False)
                e.add_field(name='/about voices', value='音声の一覧を表示します。\n> </about voices:1243804233627729950>を使ってみる', inline=False)
                e.set_footer(text="Aboutコマンドの説明")
                e.set_thumbnail(url=interaction.client.user.avatar.url)
                e.set_author(name=f"{interaction.client.user.name}のヘルプ", icon_url=interaction.client.user.avatar.url)

            await interaction.response.send_message(embed=e, view=HelpView(), ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))