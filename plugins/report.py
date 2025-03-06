from telethon import TelegramClient, events
import asyncio
import logging
from . import *


moderator_id : 460000

async def send_report(client, user_id, message_id, reported_message_text):
    """Sends a report to the moderator."""
    try:
        user = await client.get_entity(user_id)
        report_message = (
            f"⚠️ Report from @{user.username} ({user_id}):\n"
            f"Message ID: {message_id}\n"
            f"Reported Message: {reported_message_text}\n"
            f"Link to Message: https://t.me/c/{str(group_id).replace('-100', '')}/{message_id}"
        )
        await client.send_message(moderator_id, report_message)
        await client.send_message(user_id, "Your report has been sent to the moderator.")

    except Exception as e:
        logging.error(f"Error sending report: {e}")
        await client.send_message(user_id, "Failed to send the report. Please try again later.")

@ultroid_cmd(pattern="report")
async def handle_report(event):
    """Handles the /report command."""
    if event.is_private:
        await event.respond("This command can only be used in groups.")
        return

    reply_to = await event.get_reply_message()

    if reply_to:
        user_id = event.sender_id
        message_id = reply_to.id
        reported_message_text = reply_to.text or reply_to.media  # Include media if present.
        await send_report(bot, user_id, message_id, reported_message_text)
    else:
        await event.respond("Please reply to the message you want to report.")

