from telethon import TelegramClient, events
from bs4 import BeautifulSoup
import requests
import re
from . import *

async def get_imdb_info(movie_title):
    """Mengambil informasi film dari IMDb."""
    try:
        # Mencari film di IMDb
        search_url = f"https://www.imdb.com/find?q={movie_title}&s=tt&ttype=ft"
        search_response = requests.get(search_url)
        search_response.raise_for_status()  # Memunculkan HTTPError untuk respons yang buruk (4xx atau 5xx)

        search_soup = BeautifulSoup(search_response.content, 'html.parser')
        movie_link = search_soup.find('a', href=re.compile(r'/title/tt\d+'))['href']
        movie_url = f"https://www.imdb.com{movie_link}"

        # Mengambil informasi film
        movie_response = requests.get(movie_url)
        movie_response.raise_for_status()

        movie_soup = BeautifulSoup(movie_response.content, 'html.parser')

        title = movie_soup.find('h1').text.strip()
        rating = movie_soup.find('span', class_='AggregateRatingButton__RatingScore-sc-1ll29k4-1 fgmrzC').text.strip()
        plot = movie_soup.find('span', class_='GenresAndPlot__Plot-cum89p-6 bUyrFc').text.strip()

        return f"**{title}**\nRating: {rating}\n\n{plot}"

    except requests.exceptions.RequestException as e:
        return f"Terjadi kesalahan saat mengambil informasi film: {e}"
    except AttributeError:
        return "Film tidak ditemukan."

@ultroid_cmd(pattern="imdb (.*)")
async def imdb_handler(event):
    """Menangani perintah /imdb."""
    movie_title = event.pattern_match.group(1)
    await event.respond(await get_imdb_info(movie_title))

