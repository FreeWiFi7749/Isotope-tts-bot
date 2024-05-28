import httpx
import tempfile
import os
import logging

async def process_message(api_url, payload, ctx, self, endpoint):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{api_url}{endpoint}", json=payload)
            if response.status_code == 200:
                response_data = response.json()
                audio_url = response_data.get('audio_url')
                if audio_url:
                    dl_response = await client.get(f"{api_url}{audio_url}")
                    if dl_response.status_code == 200:
                        fd, tmp_path = tempfile.mkstemp()
                        with os.fdopen(fd, 'wb') as tmp:
                            tmp.write(dl_response.content)
                        if os.path.exists(tmp_path):
                            guild_id = ctx.guild.id
                            self.queues[guild_id].append(tmp_path)
                            if not self.currently_playing[guild_id]:
                                await self.play_next_in_queue(guild_id)
                        else:
                            logging.error(f"File not found: {tmp_path}")
                            await ctx.send("ダウンロードしたファイルが見つかりませんでした。")
                    else:
                        logging.error(f"Failed to download file: {dl_response.status_code}")
                        await ctx.send("ファイルのダウンロードに失敗しました。")
                else:
                    logging.error("Audio URL is missing in the response.")
                    await ctx.send("レスポンスにAudio URLが含まれていません。")
            else:
                logging.error(f"Failed to synthesize: {response.status_code}")
                await ctx.send(f"音声合成に失敗しました: {response.status_code}")
        except httpx.RequestError as e:
            logging.error(f"An error occurred while requesting: {e}")
            await ctx.send("リクエスト中にエラーが発生しました。")
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            await ctx.send("エラーが発生しました。")

async def join_message(api_url, payload, ctx, self):
    await process_message(api_url, payload, ctx, self, "api/v01/startup/")

async def leave_message(api_url, payload, ctx, self):
    await process_message(api_url, payload, ctx, self, "api/v01/shutdown/")
