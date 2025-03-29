from aiofiles import os

import config
from src import client


async def create_directories() -> None:
    """Create necessary directories."""
    try:
        await os.makedirs(config.DOWNLOADS_DIR, exist_ok=True)
        await os.makedirs("database/photos", exist_ok=True)
    except Exception as e:
        raise SystemExit(1) from e


if __name__ == "__main__":
    client.loop.create_task(create_directories())
    client.run()
