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
        # Corrected: Pass only the search query string
        # Assuming google_images_download handles its own internal configuration
        pth = await google_images_download(search)
        ok = pth[0][search] # This line assumes pth has the same structure as before.
                            # If it changes, you might need to adjust this.
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
            images[search] = await google_images_download(search)
        if not images.get(search):
            return
        img = random.choice(images[search])
        filee = await download_file(img["original"], "resources/downloads/autopic.jpg")
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
