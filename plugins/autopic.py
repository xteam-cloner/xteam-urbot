import asyncio
import os
import random
from random import shuffle

from telethon.tl.functions.photos import UploadProfilePhotoRequest

from xteam.fns.helper import download_file
from xteam.fns.tools import google_images_download

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

    try:
        pth = await google_images_download(search)
        # Corrected: Access the 'search' key directly from the dictionary
        ok = pth.get(search) # Using .get() is safer, returns None if key not found
        if ok is None: # If the key 'search' is not found in pth
            # This indicates an unexpected structure from google_images_download.
            # You might want to log pth to understand its actual structure.
            LOGS.warning(f"Unexpected output from google_images_download for '{search}': {pth}")
            return await e.eor(get_string("autopic_2").format(search), time=5)

    except Exception as er:
        LOGS.exception(er)
        return await e.eor(str(er))

    if not ok: # Check if the list of paths is empty
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
            # This usage confirms that google_images_download is an async function that takes 'search'
            # And also implies that it returns something that can be directly assigned to images[search]
            pth_result = await google_images_download(search)
            # Assuming pth_result is a dictionary like {"query": [paths...]}
            images[search] = pth_result.get(search)
            if not images[search]:
                LOGS.warning(f"No images found for '{search}' in autopic_func.")
                return

        if not images.get(search):
            return
        
        # Add a check here for empty list, though it's already done above when assigning.
        if not images[search]:
            LOGS.warning(f"No images available for '{search}' to choose from.")
            return

        img = random.choice(images[search])
        filee = await download_file(img["original"], "resources/downloads/autopic.jpg") # This implies img is a dictionary with an "original" key, not just a path.
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
