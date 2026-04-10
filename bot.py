from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os

# ========== CONFIG ==========
API_ID = int(os.getenv("API_ID", "12345"))          # Telegram API ID
API_HASH = os.getenv("API_HASH", "your_api_hash")    # Telegram API Hash
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token") # BotFather se le

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
    }
}
"""

# ========== BOT ==========
app = Client(
    "anime_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=100,  # Fast responses ke liye
    parse_mode="html"
)

# ========== HELPERS ==========
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

def format_season(season, year):
    if season and year:
        num = {"WINTER": "01", "SPRING": "02", "SUMMER": "03", "FALL": "04"}.get(season, "")
        return num
    return "N/A"

def format_rating(score):
    if not score:
        return "N/A"
    # Styled numbers: 𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿
    styled = str(score).translate(str.maketrans("0123456789", "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿"))
    return f"{styled}/𝟷𝟶"

def clean_desc(text):
    if not text:
        return "No synopsis available."
    text = text.replace("<br>", "\n").replace("<i>", "").replace("</i>", "").replace("<b>", "").replace("</b>", "")
    if len(text) > 380:
        return text[:380].rsplit(' ', 1)[0] + "..."
    return text

def fetch_anilist(query, variables):
    try:
        r = requests.post(ANILIST_URL, json={"query": query, "variables": variables}, timeout=10)
        return r.json().get('data') if r.status_code == 200 else None
    except:
        return None

# ========== COMMANDS ==========
@app.on_message(filters.command("start"))
def start(_, msg):
    msg.reply_text(
        "<b>🎌 Kenshin Anime Bot</b>\n\n"
        "Search any anime info with HD posters!\n\n"
        "<b>Usage:</b>\n"
        "• /search [anime name]\n"
        "• Direct message anime name\n\n"
        "<i>Powered by Anilist</i>"
    )

@app.on_message(filters.command("search"))
def search(_, msg):
    query = msg.text.replace("/search", "").strip()
    if not query:
        return msg.reply_text("⚠️ Provide anime name!\nExample: /search Solo Leveling")
    
    send_results(msg, query)

@app.on_message(filters.text & ~filters.command(["start", "search"]))
def direct_search(_, msg):
    if len(msg.text) < 2:
        return
    send_results(msg, msg.text)

def send_results(msg, query):
    # Searching...
    temp = msg.reply_text("🔍 <b>Searching...</b>")
    
    data = fetch_anilist(SEARCH_QUERY, {"search": query})
    if not data or not data.get('Page', {}).get('media'):
        return temp.edit_text("❌ <b>No results found!</b>")
    
    animes = data['Page']['media']
    
    # Build buttons
    buttons = []
    for anime in animes:
        title = anime['title'].get('english') or anime['title'].get('romaji') or "Unknown"
        btn = InlineKeyboardButton(
            f"🎬 {title[:35]}{'...' if len(title) > 35 else ''}",
            callback_data=f"info_{anime['id']}"
        )
        buttons.append([btn])
    
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    
    temp.edit_text(
        f"<b>🎯 {len(animes)} results for:</b> <code>{query}</code>\n\n<i>Select one:</i>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ========== CALLBACKS ==========
@app.on_callback_query()
def callback_handler(_, cb):
    data = cb.data
    
    if data == "cancel":
        cb.answer("Cancelled!")
        cb.message.delete()
        return
    
    if data.startswith("info_"):
        anime_id = int(data.split("_")[1])
        cb.answer("⏳ Loading...")
        
        info_data = fetch_anilist(INFO_QUERY, {"id": anime_id})
        if not info_data or not info_data.get('Media'):
            return cb.message.edit_text("❌ <b>Error fetching info!</b>")
        
        anime = info_data['Media']
        
        # Build caption
        title = anime['title'].get('english') or anime['title'].get('romaji') or "Unknown"
        
        caption = f"""<b><blockquote>「 {title.upper()} 」</blockquote>
═══════════════════
🌸 Category: {anime.get('format', 'Anime')}
🍥 Season: {format_season(anime.get('season'), anime.get('seasonYear'))} 
🧊 Episodes: {anime.get('episodes') or 'N/A'} 
🍣 Runtime: {anime.get('duration') or 'N/A'} min per ep 
🍡 Rating: {format_rating(anime.get('averageScore'))}
🍙 Status: {format_status(anime.get('status'))} 
🍵 Studio: {get_studio(anime.get('studios')).lower()}
🎐 Genres: {', '.join(anime.get('genres', [])[:3]) or 'N/A'} 
═══════════════════
<blockquote>🥗 Synopsis: {clean_desc(anime.get('description'))}</blockquote>

<blockquote>POWERED BY: [@KENSHIN_ANIME]</blockquote></b>"""
        
        # Get HD image
        img = anime.get('coverImage', {}).get('extraLarge')
        
        # Delete old message, send new with photo
        cb.message.delete()
        
        if img:
            app.send_photo(
                chat_id=cb.message.chat.id,
                photo=img,
                caption=caption,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔍 Search Again", switch_inline_query_current_chat="")
                ]])
            )
        else:
            app.send_message(
                chat_id=cb.message.chat.id,
                text=caption,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔍 Search Again", switch_inline_query_current_chat="")
                ]])
            )

# ========== RUN ==========
if __name__ == "__main__":
    print("🎌 Kenshin Anime Bot Started!")
    app.run()
