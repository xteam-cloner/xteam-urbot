# Ultroid plugin to convert image to Ghibli style with optional custom prompt

import base64
import aiohttp
from telethon.tl.types import MessageMediaPhoto
import os
from . import eor, ultroid_cmd

API_KEY = "AIzaSyDQBgED9EZ7k89kJuBewuw5QmBESKE1TNU"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent"

DEFAULT_PROMPT = (
    "Convert this photo to a high-quality Studio Ghibli style anime image. "
    "Make it look like it was hand-drawn by Studio Ghibli artists with their distinctive style, colors, and aesthetics. "
    "Keep the subject recognizable but with anime features."
)


@ultroid_cmd(pattern="anime ?(.*)")
async def ghibli_convert(event):
    prompt = event.pattern_match.group(1) or DEFAULT_PROMPT

    reply = await event.get_reply_message()
    if not (reply and reply.media and isinstance(reply.media, MessageMediaPhoto)):
        return await eor(event, "Reply to a photo to convert it to Ghibli/anime style.")

    temp = await eor(event, "**Status**: [ `♻️ Downloading` ]")

    downloaded = await reply.download_media()
    with open(downloaded, "rb") as img_file:
        encoded_img = base64.b64encode(img_file.read()).decode()

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": encoded_img
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["Text", "Image"]
        }
    }

    await temp.edit("**Status**: [ `⚡ Proccessing` ]")

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, params={"key": API_KEY}, json=payload) as resp:
            result = await resp.json()

    try:
        if result["candidates"]:
            image_data = result['candidates'][0]['content']['parts'][0]['inlineData']['data']
        else:
            return await temp.edit(f"**Status**: [ `💔 Error` ]\n {result}")
        
        decoded = base64.b64decode(image_data)
        await temp.edit("**Status**: [ `❤️‍🩹 Done` ]")
        out = "ghibli_output.jpg"
        with open(out, "wb") as f:
            f.write(decoded)
        caption = f"<b>🖼️ Genrated Image</b>\n\n<b>🌟 Query:</b> <code>{prompt}</code>\n\n <blockquote>[ 🔐 <i>@AgainOwner</i> ]</blockquote>"
        await event.client.send_file(event.chat_id, out, reply_to=reply.id, caption=caption, parse_mode="html")
        try:
            os.system("rm photo_*.jpg")
            os.remove(out)
            await temp.edit("**Status**: [ `🗑️ Cleanup` ]")
        except:
            pass
        await temp.delete()
    except Exception as e:
        await temp.edit(f"Something went wrong:\n`{str(e)}`")
