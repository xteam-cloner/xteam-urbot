# < Source - t.me/testingpluginnn >
# < https://github.com/TeamUltroid/Ultroid >

"""
✘ Download song, playlist, album from Spotify!
• using -yt = better results
• Playlists will be uploaded in Log Group!

✘ **CMD:**
>>  `{i}spotify <song name>`
>>  `{i}spotify -yt <song / playlist link>`
"""

import os
from uuid import uuid4
import asyncio
from telethon.tl.types import DocumentAttributeAudio
from xteam.fns.tools import metadata
from . import * # Assuming this imports ultroid_cmd, bash, LOGS, udB, humanbytes, and fast_uploader

try:
    import spotdl
except ImportError:
    # This block will only be executed if spotdl is not found.
    # It's better to log an error or raise an exception than to try installing it
    # within the script, as installations should ideally be managed via requirements.
    LOGS.error("spotdl not found. Please install it with 'pip install spotdl'")
    # You might want to exit or disable the functionality if spotdl is crucial.

# Define constants for better readability
TEMP_DIR = "resources/spotify"
# Use f-strings for cleaner formatting
UPLOAD_TEXT = "**Uploading {0}/{1}**\n»» `{2}!`"
MAX_AUDIO_SIZE_FOR_METADATA = 10 * 1024 * 1024  # 10 MB


def list_dir(folder):
    """
    Lists the contents of a directory, excluding the .spotdl-cache folder.
    Returns a list of full paths to the items in the directory.
    """
    # Using a list comprehension for a more concise way to build the list
    return [
        os.path.join(folder, item)
        for item in os.listdir(folder)
        if item != ".spotdl-cache"
    ]


async def get_attrs(path):
    """
    Generates DocumentAttributeAudio for files smaller than MAX_AUDIO_SIZE_FOR_METADATA.
    Uses an external metadata function to extract audio information.
    """
    if os.path.getsize(path) <= MAX_AUDIO_SIZE_FOR_METADATA:
        # Assuming 'metadata' is an async function that returns a dict
        minfo = await metadata(path)
        return [
            DocumentAttributeAudio(
                duration=minfo.get("duration"),
                title=minfo.get("title"),
                performer=minfo.get("performer"),
            )
        ]
    return []


@ultroid_cmd(pattern="spot(?:dl|ify)(?: (-yt)?|$)(.*)")
async def spotify_dl(e):
    """
    Downloads songs from Spotify (or YouTube if -yt is specified) using spotdl.
    Uploads the downloaded songs to Telegram.
    """
    # Extract arguments from the command
    use_youtube = bool(e.pattern_match.group(1))
    search_query = e.pattern_match.group(2).strip()

    # Get search query from reply if not provided in the command
    if not search_query:
        reply_message = await e.get_reply_message()
        if reply_message and reply_message.text:
            search_query = reply_message.text
        else:
            return await e.eor("Please provide a song name or reply to a message with one.", time=5)

    # Create a unique temporary directory for downloads
    download_folder = os.path.join(TEMP_DIR, str(uuid4().hex)[:8])
    os.makedirs(download_folder, exist_ok=True)

    eris = await e.eor("`Searching on Spotify! Please wait...`")

    # Construct the spotdl command
    cmd = (
        f'spotdl "{search_query}" -o "{download_folder}" '
        "--ignore-ffmpeg-version --dt 20 --st 20"
    )
    if use_youtube:
        cmd += " --use-youtube"

    await bash(cmd)  # Execute the spotdl command
    await asyncio.sleep(2)  # Give a small delay for files to settle

    files = list_dir(download_folder)

    if not files:
        return await eris.eor(f"**No results found for:** `{search_query}`", time=30)

    # Determine the chat ID for uploading. Use LOG_CHANNEL for playlists with many songs.
    # Assuming udB.get_key("LOG_CHANNEL") returns an integer chat ID.
    chat_id = int(udB.get_key("LOG_CHANNEL")) if len(files) > 8 else e.chat_id

    for count, file_path in enumerate(files, start=1):
        file_name = os.path.basename(file_path)
        await eris.edit(UPLOAD_TEXT.format(count, len(files), file_name))

        attributes = await get_attrs(file_path)
        file_size = humanbytes(os.path.getsize(file_path))

        # Use fast_uploader for efficient uploads
        # Assuming fast_uploader returns a tuple where the first element is the file ID/object
        uploaded_files = await e.client.fast_uploader(
            file_path, show_progress=False, to_delete=True
        )

        if not uploaded_files:
            LOGS.error(f"Error occurred while uploading: {file_name}")
            continue

        await e.client.send_file(
            chat_id,
            uploaded_files[0],
            caption=f"`{file_name}` – [ `{file_size}` ]",
            silent=True,
            attributes=attributes,
            supports_streaming=True,
        )
        await asyncio.sleep(5)  # Small delay between uploads

    await eris.eor(f"**Uploaded {len(files)} song(s)!**", time=20)
