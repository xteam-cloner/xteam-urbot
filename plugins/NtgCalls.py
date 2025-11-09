
from ntgcalls import NTgCalls, MediaDescription, AudioDescription, MediaSource, StreamMode
from . import *
# ...
import youtube_dl

async def get_music_url(query):
    ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s%(ext)s', 'format': 'bestaudio'})
    info = ydl.extract_info(query, download=False)
    url = info['formats'][0]['url']
    return url

@ultroid_cmd(pattern="play")
async def play_music(event):
    chat_id = event.chat_id
    query = event.text.split(" ", 1)[1]
    url = await get_music_url(query)  # Fungsi untuk mendapatkan URL musik dari query

    if not url:
        await event.edit("Musik tidak ditemukan")
        return

    await wrtc.set_stream_sources(
        chat_id,
        StreamMode.CAPTURE,
        MediaDescription(
            microphone=AudioDescription(
                media_source=MediaSource.URL,
                input=url,
            ),
        ),
    )

    await wrtc.connect(chat_id)
    await event.edit("Musik sedang diputar")

async def get_music_url(query):
    # Fungsi untuk mendapatkan URL musik dari query
    # Contoh menggunakan YouTube
    from youtube_search import YoutubeSearch
    results = YoutubeSearch(query, max_results=1).to_dict()
    if results:
        return f"https://www.youtube.com/watch?v={results[0]['id']}"
    return None
