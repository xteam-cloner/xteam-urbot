# Ultroid Plugin: Video Downloader
# Command: .dl <url> (or reply to a message containing a URL)
# Dependencies: aiohttp, urllib
#
# NOTE: This file assumes 'ultroid_cmd' is a decorator imported from a local
# Ultroid utility file (. import ultroid_cmd) that registers a Telethon event handler.

from telethon import events
# Assuming the import below works within the Ultroid framework
from . import ultroid_cmd 
import os
import aiohttp
import asyncio
import tempfile
import urllib.parse 

# --- Configuration ---
# API endpoint structure: Using the base endpoint and sending data via POST body
BASE_API = "http://38.92.25.205:63123/api/download"
HTTP_TIMEOUT = aiohttp.ClientTimeout(total=60)
DOWNLOAD_TIMEOUT = aiohttp.ClientTimeout(total=3600) # Extended timeout for large files

# --- Helper function for fetching URL ---
def get_url_from_message(event):
    """Extracts URL from command arguments or replied message."""
    text = event.raw_text
    
    # 1. Check command arguments (e.g., .dl http://...)
    parts = text.split(maxsplit=1)
    url = parts[1].strip() if len(parts) > 1 and parts[1].startswith("http") else None
    
    # 2. Check reply (requires fetching the replied message content)
    if not url and event.is_reply:
        # We need the full message object for the reply_to_msg_id to get the content
        reply_msg = asyncio.run(event.get_reply_message())
        
        if reply_msg and reply_msg.text:
            # Find the first URL-like string in the replied message
            for candidate in reply_msg.text.split():
                 if candidate.startswith("http"):
                     url = candidate
                     break
    
    return url

# --- Main Handler ---
@ultroid_cmd(pattern="dld")
async def dl_handler(event):
    """Downloads a video using the external API and uploads it via Telethon."""
    
    url = get_url_from_message(event)

    if not url:
        return await event.edit("❌ **Usage:** `.dl <video_url>` or reply to a message containing a URL.")

    # Edit the message to show processing status
    status_msg = await event.edit(f"⏳ Processing details for: `{url}`")

    # Target URL is now just the base API, as the URL parameter is moved to the JSON body
    api_url = BASE_API 

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/118.0.0.0 Safari/537.36",
        # Explicitly set content type to JSON
        "Content-Type": "application/json", 
        "Accept": "application/json",
        "Connection": "keep-alive",
    }
    
    # Data to be sent in the POST body as JSON
    json_data = {"url": url}

    temp_file_path = None

    # Use aiohttp for the requests
    async with aiohttp.ClientSession(headers=headers, timeout=HTTP_TIMEOUT) as session:
        # 1. Fetch download information from the external API
        try:
            # FIX: Using POST request with data only in the JSON body, simplifying the request URL.
            async with session.post(api_url, json=json_data) as resp:
                if resp.status != 200:
                    try:
                        # Attempt to get error message from JSON body
                        error_data = await resp.json()
                        error_message = error_data.get('message', f"HTTP Status {resp.status}")
                    except:
                        error_message = f"HTTP Status {resp.status}"
                        
                    return await status_msg.edit(f"❌ Server Error ({resp.status}): `{api_url}`\nDetails: `{error_message}`")
                
                # Check content type before parsing JSON
                if 'application/json' not in resp.content_type:
                    return await status_msg.edit(f"❌ API returned non-JSON response. Status: {resp.status}")
                
                data = await resp.json()

        except Exception as e:
            return await status_msg.edit(f"❌ API Request Failed: `{e}`")

        if data.get("status") != "success":
            return await status_msg.edit(f"❌ API Reported Failure: `{data.get('message', data)}`")

        dl_url = data.get("download_url")
        
        if not dl_url:
            return await status_msg.edit(
                f"❌ Download URL not found in API response. "
                f"The API reported success but missing the required URL. Full response: `{data}`"
            )

        title = (data.get("title") or "Download").strip()
        uploader = data.get('uploader') or '-'
        duration = data.get('duration') or '-'
        watch_url = data.get('watch_url') or url

        caption = (
            f"**{title}**\n\n"
            f"👤 Uploader: `{uploader}`\n"
            f"⏱️ Duration: `{duration}`\n"
            f"🔗 Source: [Link]({watch_url})"
        )

        # 2. Stream and upload the video
        # Create a temporary file path
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as ftmp:
            temp_file_path = ftmp.name
        
        try:
            # Update status to reflect streaming process
            await status_msg.edit(f"⚡ Streaming video file...")

            # Use a separate session/timeout for the streaming download
            async with aiohttp.ClientSession(headers=headers, timeout=DOWNLOAD_TIMEOUT) as dl_session:
                async with dl_session.get(dl_url) as resp:
                    if resp.status != 200:
                        return await status_msg.edit(f"❌ Download Link Error ({resp.status}): `{dl_url}`")
                    
                    # Write the content stream to the temporary file path
                    with open(temp_file_path, 'wb') as f:
                        async for chunk in resp.content.iter_chunked(1024 * 1024): # 1MB chunks
                            f.write(chunk)
            
            # Update status for final upload
            await status_msg.edit(f"⬆️ Uploading **{title}** to Telegram...")

            # 3. Upload the file using Telethon's send_file
            await event.client.send_file(
                event.chat_id,
                temp_file_path,
                caption=caption,
                force_document=False, # Send as video if possible
                supports_streaming=True,
                reply_to=event.reply_to_msg_id if event.is_reply else event.id
            )
            
            # Delete the status message after successful upload
            await status_msg.delete()

        except Exception as e:
            await status_msg.edit(f"❌ Video Download/Upload Failed: `{e}`")

        finally:
            # 4. Clean up the temporary file
            try:
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception:
                # Cleanup failed, ignore
                pass
