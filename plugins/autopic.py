import asyncio
import os
import random
from random import shuffle
#from google_images_download import google_images_download as GoogleImagesDownload # Corrected import
from telethon.tl.functions.photos import UploadProfilePhotoRequest

from xteam.fns.helper import download_file
from xteam.fns.tools import get_google_images

from . import LOGS, get_help, get_string, udB, ultroid_bot, ultroid_cmd

__doc__ = get_help("help_autopic")


@ultroid_cmd(pattern="autopic( (.*)|$)")
async def autopic(e):
    search = e.pattern_match.group(1).strip()
    if udB.get_key("AUTOPIC") and not search:
        udB.del_key("AUTOPIC")
        return await e.eor(get_string("autopic_5"))
    if not search:
        return await e.eor(get_string("autopic_1"), time=5)
    e = await e.eor(get_string("com_1"))
    gi = get_google_images() # Corrected instantiation
    args = {
        "keywords": search,
        "limit": 50,
        "format": "jpg",
        "output_directory": "./resources/downloads/",
    }
    try:
        pth = await gi.download(args)
        ok = pth[0][search]
    except Exception as er:
        LOGS.exception(er)
        return await e.eor(str(er))
    if not ok:
        return await e.eor(get_string("autopic_2").format(search), time=5)
    await e.eor(get_string("autopic_3").format(search))
    udB.set_key("AUTOPIC", search)
    SLEEP_TIME = udB.get_key("SLEEP_TIME") or 1221
    while True:
        for lie in ok:
            if udB.get_key("AUTOPIC") != search:
                return
            file = await e.client.upload_file(lie)
            await e.client(UploadProfilePhotoRequest(file))
            await asyncio.sleep(SLEEP_TIME)
        shuffle(ok)


if search := udB.get_key("AUTOPIC"):
    images = {}
    sleep = udB.get_key("SLEEP_TIME") or 1221

    async def autopic_func():
        search = udB.get_key("AUTOPIC")
        if images.get(search) is None:
            # You'll need to instantiate GoogleImagesDownload here too if it's not global
            # or if you want to use it within this function's scope.
            # Assuming you want to use the download method directly, you need to import the class again or pass an instance.
            # For simplicity, let's assume we'll instantiate it here.
            gi_instance = get_google_images()
            try:
                pth = await gi_instance.download({"keywords": search, "limit": 1}) # Limit 1 for a single random image
                ok = pth[0][search]
                images[search] = [item["url"] for item in ok] # Assuming you want URLs from the download result
            except Exception as er:
                LOGS.exception(er)
                images[search] = [] # Set to empty to avoid further errors

        if not images.get(search):
            return

        # Assuming images[search] now contains a list of URLs
        img_url = random.choice(images[search])
        filee = await download_file(img_url, "resources/downloads/autopic.jpg")
        file = await ultroid_bot.upload_file(filee)
        await ultroid_bot(UploadProfilePhotoRequest(file))
        os.remove(filee)

    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        schedule = AsyncIOScheduler()
        schedule.add_job(autopic_func, "interval", seconds=sleep)
        schedule.start()
    except ModuleNotFoundError as er:
        LOGS.error(f"autopic: '{er.name}' not installed.")
