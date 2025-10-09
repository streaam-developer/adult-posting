import os
import re
import asyncio
import cloudscraper
from telegram import Bot
from config import POST_URL

BOT_TOKEN = '7760514362:AAEukVlluWrzqOrsO4-i_dH7F73oXQEmRgw'
CHANNEL_ID = -1002706635277
post_url = POST_URL


async def main():
    try:
        print(f"Fetching page content from {post_url} using cloudscraper...")
        scraper = cloudscraper.create_scraper()
        response = scraper.get(post_url)
        response.raise_for_status()
        html_content = response.text

        # Find .mp4 link
        match = re.search(r'(https?://vk[^\s"]+\.mp4)', html_content)
        if not match:
            print("Could not find video URL in the page source.")
            return

        video_url = match.group(1)
        print(f"Found video URL: {video_url}")

        # Download video
        print(f"Downloading video from {video_url} ...")
        with scraper.get(video_url, stream=True) as r:
            r.raise_for_status()
            with open('temp_video.mp4', 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print("Download complete. Uploading to Telegram...")

        # Upload video to Telegram
        bot = Bot(token=BOT_TOKEN)
        async with bot:
            with open('temp_video.mp4', 'rb') as f:
                await bot.send_video(
                    chat_id=CHANNEL_ID,
                    video=f,
                    caption=f"Video from {post_url}",
                )

        print("✅ Uploaded successfully")
        os.remove('temp_video.mp4')

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
