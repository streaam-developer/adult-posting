import os
import re
import asyncio
import cloudscraper
import math
from telegram import Bot
from telegram.error import TimedOut, RetryAfter, NetworkError
from config import POST_URL

BOT_TOKEN = '7760514362:AAEukVlluWrzqOrsO4-i_dH7F73oXQEmRgw'
CHANNEL_ID = -1002706635277
post_url = POST_URL


async def upload_with_retry(bot, file_path, caption, retries=3):
    """Upload video with retry + Telegram message updates."""
    file_size = os.path.getsize(file_path)
    size_mb = file_size / (1024 * 1024)
    start_msg = await bot.send_message(
        chat_id=CHANNEL_ID,
        text=f"📤 **Starting upload...**\n"
             f"🎬 *{caption}*\n"
             f"📦 Size: `{size_mb:.2f} MB`"
    )

    for attempt in range(1, retries + 1):
        try:
            print(f"📤 Attempt {attempt}: Uploading video ({size_mb:.2f} MB)...")
            with open(file_path, 'rb') as f:
                await bot.send_video(
                    chat_id=CHANNEL_ID,
                    video=f,
                    caption=f"Video from {caption}",
                    read_timeout=1200,  # 20 minutes
                    write_timeout=1200,
                    connect_timeout=30,
                )
            await start_msg.edit_text(
                f"✅ **Upload complete!**\n"
                f"📦 Size: `{size_mb:.2f} MB`\n"
                f"🔁 Attempts: {attempt}"
            )
            return
        except RetryAfter as e:
            wait = math.ceil(e.retry_after) + 5
            print(f"⚠️ Rate limited — waiting {wait}s before retry...")
            await start_msg.edit_text(f"⏳ Rate limited, retrying in {wait}s...")
            await asyncio.sleep(wait)
        except (TimedOut, NetworkError) as e:
            print(f"⚠️ Network/timeout error: {e}. Retrying in 10s...")
            await start_msg.edit_text(
                f"⚠️ Network/timeout error (attempt {attempt}) — retrying..."
            )
            await asyncio.sleep(10)
        except Exception as e:
            await start_msg.edit_text(f"❌ Upload failed: {e}")
            print(f"❌ Upload failed: {e}")
            break

    await start_msg.edit_text("❌ Upload failed after multiple attempts.")


async def main():
    try:
        print(f"Fetching page content from {post_url} using cloudscraper...")
        scraper = cloudscraper.create_scraper()
        response = scraper.get(post_url)
        response.raise_for_status()
        html_content = response.text

        match = re.search(r'(https?://vk[^\s"]+\.mp4)', html_content)
        if not match:
            print("Could not find video URL in the page source.")
            return

        video_url = match.group(1)
        print(f"Found video URL: {video_url}")

        print(f"Downloading video from {video_url} ...")

        # Send initial status message
        bot = Bot(token=BOT_TOKEN)
        async with bot:
            status_msg = await bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"⬇️ **Downloading video...**\n{post_url}"
            )

            with scraper.get(video_url, stream=True) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                downloaded = 0
                chunk_size = 8192
                with open("temp_video.mp4", "wb") as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total > 0:
                                progress = (downloaded / total) * 100
                                await status_msg.edit_text(
                                    f"⬇️ **Downloading...** {progress:.1f}%\n"
                                    f"📥 Size: {downloaded / (1024 * 1024):.2f} MB"
                                )

            await status_msg.edit_text("✅ **Download complete!** Uploading...")

            # Upload
            await upload_with_retry(bot, "temp_video.mp4", post_url)

        if os.path.exists("temp_video.mp4"):
            os.remove("temp_video.mp4")

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
