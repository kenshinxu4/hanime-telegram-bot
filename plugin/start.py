from pyrogram import *
from pyrogram.types import *

def start(client, message):
    # Sirf text likho, parse_mode likhne ki zaroorat nahi hai
message.reply_text("**/search <hentai name> to search**\n Powered By @KENSHIN_ANIME")
