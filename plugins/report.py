from telethon import TelegramClient, events
import asyncio
import logging
from . import *
from . import ultroid_bot as client

moderator_id : 460000

async def send_report(client, user_id, message_id, reported_message_text, group_id):
    """
    Mengirim laporan ke moderator.

    Args:
        client: Objek TelegramClient.
        user_id: ID pengguna yang melaporkan.
        message_id: ID pesan yang dilaporkan.
        reported_message_text: Teks atau media dari pesan yang dilaporkan.
        group_id: ID grup tempat pesan dilaporkan.
    """
    try:
        user = await client.get_entity(user_id)
        report_message = (
            f"⚠️ Laporan dari @{user.username} ({user_id}):\n"
            f"ID Pesan: {message_id}\n"
            f"Pesan yang Dilaporkan: {reported_message_text}\n"
            f"Tautan Pesan: https://t.me/c/{str(group_id).replace('-100', '')}/{message_id}"
        )
        await client.send_message(moderator_id, report_message)
        await client.send_message(user_id, "Laporan Anda telah dikirim ke moderator.")

    except Exception as e:
        logging.error(f"Error mengirim laporan: {e}")
        await client.send_message(user_id, "Gagal mengirim laporan. Silakan coba lagi nanti.")

@ultroid_cmd(pattern="kureport")
async def handle_report(event):
    """Menangani perintah /report."""
    if event.is_private:
        await event.reply("Perintah ini hanya dapat digunakan di grup.")
        return

    reply_to = await event.get_reply_message()

    if reply_to:
        user_id = event.sender_id
        message_id = reply_to.id
        reported_message_text = reply_to.text or reply_to.media  # Menyertakan media jika ada.
        group_id = event.chat_id #mendapatkan group id dari event.
        await send_report(client, user_id, message_id, reported_message_text, group_id)
    else:
        await event.reply("Silakan balas pesan yang ingin Anda laporkan.")
