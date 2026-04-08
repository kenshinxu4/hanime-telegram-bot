from pyrogram import *
from pyrogram.types import *

def start(client, message):
    message.reply_text(
    "**/search <hentai name> to search**\n Powered By @KENSHIN_ANIME", 
    parse_mode="md"
)
