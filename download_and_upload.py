import os
import re
import asyncio
import cloudscraper
import time
import math
from telegram import Bot, Update
from telegram.error import TimedOut, RetryAfter, NetworkError, BadRequest
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import REPLACEMENTS, ADMIN_ID

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
CHANNEL_ID = -1002706635277


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
            with open(file_path, "rb") as f:
                await bot.send_video(
                    chat_id=CHANNEL_ID,
                    video=f,
                    caption=f"🎬 **{title}**\n\n📝 {description}\n\n⏱️ Duration: {readable_duration}",
                    read_timeout=1800,   # 30 min
                    write_timeout=1800,
                    connect_timeout=60,
                )
            speed = size_mb / (time.time() - start + 0.01)
            await msg.edit_text(
                f"✅ **Upload complete!**\n📦 `{size_mb:.2f} MB`\n⚡ Speed ≈ {speed:.2f} MB/s\n🔁 Attempts: {attempt}"
            )
            return
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


async def process_url(post_url):
    try:
        print(f"Fetching page content from {post_url}")
        scraper = cloudscraper.create_scraper()
        html = scraper.get(post_url).text

        # Extract metadata
        title_match = re.search(r'<meta itemprop="name\s*" content="([^"]*)"', html)
        title = title_match.group(1) if title_match else "Unknown Title"

        desc_match = re.search(r'<meta itemprop="description" content="([^"]*)"', html)
        description = desc_match.group(1) if desc_match else "No description"

        dur_match = re.search(r'<meta itemprop="duration" content="([^"]*)"', html)
        duration = dur_match.group(1) if dur_match else "Unknown"
        readable_duration = parse_duration(duration)

        # Apply replacements to title and description
        title, title_modified = apply_replacements(title, REPLACEMENTS)
        description, desc_modified = apply_replacements(description, REPLACEMENTS)
        modified = title_modified or desc_modified

        match = re.search(r"(https?://vk[^\s\"]+\.mp4)", html)
        if not match:
            print("No video found.")
            return

        video_url = match.group(1)
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

            await status_msg.edit_text("✅ **Download complete!** Uploading…")

            # ---------- Upload ----------
            if modified:
                await upload_with_retry(bot, filename, title, description, duration)
            else:
                print("No replacements applied, skipping upload.")
                await status_msg.edit_text("❌ No replacements applied, skipping upload.")

        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")


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

    await application.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
