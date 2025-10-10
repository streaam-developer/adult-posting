import asyncio
import base64
import math
import os
import random
import re
import time
from urllib.parse import urlparse

import cloudscraper
import ffmpeg
from motor.motor_asyncio import AsyncIOMotorClient
from telegram import Bot, Update
from telegram.error import BadRequest, NetworkError, RetryAfter, TimedOut
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from config import (ADMIN_ID, COLLECTION_NAME, DB_NAME, FORWARD_CHANNELS,
                    MONGO_URI, REPLACEMENTS, USERNAMES)


def parse_duration(iso_duration):
    """Parse ISO 8601 duration to HH:MM:SS format."""
    # Handle formats like P0DT0H1M10S or PT1M10S
    match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_duration)
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    # If no match, try to extract from P0DT0H1M10S format
    match = re.search(r'P\d+DT(\d+)H(\d+)M(\d+)S', iso_duration)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return iso_duration

def sanitize_filename(name):
    """Sanitize string for use as filename."""
    return re.sub(r'[<>:"/\\|?*]', '', name).strip()

async def encode(string):
    return base64.urlsafe_b64encode(string.encode()).decode()

def apply_replacements(text, replacements):
    """Apply case-insensitive word replacements to text. Returns modified text and if any replacement was made."""
    modified = False
    for old, new in replacements.items():
        # Use word boundaries to replace whole words
        pattern = r'\b' + re.escape(old) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            text = re.sub(pattern, new, text, flags=re.IGNORECASE)
            modified = True
    return text, modified

BOT_TOKEN = '7760514362:AAEukVlluWrzqOrsO4-i_dH7F73oXQEmRgw'
CHANNEL_ID = -1002818242381
FILE_STORE_CHANNEL = [-1002747781375]

# MongoDB connection
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]


# Site-specific extractors
def extract_title_default(html):
    match = re.search(r'<meta itemprop="name\s*" content="([^"]*)"', html)
    return match.group(1) if match else "Unknown Title"

def extract_description_default(html):
    match = re.search(r'<meta itemprop="description" content="([^"]*)"', html)
    return match.group(1) if match else "No description"

def extract_duration_default(html):
    match = re.search(r'<meta itemprop="duration" content="([^"]*)"', html)
    return match.group(1) if match else "Unknown"

def extract_video_url_default(html):
    match = re.search(r"(https?://[^\s\"]+\.mp4)", html)
    return match.group(1) if match else None

SITE_EXTRACTORS = {
    'viralkand.com': {
        'extract_title': extract_title_default,
        'extract_description': extract_description_default,
        'extract_duration': extract_duration_default,
        'extract_video_url': lambda html: re.search(r"(https?://vk[^\s\"]+\.mp4)", html).group(1) if re.search(r"(https?://vk[^\s\"]+\.mp4)", html) else None,
    },
    # Add more domains as needed
    'default': {
        'extract_title': extract_title_default,
        'extract_description': extract_description_default,
        'extract_duration': extract_duration_default,
        'extract_video_url': extract_video_url_default,
    }
}


# Video editor function
def add_floating_text(video_path, output_path):
    """Add floating 'zeb.monster' text to video in random places and directions."""
    try:
        # Get video dimensions
        probe = ffmpeg.probe(video_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        width = int(video_stream['width'])
        height = int(video_stream['height'])

        # Center of the screen
        center_x = width / 2
        center_y = height / 2

        # Random amplitudes and frequencies for sinusoidal movement
        amplitude_x = random.uniform(0, width / 4)
        amplitude_y = random.uniform(0, height / 4)
        freq_x = random.uniform(0.1, 0.5)
        freq_y = random.uniform(0.1, 0.5)

        # Construct the ffmpeg drawtext filter
        text = 'zeb.monster'
        x_expr = f"{center_x} + {amplitude_x}*sin({freq_x}*2*PI*t)"
        y_expr = f"{center_y} + {amplitude_y}*sin({freq_y}*2*PI*t)"

        (
            ffmpeg
            .input(video_path)
            .drawtext(text=text, x=x_expr, y=y_expr, fontsize=50, fontcolor='white', box=1, boxcolor='black@0.5', fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
            .output(output_path, vcodec='libx264', acodec='aac')
            .run(overwrite_output=True)
        )
    except Exception as e:
        print(f"Error in add_floating_text: {e}")
        print("Video editing failed. Please ensure ffmpeg is installed and in your PATH.")
        import shutil
        shutil.copy(video_path, output_path)


async def upload_with_retry(bot, file_path, title, description, duration, retries=3):
    """Upload video with retry + stats."""
    file_size = os.path.getsize(file_path)
    size_mb = file_size / (1024 * 1024)
    readable_duration = parse_duration(duration)
    msg = await bot.send_message(
        chat_id=CHANNEL_ID,
        text=f"📤 **Starting upload...**\n🎬 *{title}*\n📦 `{size_mb:.2f} MB`"
    )

    for attempt in range(1, retries + 1):
        try:
            print(f"📤 Attempt {attempt}: uploading {size_mb:.2f} MB…")
            start = time.time()

            caption = f"🎬 **{title}**\n\n📝 {description}\n\n⏱️ Duration: {readable_duration}"
            if len(caption) > 1024:
                caption = f"🎬 **{title}**"

            with open(file_path, "rb") as f:
                video_msg = await bot.send_video(
                    chat_id=CHANNEL_ID,
                    video=f,
                    caption=caption,
                    read_timeout=1800,   # 30 min
                    write_timeout=1800,
                    connect_timeout=60,
                )
            speed = size_mb / (time.time() - start + 0.01)
            await msg.edit_text(
                f"✅ **Upload complete!**\n📦 `{size_mb:.2f} MB`\n⚡ Speed ≈ {speed:.2f} MB/s\n🔁 Attempts: {attempt}"
            )
            return video_msg
        except RetryAfter as e:
            wait = math.ceil(e.retry_after) + 5
            print(f"⚠️ Flood control — waiting {wait}s")
            await msg.edit_text(f"⏳ Flood control, retrying in {wait}s…")
            await asyncio.sleep(wait)
        except (TimedOut, NetworkError) as e:
            print(f"⚠️ Timeout/network error: {e}")
            await msg.edit_text(f"⚠️ Timeout/network error (attempt {attempt}) — retrying…")
            await asyncio.sleep(10)
        except Exception as e:
            await msg.edit_text(f"❌ Upload failed: {e}")
            print(f"❌ Upload failed: {e}")
            break

    await msg.edit_text("❌ Upload failed after multiple retries.")
    return None


async def process_url(post_url):
    try:
        # Check if URL already processed
        if await collection.find_one({'url': post_url}):
            print(f"URL {post_url} already processed.")
            return

        print(f"Fetching page content from {post_url}")
        scraper = cloudscraper.create_scraper()
        html = scraper.get(post_url).text

        # Get domain
        domain = urlparse(post_url).netloc
        extractor = SITE_EXTRACTORS.get(domain, SITE_EXTRACTORS['default'])

        # Extract metadata
        title = extractor['extract_title'](html)
        description = extractor['extract_description'](html)
        duration = extractor['extract_duration'](html)
        readable_duration = parse_duration(duration)

        # Apply replacements to title and description
        title, title_modified = apply_replacements(title, REPLACEMENTS)
        description, desc_modified = apply_replacements(description, REPLACEMENTS)
        modified = title_modified or desc_modified

        video_url = extractor['extract_video_url'](html)
        if not video_url:
            print("No video found.")
            return

        print(f"Found video URL: {video_url}")
        print(f"Title: {title}")
        print(f"Duration: {readable_duration}")

        bot = Bot(token=BOT_TOKEN)
        async with bot:
            status_msg = await bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"⬇️ **Downloading video…**\n{post_url}"
            )

            # ---------- Download ----------
            with scraper.get(video_url, stream=True) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                downloaded = 0
                chunk_size = 256 * 1024  # 256 KB chunks for faster I/O
                start_time = time.time()
                last_update = 0

                filename = sanitize_filename(title) + ".mp4"
                with open(filename, "wb") as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded += len(chunk)
                        now = time.time()
                        # Update every 2 seconds only
                        if now - last_update >= 2:
                            elapsed = now - start_time
                            speed = downloaded / 1024 / 1024 / elapsed if elapsed > 0 else 0
                            percent = (downloaded / total * 100) if total else 0
                            try:
                                await status_msg.edit_text(
                                    f"⬇️ **Downloading…** {percent:.1f}%\n"
                                    f"📥 {downloaded/(1024*1024):.2f}/{total/(1024*1024):.2f} MB\n"
                                    f"⚡ Speed: {speed:.2f} MB/s"
                                )
                            except BadRequest as e:
                                if "Message is not modified" not in str(e):
                                    print(f"Edit error: {e}")
                            last_update = now

            # ---------- Edit Video ----------
            if VIDEO_EDITING_ENABLED:
                await status_msg.edit_text("✅ **Download complete!** Editing video…")
                edited_filename = filename.replace('.mp4', '_edited.mp4')
                add_floating_text(filename, edited_filename)
                await status_msg.edit_text("✅ **Video edited!** Uploading…")
                video_to_upload = edited_filename
            else:
                await status_msg.edit_text("✅ **Download complete!** Uploading…")
                video_to_upload = filename

            # ---------- Upload ----------
            video_msg = await upload_with_retry(bot, video_to_upload, title, description, duration)
            if video_msg:
                msg_id = video_msg.message_id + 1

                base64_string = await encode(f"get-{msg_id * abs(FILE_STORE_CHANNEL[0])}")
                bot_username = random.choice(USERNAMES)
                link = f"https://t.me/{bot_username}?start={base64_string}"
                link_msg = await bot.send_message(chat_id=CHANNEL_ID, text=f"🎬 **{title}**\n\n📝 {description}\n\n⏱️ Duration: {readable_duration}\n\nclick below link for file🔗 {link}")
                # Forward the message to forward channels
                for forward_channel in FORWARD_CHANNELS:
                    await bot.forward_message(chat_id=forward_channel, from_chat_id=CHANNEL_ID, message_id=link_msg.message_id)
                # Mark as processed in DB
                await collection.insert_one({'url': post_url, 'processed_at': time.time()})
                # Update last post time
                await collection.update_one({'type': 'last_post'}, {'$set': {'timestamp': time.time()}}, upsert=True)
            else:
                print("Upload failed.")
                await status_msg.edit_text("❌ Upload failed.")

        if os.path.exists(filename):
            os.remove(filename)
        if 'edited_filename' in locals() and os.path.exists(edited_filename):
            os.remove(edited_filename)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def automated_posting():
    while True:
        try:
            # Read links from file
            with open('links.txt', 'r', encoding='utf-8', errors='ignore') as f:
                links = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            if not links:
                print("No links in links.txt")
                await asyncio.sleep(3600)  # wait 1 hour
                continue
            # Pick random link
            post_url = random.choice(links)
            # Fetch last post time
            last_post_doc = await collection.find_one({'type': 'last_post'})
            if last_post_doc:
                last_post_time = last_post_doc['timestamp']
                print(f"Last post time: {time.ctime(last_post_time)}")
            else:
                print("No previous posts found.")
            print(f"Auto-processing: {post_url}")
            await process_url(post_url)
            # Sleep for 1-1.5 hours
            #sleep_time = random.randint(60, 90)
            sleep_time = random.randint(3600, 5400)
            print(f"Sleeping for {sleep_time} seconds")
            await asyncio.sleep(sleep_time)
        except Exception as e:
            print(f"Error in automated posting: {e}")
            await asyncio.sleep(600)  # wait 10 min on error

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.from_user.id == ADMIN_ID:
        text = update.message.text
        if text and re.match(r'https?://', text.strip()):
            post_url = text.strip()
            await update.message.reply_text("Processing URL...")
            await process_url(post_url)
        else:
            await update.message.reply_text("Please send a valid URL.")
    else:
        await update.message.reply_text("Unauthorized.")


async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start automated posting
    asyncio.create_task(automated_posting())

    await application.run_polling()


def run_bot():
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass
    asyncio.run(main())


if __name__ == "__main__":
    run_bot()
