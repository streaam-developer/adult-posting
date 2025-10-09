import subprocess
import os
import re
import cloudscraper
from telegram import Bot

BOT_TOKEN = '7760514362:AAEukVlluWrzqOrsO4-i_dH7F73oXQEmRgw'
CHANNEL_ID = '-1002706635277'

post_url = 'https://viralkand.com/hotel-room-mein-gf-ne-lund-choos-ke-pani-nikaal-diya/'

try:
    print(f"Fetching page content from {post_url} using cloudscraper.")
    # Create a cloudscraper instance to bypass Cloudflare
    scraper = cloudscraper.create_scraper()
    response = scraper.get(post_url)
    response.raise_for_status()  # Raise an exception for bad status codes
    html_content = response.text

    # Search for the video URL in the HTML content
    match = re.search(r'(https?://vk[^\s"]+\.mp4)', html_content)
    if not match:
        print("Could not find video URL in the page source.")
        exit(1)

    video_url = match.group(1)
    print(f"Found video URL: {video_url}")

    print(f"Downloading video from {video_url}")
    # Download using yt-dlp.
    result = subprocess.run(['yt-dlp', video_url, '-o', 'temp_video.mp4'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Failed to download: {result.stderr}")
        exit(1)

    # Upload to Telegram
    bot = Bot(token=BOT_TOKEN)
    with open('temp_video.mp4', 'rb') as f:
        bot.send_video(chat_id=CHANNEL_ID, video=f, caption=f"Video from {post_url}")

    print("Uploaded successfully")
    os.remove('temp_video.mp4')

except Exception as e:
    print(f"An unexpected error occurred: {e}")