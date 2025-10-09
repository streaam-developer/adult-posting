import subprocess
import os
from telegram import Bot

BOT_TOKEN = '7760514362:AAEukVlluWrzqOrsO4-i_dH7F73oXQEmRgw'
CHANNEL_ID = '-1002706635277'

post_url = 'https://viralkand.com/hotel-room-mein-gf-ne-lund-choos-ke-pani-nikaal-diya/'

try:
    print(f"Extracting video URL from {post_url} using yt-dlp.")
    # Use yt-dlp to extract the direct video URL, impersonating a browser
    process = subprocess.run(
        ['yt-dlp', post_url, '--get-url', '--extractor-args', 'generic:impersonate'],
        capture_output=True, text=True, check=True, encoding='utf-8'
    )
    # The output might have multiple URLs, we'll take the first one.
    video_url = process.stdout.strip().split('\n')[0]

    if not video_url.startswith('http'):
        print(f"Failed to extract a valid video URL. Output: {process.stdout}")
        exit(1)

    print(f"Found video URL: {video_url}")

    print(f"Downloading video from {video_url}")
    # Download the extracted URL using yt-dlp
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

except subprocess.CalledProcessError as e:
    print(f"Error extracting video URL with yt-dlp: {e.stderr}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
