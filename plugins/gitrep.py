import asyncio
from telethon import TelegramClient, events
import requests
from . import*


async def search_public_github(query):
    headers = {
        'Accept': 'application/vnd.github.v3+json',
    }
    params = {
        'q': query,
        'per_page': 5,
        'type': 'public',
    }
    try:
        response = requests.get('https://api.github.com/search/repositories', headers=headers, params=params)
        response.raise_for_status()  # Menimbulkan HTTPError untuk respons buruk (4xx atau 5xx)
        data = response.json()
        repositories = data.get('items', [])
        if not repositories:
            return "Tidak ada repositori publik yang ditemukan sesuai dengan kueri Anda."
        results = []
        for repo in repositories:
            results.append(f"[{repo['full_name']}]({repo['html_url']}) - {repo['description'] or 'Tidak ada deskripsi'}")
        return "\n\n".join(results)
    except requests.exceptions.RequestException as e:
        return f"Kesalahan: {e}"
    except ValueError:
        return "Kesalahan: Respons JSON tidak valid dari API GitHub."
    except KeyError:
        return "Kesalahan: Format data tidak terduga dari API GitHub."

@ultroid_cmd(pattern="repo")
async def handle_github_search(event):
    query = event.message.message.split(' ', 1)
    if len(query) > 1:
        query = query[1]
        await event.eor("Mencari repositori GitHub publik...")
        try:
            results = await search_public_github(query)
            await event.respond(results, parse_mode='md')
        except Exception as e:
            await event.respond(f"Terjadi kesalahan saat mencari: {e}")
    else:
        await event.respond("Penggunaan: repo <kueri pencarian>")
