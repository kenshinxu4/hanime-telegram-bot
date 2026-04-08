from pyrogram import Client, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import requests

async def hentaisearch(client, message):
    msgSplit = message.text.split(" ")
    if len(msgSplit) == 1:
        await client.send_animation(
            chat_id=message.chat.id,
            animation="https://telegra.ph/file/cdeae50a8a23041b01935.mp4",
            caption="**/search <space> hentai name**",
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return

    query = " ".join(msgSplit[1:])
    url = f"https://apikatsu.otakatsu.studio/api/hanime/search?query={query}&page=0"
    
    try:
        result = requests.get(url).json()
        K = result.get("response", [])
        
        if not K:
            await message.reply_text("No results found. Please check spelling.")
            return

        keyb = []
        for x in K:
            slug = x["slug"]
            name = x["name"]
            keyb.append([InlineKeyboardButton(f"{name}", callback_data=f"info_{slug}")])
        
        repl = InlineKeyboardMarkup(keyb)
        await message.reply_text(
            f"Your Search Results for **{query}**", 
            reply_markup=repl, 
            parse_mode=enums.ParseMode.MARKDOWN
        )
    except Exception as e:
        await message.reply_text(f"Error: {e}")
