from telethon import TelegramClient
import asyncio
from . import ultroid_cmd

@ultroid_cmd(pattern="cp( (.*)|$)", owner_only=True)
async def check_ping():
    result = await client.ping()
    print(f"Ping: {result} seconds")

async def main():
    while True:
        await check_ping()
        await asyncio.sleep(60)
