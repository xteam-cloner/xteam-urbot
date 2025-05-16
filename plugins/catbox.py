import os
import requests
from telethon import TelegramClient, events, Button
from . import *

def upload_file(file_path):
    url = "https://catbox.moe/user/api.php"
    data = {"reqtype": "fileupload", "json": "true"}
    files = {"fileToUpload": open(file_path, "rb")}
    try:
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()  # Raise an exception for bad status codes
        return True, response.text.strip()
    except requests.exceptions.RequestException as e:
        return False, f"ᴇʀʀᴏʀ: {e}"

@ultroid_cmd(pattern="tgm")
async def get_link_group(event):
    if not event.is_reply:
        await event.reply("Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇᴅɪᴀ ᴛᴏ ᴜᴘʟᴏᴀᴅ ᴏɴ Tᴇʟᴇɢʀᴀᴘʜ")
        return

    replied_msg = await event.get_reply_message()
    media = replied_msg.media
    if not media:
        await event.reply("Rᴇᴘʟɪᴇᴅ ᴍᴇssᴀɢᴇ ᴅᴏᴇs ɴᴏᴛ ᴄᴏɴᴛᴀɪɴ ᴀ ᴍᴇᴅɪᴀ ғɪʟᴇ.")
        return

        file_size = 0
    if replied_msg.photo:
        # 'sizes' adalah list, kita ambil ukuran terbesar dari list tersebut
        if replied_msg.photo.sizes:
            file_size = max(s.size for s in replied_msg.photo.sizes if hasattr(s, 'size'))
    elif replied_msg.video:
        file_size = replied_msg.video.size
    elif replied_msg.document:
        file_size = replied_msg.document.size
        
    if file_size > 200 * 1024 * 1024:
        await event.reply("Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴍᴇᴅɪᴀ ғɪʟᴇ ᴜɴᴅᴇʀ 200MB.")
        return

    try:
        text_message = await event.reply("❍ ʜᴏʟᴅ ᴏɴ ʙᴀʙʏ....♡")

        async def progress(current, total):
            try:
                await event.eor(
                    text_message, f"📥 Dᴏᴡɴʟᴏᴀᴅɪɴɢ... {current * 100 / total:.1f}%"
                )
            except Exception:
                pass

        try:
            local_path = await event.download_media(replied_msg, progress_callback=progress)
            await event.eor(text_message, "📤 Uᴘʟᴏᴀᴅɪɴɢ ᴛᴏ ᴛᴇʟᴇɢʀᴀᴘʜ...")

            success, upload_path = upload_file(local_path)

            if success:
                await event.eor(
                    text_message,
                    f"🌐 | [👉ʏᴏᴜʀ ʟɪɴᴋ ᴛᴀᴘ ʜᴇʀᴇ👈]({upload_path})",
                    buttons=[[Button.url(" ᴛᴀᴘ ᴛᴏ sᴇᴇ ", upload_path)]],
                )
            else:
                await event.eor(
                    text_message,
                    f"ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴜᴘʟᴏᴀᴅɪɴɢ ʏᴏᴜʀ ғɪʟᴇ\n{upload_path}",
                )

            try:
                os.remove(local_path)
            except Exception:
                pass

        except Exception as e:
            await event.eor(
                text_message, f"❌ Fɪʟᴇ ᴜᴘʟᴏᴀᴅ ғᴀɪʟᴇᴅ\n\n<i>Rᴇᴀsᴏɴ: {e}</i>"
            )
            try:
                os.remove(local_path)
            except Exception:
                pass
            return
    except Exception as e:
        print(f"An error occurred: {e}")

@ultroid_cmd(pattern="tgh")
async def get_link_group_alt(event):
    # This is a duplicate of the .tgm command.
    # You can keep it if you want two different command names for the same function.
    if not event.is_reply:
        await event.reply("Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇᴅɪᴀ ᴛᴏ ᴜᴘʟᴏᴀᴅ ᴏɴ Tᴇʟᴇɢʀᴀᴘʜ")
        return

    replied_msg = await event.get_reply_message()
    media = replied_msg.media
    if not media:
        await event.reply("Rᴇᴘʟɪᴇᴅ ᴍᴇssᴀɢᴇ ᴅᴏᴇs ɴᴏᴛ ᴄᴏɴᴛᴀɪɴ ᴀ ᴍᴇᴅɪᴀ ғɪʟᴇ.")
        return

        file_size = 0
    if replied_msg.photo:
        # 'sizes' adalah list, kita ambil ukuran terbesar dari list tersebut
        if replied_msg.photo.sizes:
            file_size = max(s.size for s in replied_msg.photo.sizes if hasattr(s, 'size'))
    elif replied_msg.video:
        file_size = replied_msg.video.size
    elif replied_msg.document:
        file_size = replied_msg.document.size
        
    if file_size > 200 * 1024 * 1024:
        await event.reply("Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴍᴇᴅɪᴀ ғɪʟᴇ ᴜɴᴅᴇʀ 200MB.")
        return

    try:
        text_message = await event.reply("❍ ʜᴏʟᴅ ᴏɴ ʙᴀʙʏ....♡")

        async def progress(current, total):
            try:
                await event.eor(
                    text_message, f"📥 Dᴏᴡɴʟᴏᴀᴅɪɴɢ... {current * 100 / total:.1f}%"
                )
            except Exception:
                pass

        try:
            local_path = await event.download_media(replied_msg, progress_callback=progress)
            await event.eor(text_message, "📤 Uᴘʟᴏᴀᴅɪɴɢ ᴛᴏ ᴛᴇʟᴇɢʀᴀᴘʜ...")

            success, upload_path = upload_file(local_path)

            if success:
                await event.eor(
                    text_message,
                    f"🌐 | [👉ʏᴏᴜʀ ʟɪɴᴋ ᴛᴀᴘ ʜᴇʀᴇ👈]({upload_path})",
                    buttons=[[Button.url(" ᴛᴀᴘ ᴛᴏ sᴇᴇ ", upload_path)]],
                )
            else:
                await event.eor(
                    text_message,
                    f"ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴜᴘʟᴏᴀᴅɪɴɢ ʏᴏᴜʀ ғɪʟᴇ\n{upload_path}",
                )

            try:
                os.remove(local_path)
            except Exception:
                pass

        except Exception as e:
            await event.eor(
                text_message, f"❌ Fɪʟᴇ ᴜᴘʟᴏᴀᴅ ғᴀɪʟᴇᴅ\n\n<i>Rᴇᴀsᴏɴ: {e}</i>"
            )
            try:
                os.remove(local_path)
            except Exception:
                pass
            return
    except Exception as e:
        print(f"An error occurred: {e}")
