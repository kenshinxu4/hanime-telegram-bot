from pyrogram import Client, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import requests

async def infohentai(client, callback_query):
    click = callback_query.data
    clickSplit = click.split("_")
    query = clickSplit[1]
    
    chatid = callback_query.from_user.id
    messageid = callback_query.message.id
    
    url = f"https://apikatsu.otakatsu.studio/api/hanime/details?id={query}" 
    result = requests.get(url).json()
    
    name = result.get("name", "N/A")
    img = result.get("poster", "")
    view = result.get("views", "0")     
    released_date = result.get("released_date", "N/A")
    
    keyb = [
        [InlineKeyboardButton("Download Now", callback_data=f"dlt_{query}")],
        [InlineKeyboardButton("Link", callback_data=f"link_{query}")]
    ]
    repl = InlineKeyboardMarkup(keyb)
    
    text = f"**Name:** [{name}]({img})\n**View:** {view}\n**Release Date:** {released_date}"
    
    await client.edit_message_text(
        chat_id=chatid, 
        message_id=messageid, 
        text=text, 
        reply_markup=repl, 
        parse_mode=enums.ParseMode.MARKDOWN
    )
