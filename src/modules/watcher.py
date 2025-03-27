from pytdbot import Client, types

from src.database import db
from src.logger import LOGGER
from src.modules.utils.admins import load_admin_cache
from src.modules.utils.buttons import AddMeButton
from src.modules.utils.cacher import chat_cache


async def handle_non_supergroup(client: Client, chat_id: int):
    """Handles cases where the bot is added to a non-supergroup chat."""
    text = f"""{chat_id} is not a supergroup yet.
<b>⚠️: Please convert this chat to a supergroup and add me as admin.</b>

If you don't know how to convert, use this guide:
🔗 https://te.legra.ph/How-to-Convert-a-Group-to-a-Supergroup-01-02

If you have any questions, join our support group:
"""
    reply = await client.sendTextMessage(
        chat_id, text, parse_mode="HTML", reply_markup=AddMeButton
    )
    if isinstance(reply, types.Error):
        LOGGER.warning(f"Error sending message: {reply}")

    ok = await client.leaveChat(chat_id)
    if isinstance(ok, types.Error):
        LOGGER.warning(f"Error leaving chat: {ok}")


@Client.on_updateChatMember()
async def chat_member(client: Client, update: types.UpdateChatMember):
    """Handles member updates in the chat (joins, leaves, promotions, demotions, bans, and unbans)."""
    chat_id = update.chat_id
    # Non supergroup
    if chat_id > 0:
        return await handle_non_supergroup(client, chat_id)

    await db.add_chat(chat_id)
    user_id = update.new_chat_member.member_id.user_id
    old_status = update.old_chat_member.status["@type"]
    new_status = update.new_chat_member.status["@type"]

    # User Joined (New Member)
    if old_status == "chatMemberStatusLeft" and new_status in {
        "chatMemberStatusMember",
        "chatMemberStatusAdministrator",
    }:
        LOGGER.info(f"User {user_id} joined the chat {chat_id}.")
        return

    # User Left (Left or Kicked)
    if (
            old_status in {"chatMemberStatusMember", "chatMemberStatusAdministrator"}
            and new_status == "chatMemberStatusLeft"
    ):
        LOGGER.info(f"User {user_id} left or was kicked from {chat_id}.")
        return

    # User Banned
    if new_status == "chatMemberStatusBanned":
        LOGGER.info(f"User {user_id} was banned in {chat_id}.")
        return

    # User Unbanned
    if old_status == "chatMemberStatusBanned" and new_status == "chatMemberStatusLeft":
        LOGGER.info(f"User {user_id} was unbanned in {chat_id}.")
        return

    is_promoted = (
            old_status != "chatMemberStatusAdministrator"
            and new_status == "chatMemberStatusAdministrator"
    )
    # Bot Promoted
    if user_id == client.options["my_id"] and is_promoted:
        LOGGER.info(f"Bot was promoted in {chat_id}, reloading admin permissions.")
        await load_admin_cache(client, chat_id, True)
        return

    # User Promoted
    if is_promoted:
        LOGGER.info(f"User {user_id} was promoted in {chat_id}.")
        await load_admin_cache(client, chat_id, True)
        return

    # User Demoted
    is_demoted = (
            old_status == "chatMemberStatusAdministrator"
            and new_status != "chatMemberStatusAdministrator"
    )
    if is_demoted:
        LOGGER.info(f"User {user_id} was demoted in {chat_id}.")
        if user_id == client.options["my_id"] or client.me.id:
            return
        await load_admin_cache(client, chat_id, True)
        return

    return


@Client.on_updateNewMessage(position=1)
async def new_message(_: Client, update: types.UpdateNewMessage):
    if not hasattr(update, "message"):
        return
    message = update.message
    if isinstance(message.content, types.MessageVideoChatEnded):
        LOGGER.info(f"Video chat ended in {message.chat_id}")
        await chat_cache.clear_chat(message.chat_id)
        return
    elif isinstance(message.content, types.MessageVideoChatStarted):
        LOGGER.info(f"Video chat started in {message.chat_id}")
        await chat_cache.clear_chat(message.chat_id)
        return

    LOGGER.debug(f"New message in {message.chat_id}: {message}")
    return
