import discord
import uuid
import pytz
import asyncio
import logging
from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

error_log_channel_id = "1244549278396055552"
bug_report_channel_id = "1244549321433682012"
main_guild_id = "855766741145616394"

logger = logging.getLogger('discord_bot')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

class BugReportModal(discord.ui.Modal, title="バグ報告"):
    reason = discord.ui.TextInput(
        label="バグの詳細",
        style=discord.TextStyle.paragraph,
        placeholder="ここにバグの詳細を記載してください...",
        required=True,
        max_length=1024
    )
    image = discord.ui.TextInput(
        label="参考画像",
        style=discord.TextStyle.paragraph,
        placeholder="[必須ではありません]画像のURLを貼り付けてください...",
        required=False,
        max_length=1024
    )

    def __init__(self, bot, error_id, channel_id, server_id, command_name, server_name):
        super().__init__()
        self.bot = bot
        self.error_id = error_id
        self.channel_id = channel_id
        self.server_id = server_id
        self.command_name = command_name
        self.server_name = server_name

    async def on_submit(self, interaction: discord.Interaction):
        logger.debug(f"Submitting bug report: error_id={self.error_id}, user={interaction.user}, channel_id={self.channel_id}, server_id={self.server_id}")
        dev_channel = self.bot.get_channel(bug_report_channel_id)
        if dev_channel:
            user_mention = interaction.user.mention
            channel_mention = f"<#{self.channel_id}>"

            embed = discord.Embed(title="エラーログ", description=f"エラーID: {self.error_id}", color=discord.Color.red())
            embed.add_field(name="ユーザー", value=user_mention, inline=False)
            embed.add_field(name="チャンネル", value=channel_mention, inline=False)
            embed.add_field(name="サーバー", value=self.server_name, inline=False)
            embed.add_field(name="コマンド", value=f"/{self.command_name}", inline=False)
            embed.add_field(name="エラーメッセージ", value=self.reason.value, inline=False)
            if self.image.value:
                embed.set_image(url=self.image.value)
            await dev_channel.send(embed=embed)
            
            await interaction.response.send_message("バグを報告しました。ありがとうございます！", ephemeral=True)
        else:
            logger.error("Bug report channel not found.")
            e = discord.Embed(title="エラー", description="> 予期せぬエラーです\n\n<@707320830387814531>にDMを送信するか、[サポートサーバー](https://hfspro.co/asb-discord)にてお問い合わせください", color=discord.Color.red())
            await interaction.response.send_message(embed=e)


class BugReportView(discord.ui.View):
    def __init__(self, bot, error_id, channel_id, server_id, command_name, server_name):
        super().__init__()
        self.bot = bot
        self.error_id = error_id
        self.channel_id = channel_id
        self.server_id = server_id
        self.command_name = command_name
        self.server_name = server_name

    async def disable_button(self, interaction):
        await asyncio.sleep(120)
        for item in self.children:
            if item.custom_id == "my_button":
                item.disabled = True
        await interaction.edit_original_response(view=self)

    @discord.ui.button(label="バグを報告する", style=discord.ButtonStyle.red, custom_id="report_bug_button", emoji="<:bug_hunter:1226787664020242482>")
    async def report_bug_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.debug(f"Bug report button clicked: error_id={self.error_id}, user={interaction.user}, channel_id={self.channel_id}, server_id={self.server_id}")
        modal = BugReportModal(self.bot, self.error_id, self.channel_id, self.server_id, self.command_name, self.server_name)
        await interaction.response.send_modal(modal)
        asyncio.create_task(self.disable_button(interaction))

async def handle_command_error(ctx, error):
    logger.error(f"Handling command error: {error}")
    if hasattr(ctx, 'handled') and ctx.handled:
        return

    if isinstance(error, commands.CommandNotFound):
        await ctx.send("そのコマンドは存在しません。", delete_after=5)
        ctx.handled = True
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("引数が不足しています。", delete_after=5)
        ctx.handled = True
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send("引数が不正です。", delete_after=5)
        ctx.handled = True
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("あなたはのコマンドを実行する権限がありません。", delete_after=5)
        ctx.handled = True
        return
    if isinstance(error, commands.BotMissingPermissions):
        await ctx.send("BOTがこのコマンドを実行する権限がありません。", delete_after=5)
        ctx.handled = True
        return
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"このコマンドは{error.retry_after:.2f}秒後に再実行できます。", delete_after=error.retry_after)
        ctx.handled = True
        return
    
    if not hasattr(ctx, 'handled') or not ctx.handled:
        error_id = uuid.uuid4()

        channel_id = ctx.channel.id
        server_id = ctx.guild.id if ctx.guild else 'DM'
        server_name = ctx.guild.name if ctx.guild else 'DM'
        channel_mention = f"<#{channel_id}>"
        now = datetime.now(pytz.timezone('Asia/Tokyo'))

        e = discord.Embed(
            title="エラー通知",
            description=(
                "> <:error:1226790218552836167>コマンド実行中にエラーが発生しました。\n"
                f"**エラーID**: `{error_id}`\n"
                f"**コマンド**: {ctx.command.qualified_name if ctx.command else 'N/A'}\n"
                f"**ユーザー**: {ctx.author.mention}\n"
                f"**エラーメッセージ**: {error}\n"
            ),
            color=discord.Color.red(),
            timestamp=now
        )
        e.set_footer(text=f"サーバー: {server_name}")
        
        guild = ctx.bot.get_guild(main_guild_id)
        if guild is None:
            if not hasattr(ctx.bot, 'main_guild_not_found_logged'):
                logger.error(f"Main guild with ID {main_guild_id} not found.")
                ctx.bot.main_guild_not_found_logged = True
            return
        else:
            logger.info(f"Main guild found: {guild.name}")

        error_log_channel = guild.get_channel(error_log_channel_id)
        if error_log_channel is None:
            if not hasattr(ctx.bot, 'error_log_channel_not_found_logged'):
                logger.error(f"Error log channel with ID {error_log_channel_id} not found in guild {guild.name}.")
                ctx.bot.error_log_channel_not_found_logged = True
            return
        else:
            logger.info(f"Error log channel found: {error_log_channel.name}")
            await error_log_channel.send(embed=e)

        view = BugReportView(ctx.bot, str(error_id), str(channel_id), str(server_id), ctx.command.qualified_name if ctx.command else "N/A", server_name)
        if hasattr(ctx, 'interaction') and ctx.interaction:
            ed = discord.Embed(
                title="エラーが発生しました",
                description=(
                    "> <:error:1226790218552836167>コマンド実行中にエラーが発生しました。\n"
                    f"エラーID: `{error_id}`\n"
                    f"チャンネル: {channel_mention}\n"
                    f"サーバー: `{server_name}`\n\n"
                    "__下のボタンを押してバグを報告してください。__\n参考となるスクリーンショットがある場合は**__事前に画像URL__**を準備してください。"
                ),
                color=discord.Color.red(),
                timestamp=now
            )
            ed.set_footer(text="バグ報告に貢献してくれた方にはサポート鯖で特別なロールを付与します。")
            view = BugReportView(ctx.bot, str(error_id), str(channel_id), str(server_id), ctx.interaction.command.qualified_name if ctx.interaction.command else "N/A", server_name)

            await ctx.interaction.response.send_message(embed=ed, view=view, ephemeral=True)
        else:
            ed = discord.Embed(
                title="エラーが発生しました",
                description=(
                    "> <:error:1226790218552836167>コマンド実行中にエラーが発生しました。\n"
                    f"エラーID: `{error_id}`\n"
                    f"チャンネル: {channel_mention}\n"
                    f"サーバー: `{server_name}`\n\n"
                    "__下のボタンを押してバグを報告してください。__\n参考となるスクリーンショットがある場合は**__事前に画像URL__**を準備してください。"
                ),
                color=discord.Color.red()
            )
            ed.set_footer(text="バグ報告に貢献してくれた方にはサポート鯖で特別なロールを付与します。")

            await ctx.author.send(embed=ed, view=view)

async def handle_application_command_error(bot, interaction: discord.Interaction, error):
    logger.error(f"Handling application command error: {error}")
    if hasattr(interaction, 'handled') and interaction.handled:
        return

    if isinstance(error, commands.CommandNotFound):
        await interaction.response.send_message("そのコマンドは存在しません。", ephemeral=True)
        interaction.handled = True
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await interaction.response.send_message("引数が不足しています。", ephemeral=True)
        interaction.handled = True
        return
    if isinstance(error, commands.BadArgument):
        await interaction.response.send_message("引数が不正です。", ephemeral=True)
        interaction.handled = True
        return
    if isinstance(error, commands.MissingPermissions):
        await interaction.response.send_message("あなたはのコマンドを実行する権限がありません。", ephemeral=True)
        interaction.handled = True
        return
    if isinstance(error, commands.BotMissingPermissions):
        await interaction.response.send_message("BOTがこのコマンドを実行する権限がありません。", ephemeral=True)
        interaction.handled = True
        return
    if isinstance(error, commands.CommandOnCooldown):
        await interaction.response.send_message(f"このコマンドは{error.retry_after:.2f}秒後に再実行できます。", ephemeral=True)
        interaction.handled = True
        return

    if not interaction.handled:
        error_id = uuid.uuid4()
        logger.error(error)

        channel_id = interaction.channel_id
        server_id = interaction.guild_id if interaction.guild else 'DM'
        server_name = interaction.guild.name if interaction.guild else 'DM'
        command_name = interaction.command.qualified_name if interaction.command else "N/A"
        channel_mention = f"<#{channel_id}>"
        now = datetime.now(pytz.timezone('Asia/Tokyo'))

        e = discord.Embed(
            title="エラー通知",
            description=(
                "> <:error:1226790218552836167>コマンド実行中にエラーが発生しました。\n"
                f"**エラーID**: `{error_id}`\n"
                f"**コマンド**: {interaction.command.qualified_name if interaction.command else 'N/A'}\n"
                f"**ユーザー**: {interaction.user.mention}\n"
                f"**エラーメッセージ**: {error}\n"
            ),
            color=discord.Color.red(),
            timestamp=now
        )
        e.set_footer(text=f"サーバー: {server_name}")
        main_guild = bot.get_guild(main_guild_id)
        if main_guild is None:
            if not hasattr(bot, 'main_guild_not_found_logged'):
                logger.error(f"Main guild with ID {main_guild_id} not found.")
                bot.main_guild_not_found_logged = True
            return
        else:
            logger.info(f"Main guild found: {main_guild.name}")

        error_log_channel = main_guild.get_channel(error_log_channel_id)
        if error_log_channel is None:
            if not hasattr(bot, 'error_log_channel_not_found_logged'):
                logger.error(f"Error log channel with ID {error_log_channel_id} not found in guild {main_guild.name}.")
                bot.error_log_channel_not_found_logged = True
            return
        else:
            logger.info(f"Error log channel found: {error_log_channel.name}")
            await error_log_channel.send(embed=e)

        es = discord.Embed(
            title="エラーが発生しました",
            description=(
                "> <:error:1226790218552836167>コマンド実行中にエラーが発生しました。\n"
                f"エラーID: `{error_id}`\n"
                f"チャンネル: {channel_mention}\n"
                f"サーバー: `{server_name}`\n\n"
                "__下のボタンを押してバグを報告してください。__\n参考となるスクリーンショットがある場合は**__事前に画像URL__**を準備してください。"
            ),
            color=discord.Color.red(),
            timestamp=now
        )
        es.set_footer(text="バグ報告に貢献してくれた方にはサポート鯖で特別なロールを付与します。")
        view = BugReportView(bot, str(error_id), str(channel_id), str(server_id), interaction.command.qualified_name if interaction.command else "N/A", server_name)

        try:
            await interaction.response.send_message(embed=es, view=view, ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send(embed=es, view=view, ephemeral=True)
