""" Google Text to Speech
Available Commands:
{tr}tts <LanguageCode> ; <text>
{tr}tts <text> (uses 'en' by default)
{tr}tts <LanguageCode> (as reply to a message)
"""

import os
import subprocess
from datetime import datetime

from gtts import gTTS

# Menggunakan impor spesifik dari Xteam/Ultroid yang Anda berikan
from xteam._misc._decorators import ultroid_cmd
from xteam._misc._wrappers import eod, eor # eod = edit_delete, eor = edit_or_reply
from xteam.fns.helper import deEmojify # Mengasumsikan deEmojify ada di sini, atau di import *
from xteam.fns.misc import reply_id # Mengasumsikan reply_id ada di sini, atau di import *

# Jika deEmojify dan reply_id tidak ada di fns.helper/fns.misc:
# Harap pastikan fungsi ini tersedia atau impor dari lokasi aslinya.
# Jika Anda menggunakan core Ultroid, mungkin harus kembali ke:
# from ultroid.core.helpers import deEmojify
# from telethon.utils import get_reply_id as reply_id 
# Namun, saya akan mengikuti struktur impor Xteam Anda.

plugin_category = "utils"


@ultroid_cmd(
    pattern="tts(?:\s|$)([\s\S]*)",
    command=("tts", plugin_category),
    info={
        "header": "Text to speech command using Google TTS.",
        "usage": [
            "{tr}tts <text>",
            "{tr}tts <reply>",
            "{tr}tts <language code> ; <text>",
        ],
    },
)
async def tts_cmd(event):
    "Text to speech command"
    input_str = event.pattern_match.group(1)
    start = datetime.now()
    
    # Menggunakan reply_id yang diimpor dari fns.misc (sesuai struktur Xteam)
    reply_to_id = await reply_id(event) 

    lan = "en"  # Default language
    text = None

    if ";" in input_str:
        try:
            lan, text = input_str.split(";", 1)
            lan = lan.strip()
            text = text.strip()
        except ValueError:
            # Fallback jika split gagal
            text = input_str.strip()
            lan = "en"
    elif event.reply_to_msg_id:
        previous_message = await event.get_reply_message()
        text = previous_message.message
        # Jika reply, input_str digunakan sebagai language code
        lan = input_str.strip() or "en"
    else:
        text = input_str.strip()
        lan = "en"

    if not text:
        return await eor(event, "Invalid Syntax. Please provide text or reply to a message.", time=5)

    # Menggunakan eor (Edit or Reply)
    catevent = await eor(event, "`Recording......`")
    
    try:
        # Menggunakan deEmojify yang diimpor (sesuai struktur Xteam)
        text = deEmojify(text)
        
        if not os.path.isdir("./temp/"):
            os.makedirs("./temp/")
            
        required_file_name = "./temp/" + "voice.ogg"
        
        # gTTS part
        tts = gTTS(text, lang=lan)
        tts.save(required_file_name)

        # FFMPEG Conversion to OGG Opus
        opus_file_name = f"{required_file_name}.opus"
        command_to_execute = [
            "ffmpeg",
            "-i",
            required_file_name,
            "-map",
            "0:a",
            "-codec:a",
            "libopus",
            "-b:a",
            "100k",
            "-vbr",
            "on",
            opus_file_name,
        ]

        try:
            # Execute FFmpeg command (output diabaikan)
            subprocess.check_output(
                command_to_execute, stderr=subprocess.STDOUT
            )
            os.remove(required_file_name)
            final_file_name = opus_file_name
        except (subprocess.CalledProcessError, NameError, FileNotFoundError) as exc:
            # Jika FFmpeg gagal, gunakan file OGG mentah
            final_file_name = required_file_name
            # Perlu diperhatikan, di userbot Xteam/Ultroid, logging harus digunakan di sini.

        # --- Send File and Cleanup ---
        end = datetime.now()
        ms = (end - start).seconds
        
        await event.client.send_file(
            event.chat_id,
            final_file_name,
            reply_to=reply_to_id,
            allow_cache=False,
            voice_note=True,  # Kirim sebagai voice note
        )
        
        # Cleanup
        os.remove(final_file_name)
        if os.path.exists(required_file_name): # Pastikan file OGG mentah juga dihapus
             os.remove(required_file_name)
             
        # Menggunakan eod (Edit or Delete)
        await eod(
            catevent, f"`Processed text {text[:30]}... into voice in {ms} seconds!`", time=5
        )

    except Exception as e:
        # Menggunakan eor untuk melaporkan error
        await eor(catevent, f"**Error during TTS process:**\n`{e}`\n\n*Check language code (`{lan}`) or `ffmpeg` installation.*", time=10)
                         
