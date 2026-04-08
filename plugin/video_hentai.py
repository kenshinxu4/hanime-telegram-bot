import os
import subprocess
import requests
from pyrogram import Client, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pymongo import MongoClient

# Variables fetch kar rahe hain
MONGO_URL = os.environ.get("MONGO_URL") 
CACHE_CHANNEL = int(os.environ.get("CACHE_CHANNEL", "-100123456789"))
hentaidb = MongoClient(MONGO_URL)
db_collection = hentaidb["MangaDb"]["Name"]

async def hentailink(client, callback_query):
    # Ye function hona zaroori hai import ke liye
    link = callback_query.data.split("_")[1]
    url = f"https://apikatsu.otakatsu.studio/api/hanime/link?id={link}" 
    
    try:
        res = requests.get(url).json()
        data = res.get("data", [])
        
        if not data:
            await callback_query.answer("Links not found!", show_alert=True)
            return

        keyb = []
        for item in data:
            if item.get("url"):
                keyb.append([InlineKeyboardButton(f"Stream {item['height']}p", url=item['url'])])
        
        keyb.append([InlineKeyboardButton("Back", callback_data=f"info_{link}")])
        repl = InlineKeyboardMarkup(keyb)
        
        text = f"You are now watching: `https://hanime.tv/videos/hentai/{link}`\n\nShared by @KENSHIN_ANIME"
        await client.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.id,
            text=text,
            reply_markup=repl,
            parse_mode=enums.ParseMode.MARKDOWN
        )
    except Exception as e:
        await callback_query.answer(f"Error: {e}", show_alert=True)

async def hentaidl(client, callback_query):
    # Ye doosra function hai jo import ho raha hai
    link = callback_query.data.split("_")[1]
    chatid = callback_query.from_user.id
    
    await callback_query.edit_message_text("Wait... Status: **DOWNLOADING**", parse_mode=enums.ParseMode.MARKDOWN)
    
    is_hentai = db_collection.find_one({"name": link})
    if is_hentai:
        await callback_query.edit_message_text("Status: **UPLOADING**", parse_mode=enums.ParseMode.MARKDOWN)
        await client.send_document(chat_id=chatid, document=is_hentai["file_id"], caption="Downloaded By @KENSHIN_ANIME")
        return

    api_url = f"https://apikatsu.otakatsu.studio/api/hanime/link?id={link}"
    try:
        res_data = requests.get(api_url).json().get("data", [])
        if res_data:
            video_url = res_data[-1]["url"] 
            file_name = f"{link}.mp4"
            
            subprocess.run(f'ffmpeg -i "{video_url}" -c copy "{file_name}"', shell=True)
            
            await callback_query.edit_message_text("Status: **UPLOADING**", parse_mode=enums.ParseMode.MARKDOWN)
            
            sent_msg = await client.send_document(chat_id=chatid, document=file_name, caption="Downloaded By @KENSHIN_ANIME")
            file_id = sent_msg.document.file_id
            
            await client.send_document(chat_id=CACHE_CHANNEL, document=file_id, caption=f"Backup: {link}")
            db_collection.insert_one({"name": link, "file_id": file_id})
            
            if os.path.exists(file_name):
                os.remove(file_name)
        else:
            await callback_query.edit_message_text("Download failed. Link not found.")
    except Exception as e:
        await callback_query.edit_message_text(f"Error: {e}")
