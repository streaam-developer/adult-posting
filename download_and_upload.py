import os
import re
import cloudscraper
from telegram import Bot

BOT_TOKEN = '7760514362:AAEukVlluWrzqOrsO4-i_dH7F73oXQEmRgw'
CHANNEL_ID = '-1002706635277'

post_url = 'https://viralkand.com/hotel-room-mein-gf-ne-lund-choos-ke-pani-nikaal-diya/'

try:
    print(f"Fetching page content from {post_url} using cloudscraper.")
    scraper = cloudscraper.create_scraper()
    response = scraper.get(post_url)
    response.raise_for_status()
    html_content = response.text

    match = re.search(r'(https?://vk[^\s"]+\.mp4)', html_content)
    if not match:
        print("Could not find video URL in the page source.")
        exit(1)

    video_url = match.group(1)
    print(f"Found video URL: {video_url}")

    print(f"Downloading video from {video_url} using cloudscraper.")
    # Use the same scraper to download the video file
    with scraper.get(video_url, stream=True) as r:
        r.raise_for_status()
        with open('temp_video.mp4', 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print("Download complete. Uploading to Telegram...")
    # Upload to Telegram
    bot = Bot(token=BOT_TOKEN)
    with open('temp_video.mp4', 'rb') as f:
        bot.send_video(chat_id=CHANNEL_ID, video=f, caption=f"Video from {post_url}")

    print("Uploaded successfully")
    os.remove('temp_video.mp4')

except Exception as e:
    print(f"An unexpected error occurred: {e}")
