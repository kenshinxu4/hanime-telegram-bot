from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode  # <-- YEH ADD KIYA
import aiohttp
import re
import os

# ========== CONFIG ==========
API_ID = int(os.getenv("API_ID", "12345"))
API_HASH = os.getenv("API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")

# ========== ANILIST API ==========
ANILIST_URL = "https://graphql.anilist.co"

SEARCH_QUERY = """
query ($search: String) {
    Page(perPage: 8) {
        media(search: $search, type: ANIME) {
            id
            title {
                romaji
                english
            }
            coverImage {
                extraLarge
            }
        }
    }
}
"""

INFO_QUERY = """
query ($id: Int) {
    Media(id: $id, type: ANIME) {
        id
        title {
            romaji
            english
            native
        }
        coverImage {
            extraLarge
        }
        format
        status
        episodes
        duration
        season
        seasonYear
        averageScore
        genres
        studios {
            nodes {
                name
            }
        }
        description
        relations {
            edges {
                relationType
                node {
                    id
                    title {
                        romaji
                    }
                }
            }
        }
    }
}
"""

# ========== HELPERS ==========
def extract_season_number(title, relations):
    """Extract season number from title"""
    if not title:
        return "01"
    
    title = title.lower()
    
    # Pattern 1: "Season 2"
    match = re.search(r'season\s+(\d+)', title)
    if match:
        return f"{int(match.group(1)):02d}"
    
    # Pattern 2: "2nd Season"
    match = re.search(r'(\d+)(?:st|nd|rd|th)\s+season', title)
    if match:
        return f"{int(match.group(1)):02d}"
    
    # Pattern 3: "Part 2"
    match = re.search(r'part\s+(\d+)', title)
    if match:
        return f"{int(match.group(1)):02d}"
    
    # Pattern 4: Number at end
    match = re.search(r'\s+(\d+)$', title)
    if match:
        return f"{int(match.group(1)):02d}"
    
    # Check prequel
    if relations and relations.get('edges'):
        prequels = [edge for edge in relations['edges'] if edge.get('relationType') == 'PREQUEL']
        if prequels:
            return "02"
    
    return "01"

def get_studio(studios):
    if studios and studios.get('nodes'):
        return studios['nodes'][0]['name']
    return "Unknown"

def format_status(status):
    return {
        "FINISHED": "finished airing",
        "RELEASING": "currently airing",
        "NOT_YET_RELEASED": "not yet released",
        "CANCELLED": "cancelled"
    }.get(status, status.lower().replace("_", " "))

def format_rating(score):
    if not score:
        return "N/A"
    styled = str(score).translate(str.maketrans("0123456789", "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿"))
    return f"{styled}/𝟷𝟶"

def clean_desc(text):
    if not text:
        return "No synopsis available."
    text = text.replace("<br>", "\n").replace("<i>", "").replace("</i>", "").replace("<b>", "").replace("</b>", "")
    if len(text) > 380:
        return text[:380].rsplit(' ', 1)[0] + "..."
    return text

async def fetch_anilist(query, variables):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(ANILIST_URL, json={"query": query, "variables": variables}, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data')
                return None
    except Exception as e:
        print(f"Fetch error: {e}")
        return None

# ========== BOT ==========
# parse_mode HATA DIYA Client se
app = Client(
    "anime_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=100
)

# ========== HANDLERS ==========
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "<b>🎌 Kenshin Anime Bot</b>\n\n"
        "Search any anime info with HD posters!\n\n"
        "<b>Usage:</b>\n"
        "• /search [anime name]\n"
        "• Direct message anime name\n\n"
        "<i>Powered by Anilist</i>",
        parse_mode=ParseMode.HTML  # <-- HAR JAGAH ADD KIYA
    )

@app.on_message(filters.command("search"))
async def search(client, message):
    query = message.text.replace("/search", "").strip()
    if not query:
        await message.reply_text(
            "⚠️ Provide anime name!\nExample: /search Solo Leveling",
            parse_mode=ParseMode.HTML
        )
        return
    
    await send_results(client, message, query)

@app.on_message(filters.text & ~filters.command(["start", "search"]))
async def direct_search(client, message):
    if len(message.text) < 2:
        return
    await send_results(client, message, message.text)

async def send_results(client, message, query):
    temp = await message.reply_text(
        "🔍 <b>Searching...</b>",
        parse_mode=ParseMode.HTML
    )
    
    data = await fetch_anilist(SEARCH_QUERY, {"search": query})
    if not data or not data.get('Page', {}).get('media'):
        await temp.edit_text(
            "❌ <b>No results found!</b>",
            parse_mode=ParseMode.HTML
        )
        return
    
    animes = data['Page']['media']
    
    buttons = []
    for anime in animes:
        title = anime['title'].get('english') or anime['title'].get('romaji') or "Unknown"
        btn = InlineKeyboardButton(
            f"🎬 {title[:35]}{'...' if len(title) > 35 else ''}",
            callback_data=f"info_{anime['id']}"
        )
        buttons.append([btn])
    
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    
    await temp.edit_text(
        f"<b>🎯 {len(animes)} results for:</b> <code>{query}</code>\n\n<i>Select one:</i>",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )

@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    
    if data == "cancel":
        await callback_query.answer("Cancelled!")
        await callback_query.message.delete()
        return
    
    if data.startswith("info_"):
        anime_id = int(data.split("_")[1])
        await callback_query.answer("⏳ Loading...")
        
        info_data = await fetch_anilist(INFO_QUERY, {"id": anime_id})
        if not info_data or not info_data.get('Media'):
            await callback_query.message.edit_text(
                "❌ <b>Error fetching info!</b>",
                parse_mode=ParseMode.HTML
            )
            return
        
        anime = info_data['Media']
        
        title_english = anime['title'].get('english') or ""
        title_romaji = anime['title'].get('romaji') or ""
        
        season_num = extract_season_number(title_romaji, anime.get('relations'))
        display_title = title_english if title_english else title_romaji
        
        caption = f"""<b><blockquote>「 {display_title.upper()} 」</blockquote>
═══════════════════
🌸 Category: {anime.get('format', 'Anime')}
🍥 Season: {season_num} 
🧊 Episodes: {anime.get('episodes') or 'N/A'} 
🍣 Runtime: {anime.get('duration') or 'N/A'} min per ep 
🍡 Rating: {format_rating(anime.get('averageScore'))}
🍙 Status: {format_status(anime.get('status'))} 
🍵 Studio: {get_studio(anime.get('studios')).lower()}
🎐 Genres: {', '.join(anime.get('genres', [])[:3]) or 'N/A'} 
═══════════════════
<blockquote>🥗 Synopsis: {clean_desc(anime.get('description'))}</blockquote>

<blockquote>POWERED BY: [@KENSHIN_ANIME]</blockquote></b>"""
        
        img = anime.get('coverImage', {}).get('extraLarge')
        
        await callback_query.message.delete()
        
        if img:
            await client.send_photo(
                chat_id=callback_query.message.chat.id,
                photo=img,
                caption=caption,
                parse_mode=ParseMode.HTML,  # <-- YAHA BHI ADD KIYA
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔍 Search Again", switch_inline_query_current_chat="")
                ]])
            )
        else:
            await client.send_message(
                chat_id=callback_query.message.chat.id,
                text=caption,
                parse_mode=ParseMode.HTML,  # <-- YAHA BHI ADD KIYA
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔍 Search Again", switch_inline_query_current_chat="")
                ]])
            )

# ========== RUN ==========
if __name__ == "__main__":
    print("🎌 Kenshin Anime Bot Started!")
    app.run()
