import asyncio
import random
import re

from telegram import Bot, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from config import *
from main import process_url, automated_posting
from utils import encode

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