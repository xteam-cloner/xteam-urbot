import asyncio
import platform
import subprocess
from datetime import datetime
import asyncio
from platform import python_version as pyver
from pyrogram.enums import ChatType
from pyrogram import __version__ as pver
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from telethon.tl.types import ReplyKeyboardMarkup, KeyboardButton
#from telethon.tl.types import KeyboardButton
from telegram import __version__ as lver
from telethon import __version__ as tver
from pytgcalls import __version__ as pytver
from pyrogram import filters
from pyrogram.types import Message
from telethon import TelegramClient, events
from telethon.tl.custom import Button
from . import *
from . import ultroid_bot as client
import resources
from pyUltroid.fns.helper import inline_mention

async def member_permissions(chat_id: int, user_id: int):
    perms = []
    member = (await ultroid_bot.get_chat_member(chat_id, user_id)).privileges
    if not member:
        return []
    if member.can_post_messages:
        perms.append("can_post_messages")
    if member.can_edit_messages:
        perms.append("can_edit_messages")
    if member.can_delete_messages:
        perms.append("can_delete_messages")
    if member.can_restrict_members:
        perms.append("can_restrict_members")
    if member.can_promote_members:
        perms.append("can_promote_members")
    if member.can_change_info:
        perms.append("can_change_info")
    if member.can_invite_users:
        perms.append("can_invite_users")
    if member.can_pin_messages:
        perms.append("can_pin_messages")
    if member.can_manage_video_chats:
        perms.append("can_manage_video_chats")
    return perms

PHOTO = [
    "https://telegra.ph/file/d2a23fbe48129a7957887.jpg",
    "https://telegra.ph/file/ddf30888de58d77911ee1.jpg",
    "https://telegra.ph/file/268d66cad42dc92ec65ca.jpg",
    "https://telegra.ph/file/13a0cbbff8f429e2c59ee.jpg",
    "https://telegra.ph/file/bdfd86195221e979e6b20.jpg",
]

Mukesh = [
    [
        Button.url("ɴᴏᴏʙ", url=f"https://t.me/{OWNER_USERNAME}"),
        Button.url("ꜱᴜᴘᴘᴏʀᴛ", url=f"https://t.me/xteam_cloner"),
    ],
    [
        Button.url("➕ᴀᴅᴅ ᴍᴇ ᴇʟsᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ➕",
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true",
        ),
    ],
]

message_text = [
"ʜᴇʏ, ɪ ᴀᴍ 『 {BOT_NAME} 🥀』
   ━━━━━━━━━━━━━━━━━━━
  » ᴍʏ ᴏᴡɴᴇʀ : {inline_mention(ultroid_bot.me)}
  
  » ʟɪʙʀᴀʀʏ ᴠᴇʀsɪᴏɴ : {lver}
  
  » ᴛᴇʟᴇᴛʜᴏɴ ᴠᴇʀsɪᴏɴ : {tver}
  
  » ᴘʏʀᴏɢʀᴀᴍ ᴠᴇʀsɪᴏɴ : {pver}
  
  » ᴘʏᴛʜᴏɴ ᴠᴇʀsɪᴏɴ : {pyver()}
   ━━━━━━━━━━━━━━━━━━━"
]


@ultroid_cmd(pattern="Alive$")
async def alive(event):
    await event.delete()
    accha = await event.reply("⚡")
    await asyncio.sleep(1)
    await accha.edit("ᴅɪɴɢ ᴅᴏɴɢ ꨄ︎ ᴀʟɪᴠɪɴɢ..")
    await asyncio.sleep(1)
    await accha.delete()
    umm = await event.reply(file="resources/extras/ping_pic.mp4")
    await asyncio.sleep(1)
    await umm.delete()
    owner=await ultroid_bot.get_users(OWNER_ID)
    await client.send_message(event.chat.id, message_text, buttons=Mukesh)
    
