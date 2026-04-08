import os
import logging
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler

# Plugins import (Make sure these paths are correct)
from plugin.search_hentai import hentaisearch
from plugin.info_hentai import infohentai
from plugin.video_hentai import hentailink, hentaidl
from plugin.start import start

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

# Environment Variables
# API_ID ko int() mein convert karna zaroori hai
API_ID = int(os.environ.get("API_ID", "0")) 
API_HASH = os.environ.get("API_HASH", None) 
BOT_TOKEN = os.environ.get("BOT_TOKEN", None) 

bot = Client(
    "comic",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    sleep_threshold=30 # Ye network stability mein help karega
)

def main():
    # Handlers setup
    bot.add_handler(MessageHandler(hentaisearch, filters.regex(r'search')), group=1)
    bot.add_handler(CallbackQueryHandler(hentaidl, filters.regex('dlt_*')), group=5)
    bot.add_handler(CallbackQueryHandler(infohentai, filters.regex('info_*')), group=2)
    bot.add_handler(CallbackQueryHandler(hentailink, filters.regex('link_*')), group=6)
    bot.add_handler(MessageHandler(start, filters.regex(r'start')), group=13)

if __name__ == '__main__':
    bot.run(main())
