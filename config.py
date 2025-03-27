from os import getenv

from dotenv import load_dotenv

load_dotenv()

"You can get these variables from my.telegram.org"
API_ID = int(getenv("API_ID", None))
API_HASH = getenv("API_HASH", None)

"You can get this variable from @BotFather"
TOKEN = getenv("TOKEN", None)

"Pyrogram/kurigram String Session"
STRING = getenv("STRING", None)
STRING2 = getenv("STRING2", None)
STRING3 = getenv("STRING3", None)
STRING4 = getenv("STRING4", None)
STRING5 = getenv("STRING5", None)
STRING6 = getenv("STRING6", None)
STRING7 = getenv("STRING7", None)
STRING8 = getenv("STRING8", None)
STRING9 = getenv("STRING9", None)
STRING10 = getenv("STRING10", None)

SESSION_STRINGS = [
    STRING,
    STRING2,
    STRING3,
    STRING4,
    STRING5,
    STRING6,
    STRING7,
    STRING8,
    STRING9,
    STRING10,
]

"Your Telegram User ID"
OWNER_ID = int(getenv("OWNER_ID", 5938660179))

"Your MongoDB URI; get it from https://cloud.mongodb.com"
MONGO_URI = getenv("MONGO_URI", None)

API_URL = getenv("API_URL", None)
API_KEY = getenv("API_KEY", None)
PROXY_URL = getenv("PROXY_URL", None)

DOWNLOADS_DIR = getenv("DOWNLOADS_DIR", "database/music")
YOUTUBE_IMG_URL = "https://te.legra.ph/file/6298d377ad3eb46711644.jpg"
