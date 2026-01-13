import asyncio
import os
import random
import time
from urllib.parse import urlparse

import cloudscraper
from motor.motor_asyncio import AsyncIOMotorClient

from config import *
from extractors import SITE_EXTRACTORS
from utils import apply_replacements, parse_duration, sanitize_filename
from video_processing import add_floating_text

# MongoDB connection
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

async def upload_with_retry(bot, file_path, title, description, duration, retries=3):
    """Upload video with retry + stats."""
    import os
    import math
    import time
    from telegram import Bot
    from telegram.error import BadRequest, NetworkError, RetryAfter, TimedOut

    file_size = os.path.getsize(file_path)
    size_mb = file_size / (1024 * 1024)
    readable_duration = parse_duration(duration)

    # Use file store channel for large files to potentially bypass limits
    upload_chat_id = FILE_STORE_CHANNEL[0] if size_mb > 50 else CHANNEL_ID

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
                    chat_id=upload_chat_id,
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

        # Check if direct video URL
        if post_url.endswith('.mp4'):
            print(f"Direct video URL detected: {post_url}")
            video_url = post_url
            title = "Direct Video"
            description = "Downloaded directly from URL"
            duration = "00:00:00"  # Default duration
            readable_duration = "00:00:00"
            modified = False
            # Add random metadata edits
            import random
            emojis = ['🔥', '💥', '⭐', '🌟', '🎉', '😍', '👍', '❤️']
            random_emoji = random.choice(emojis)
            title += f" {random_emoji}"
            description += f" Enjoy! {random_emoji}"
        else:
            print(f"Fetching page content from {post_url}")
            scraper = cloudscraper.create_scraper()
            html = scraper.get(post_url).text

            # Get domain
            domain = urlparse(post_url).netloc
            print(f"Domain: {domain}")
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

            # Add random metadata edits
            import random
            emojis = ['🔥', '💥', '⭐', '🌟', '🎉', '😍', '👍', '❤️']
            random_emoji = random.choice(emojis)
            title += f" {random_emoji}"
            description += f" Enjoy! {random_emoji}"
            upload_date = None
            thumbnail_url = None
            thumbnail_local_path = None

            video_url = extractor['extract_video_url'](html)
            if not video_url:
                print("No video found.")
                return
            upload_date = extractor['extract_upload_date'](html)
            thumbnail_url = extractor['extract_thumbnail_url'](html)
            thumbnail_local_path = None
            if thumbnail_url:
                os.makedirs('thumbnails', exist_ok=True)
                filename = thumbnail_url.split('/')[-1]
                path = f'thumbnails/{filename}'
                try:
                    with scraper.get(thumbnail_url, stream=True) as r:
                        r.raise_for_status()
                        with open(path, 'wb') as f:
                            for chunk in r.iter_content(1024):
                                if chunk:
                                    f.write(chunk)
                    thumbnail_local_path = path
                    print(f"Thumbnail downloaded: {path}")
                except Exception as e:
                    print(f"Failed to download thumbnail: {e}")
            
            print(f"Found video URL: {video_url}")
            print(f"Title: {title}")
            print(f"Duration: {readable_duration}")

        from telegram import Bot
        bot = Bot(token=BOT_TOKEN)
        async with bot:
            status_msg = await bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"⬇️ **Downloading video…**\n{post_url}"
            )

            # ---------- Download ----------
            scraper = cloudscraper.create_scraper()  # Reinitialize if needed
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

                from utils import encode
                base64_string = await encode(f"get-{msg_id * abs(FILE_STORE_CHANNEL[0])}")
                bot_username = random.choice(USERNAMES)
                link = f"https://t.me/{bot_username}?start={base64_string}"
                link_msg = await bot.send_message(chat_id=CHANNEL_ID, text=f"🎬 **{title}**\n\n📝 {description}\n\n⏱️ Duration: {readable_duration}\n\nclick below link for file🔗 {link}")
                # Forward the message to forward channels
                for forward_channel in FORWARD_CHANNELS:
                    await bot.forward_message(chat_id=forward_channel, from_chat_id=CHANNEL_ID, message_id=link_msg.message_id)
                # Mark as processed in DB
                await collection.insert_one({
                    'url': post_url,
                    'title': title,
                    'description': description,
                    'duration': duration,
                    'upload_date': upload_date,
                    'thumbnail_local_path': thumbnail_local_path,
                    'processed_at': time.time()
                })
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