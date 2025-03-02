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
    response = requests.get('https://api.github.com/search/repositories', headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        repositories = data.get('items', [])
        if not repositories:
            return "No public repositories found matching your query."
        results = []
        for repo in repositories:
            results.append(f"[{repo['full_name']}]({repo['html_url']}) - {repo['description'] or 'No description'}")
        return "\n\n".join(results)
    else:
        return f"Error: {response.status_code} - {response.text}"


@ultroid_cmd(pattern="repo")
async def handle_github_search(event):
    query = event.message.message.split(' ', 1)
    if len(query) > 1:
        query = query[1]
        await event.respond("Searching public GitHub repositories...")
        results = await search_public_github(query)
        await event.respond(results, parse_mode='md')
    else:
        await event.respond("Usage: repo <search query>")
