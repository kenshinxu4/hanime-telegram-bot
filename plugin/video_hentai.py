import os
import subprocess
import requests
from pyrogram import Client, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pymongo import MongoClient

MONGO_URL = os.environ.get("MONGO_URL") 
CACHE_CHANNEL = int(os.environ.get("CACHE_CHANNEL", "-100123456789"))
hentaidb = MongoClient(MONGO_URL)
db_collection = hentaidb["MangaDb"]["Name"]

async def hentaidl(client, callback_query):
    link = callback_query.data.split("_")[1]
    chatid = callback_query.from_user.id
    
    await callback_query.edit_message_text("Wait... Status: **DOWNLOADING**", parse_mode=enums.ParseMode.MARKDOWN)
    
    is_hentai = db_collection.find_one({"name": link})
    if is_hentai:
        await callback_query.edit_message_text("Status: **UPLOADING**", parse_mode=enums.ParseMode.MARKDOWN)
        # Fix yahan hai (Ending quotes added)
        await client.send_document(chat_id=chatid, document=is_hentai["file_id"], caption="Downloaded By @KENSHIN_ANIME")
        return

    # If not in DB, download using ffmpeg
    api_url = f"https://apikatsu.otakatsu.studio/api/hanime/link?id={link}"
    res_data = requests.get(api_url).json().get("data", [])
    
    if res_data:
        video_url = res_data[-1]["url"] # Best quality available
        file_name = f"{link}.mp4"
        
        subprocess.run(f'ffmpeg -i "{video_url}" -c copy "{file_name}"', shell=True)
        
        await callback_query.edit_message_text("Status: **UPLOADING**", parse_mode=enums.ParseMode.MARKDOWN)
        
        # Yahan bhi check kar lena quotes sahi hain
        sent_msg = await client.send_document(chat_id=chatid, document=file_name, caption="Downloaded By @KENSHIN_ANIME")
        file_id = sent_msg.document.file_id
        
        # Save to Cache and DB
        await client.send_document(chat_id=CACHE_CHANNEL, document=file_id, caption=f"Backup: {link}")
        db_collection.insert_one({"name": link, "file_id": file_id})
        
        os.remove(file_name)
    else:
        await callback_query.edit_message_text("Download failed. Link not found.")
