import asyncio
import platform
import subprocess
from telethon import TelegramClient, events
from . import *

async def member_permissions(chat_id: int, user_id: int):
    perms = []
    member = (await app.get_chat_member(chat_id, user_id)).privileges
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

Xteam = [
    [
        InlineKeyboardButton(text="ɴᴏᴏʙ", user_id=OWNER_ID),
        InlineKeyboardButton(text="ꜱᴜᴘᴘᴏʀᴛ", url=f"https://t.me/xteam_cloner"),
    ],
    [
        InlineKeyboardButton(
            text="➕ᴀᴅᴅ ᴍᴇ ᴇʟsᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ➕",
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true",
        ),
    ],
]



@ultroid_cmd(pattern="calive$")
async def alive(event):
    await event.delete()
    accha = await event.reply("⚡")
    await asyncio.sleep(1)
    await accha.edit("ᴅɪɴɢ ᴅᴏɴɢ ꨄ︎ ᴀʟɪᴠɪɴɢ..")
    await asyncio.sleep(1)
    await accha.delete()
    umm = await event.reply_sticker(
        "CAACAgUAAxkDAAJHbmLuy2NEfrfh6lZSohacEGrVjd5wAAIOBAACl42QVKnra4sdzC_uKQQ"
    )
    await asyncio.sleep(1)
    await umm.delete()
    owner=await app.get_users(OWNER_ID)
    await m.reply_photo(
        PING_IMG_URL,
        caption=f"""<blockquote>» ʜᴇʏ, ɪ ᴀᴍ {app.mention}
   ━━━━━━━━━━━━━━━━━━━
  » ᴍʏ ᴏᴡɴᴇʀ : {owner.mention()}
  
  » ʟɪʙʀᴀʀʏ ᴠᴇʀsɪᴏɴ : {lver}
  
  » ᴛᴇʟᴇᴛʜᴏɴ ᴠᴇʀsɪᴏɴ : {tver}
  
  » ᴘʏʀᴏɢʀᴀᴍ ᴠᴇʀsɪᴏɴ : {pver}
  
  » ᴘʏᴛʜᴏɴ ᴠᴇʀsɪᴏɴ : {pyver()}
  
  » ᴘʏ-ᴛɢᴄᴀʟʟꜱ ᴠᴇʀꜱɪᴏɴ : {pytver}
   ━━━━━━━━━━━━━━━━━━━</blockquote>""",
        reply_markup=InlineKeyboardMarkup(Xteam)
    )
