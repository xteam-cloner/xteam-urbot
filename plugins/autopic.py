import asyncio
import os
import random
from random import shuffle
#from google_images_download import google_images_download as GoogleImagesDownload # Corrected import
from telethon.tl.functions.photos import UploadProfilePhotoRequest

from xteam.fns.helper import download_file
from xteam.fns.tools import get_google_images # Assuming get_google_images returns image data directly

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
        # Assume get_google_images directly returns the image paths/data
        # It might return a list of dictionaries, where each dict contains 'url' or 'path'
        # Or it might return a dictionary similar to what google_images_download returns
        # Let's try to adapt to the original structure 'pth[0][search]' if possible
        # If get_google_images already handles the limit, you might not need to pass it explicitly if it's configurable within the function.
        # For now, let's pass the search directly as it was causing the initial Type Error for 'query'.
        # We'll assume the result format is similar to google_images_download's 'pth'
        raw_images_data = await get_google_images(search)

        # Adapt this part based on the actual structure of 'raw_images_data'
        # If raw_images_data is already a list of image paths/URLs:
        # ok = raw_images_data

        # If raw_images_data is structured like google_images_download's output:
        # Example: {'search_term': ['path/to/img1.jpg', 'path/to/img2.jpg']}
        if isinstance(raw_images_data, list) and len(raw_images_data) > 0 and isinstance(raw_images_data[0], dict) and search in raw_images_data[0]:
             ok = raw_images_data[0][search] # Assuming the structure is [{search_term: [paths]}]
        elif isinstance(raw_images_data, dict) and search in raw_images_data:
            ok = raw_images_data[search] # If it's directly {search_term: [paths]}
        else:
            # Fallback if the structure is not as expected, perhaps it's a direct list of paths/URLs
            ok = raw_images_data if isinstance(raw_images_data, list) else []
            # You might need more specific handling here if it's not a list of paths
            LOGS.warning(f"Unexpected structure from get_google_images: {type(raw_images_data)}. Attempting to treat as list of paths.")


        if not ok: # If ok is still empty after trying to extract
            return await e.eor(get_string("autopic_2").format(search), time=5)

    except Exception as er:
        LOGS.exception(er)
        return await e.eor(f"Error fetching images: {str(er)}")

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
            try:
                # Again, assume get_google_images returns the data directly
                raw_images_data_func = await get_google_images(search)

                # Adapt this part based on the actual structure of 'raw_images_data_func'
                # For a single random image, it's likely a direct list of URLs or paths
                if isinstance(raw_images_data_func, list) and len(raw_images_data_func) > 0 and isinstance(raw_images_data_func[0], dict) and search in raw_images_data_func[0]:
                    # If the structure is [{search_term: [paths]}]
                    # We only need one for `autopic_func` to get a random one.
                    # However, since `get_google_images` probably fetches more than 1,
                    # we'll store all available URLs/paths and then pick one.
                    temp_ok = raw_images_data_func[0][search]
                    images[search] = [item["url"] for item in temp_ok] if any("url" in item for item in temp_ok) else temp_ok
                elif isinstance(raw_images_data_func, dict) and search in raw_images_data_func:
                    # If it's directly {search_term: [paths]}
                    temp_ok = raw_images_data_func[search]
                    images[search] = [item["url"] for item in temp_ok] if any("url" in item for item in temp_ok) else temp_ok
                else:
                    # Fallback if the structure is not as expected, assume it's a direct list of paths/URLs
                    images[search] = raw_images_data_func if isinstance(raw_images_data_func, list) else []
                    LOGS.warning(f"Unexpected structure from get_google_images in autopic_func: {type(raw_images_data_func)}. Attempting to treat as list of paths/URLs.")

            except Exception as er:
                LOGS.exception(er)
                images[search] = [] # Set to empty to avoid further errors

        if not images.get(search):
            LOGS.warning(f"No images found for search term: {search} in autopic_func.")
            return

        # Assuming images[search] now contains a list of URLs or local paths
        img_source = random.choice(images[search])

        # Determine if it's a URL or a local file path
        if img_source.startswith(("http://", "https://")):
            filee = await download_file(img_source, "resources/downloads/autopic.jpg")
        else:
            # It's already a local path
            filee = img_source

        file = await ultroid_bot.upload_file(filee)
        await ultroid_bot(UploadProfilePhotoRequest(file))
        if img_source.startswith(("http://", "https://")) and os.path.exists(filee):
            os.remove(filee) # Only remove if it was a downloaded file

    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        schedule = AsyncIOScheduler()
        schedule.add_job(autopic_func, "interval", seconds=sleep)
        schedule.start()
    except ModuleNotFoundError as er:
        LOGS.error(f"autopic: '{er.name}' not installed.")
