import asyncio
import os

from telethon.errors.rpcerrorlist import ChatAdminRequiredError, FloodWaitError
from telethon.tl.functions.channels import EditAdminRequest
from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
from telethon.tl.types import ChatAdminRights, User

from xteam.dB import DEVLIST
from xteam.dB.base import KeyManager
from xteam.dB.gban_mute_db import (
    gban,
    gmute,
    is_gbanned,
    is_gmuted,
    list_gbanned,
    ungban,
    ungmute,
)
from xteam.fns.tools import create_tl_btn, format_btn, get_msg_button

from . import (
    HNDLR,
    LOGS,
    NOSPAM_CHAT,
    OWNER_NAME,
    eod,
    eor,
    get_string,
    inline_mention,
    ultroid_bot,
    ultroid_cmd,
)
from ._inline import something

_gpromote_rights = ChatAdminRights(
    add_admins=False,
    invite_users=True,
    change_info=False,
    ban_users=True,
    delete_messages=True,
    pin_messages=True,
)

_gdemote_rights = ChatAdminRights(
    add_admins=False,
    invite_users=False,
    change_info=False,
    ban_users=False,
    delete_messages=False,
    pin_messages=False,
)

keym = KeyManager("BLACKLIST_GCAST", cast=list)


@ultroid_cmd(pattern="Gcast( (.*)|$)", fullsudo=True)
async def gcast(event):
    text, btn, reply = "", None, None
    if xx := event.pattern_match.group(2):
        msg, btn = get_msg_button(event.text.split(maxsplit=1)[1])
    elif event.is_reply:
        reply = await event.get_reply_message()
        msg = reply.text
        if reply.buttons:
            btn = format_btn(reply.buttons)
        else:
            msg, btn = get_msg_button(msg)
    else:
        return await eor(
            event, "Give some text to Globally Broadcast or reply a message.."
        )

    kk = await event.eor("Globally Broadcasting Msg...")
    er = 0
    done = 0
    err = ""
    if event.client._dialogs:
        dialog = event.client._dialogs
    else:
        dialog = await event.client.get_dialogs()
        event.client._dialogs.extend(dialog)
    for x in dialog:
        if x.is_group:
            chat = x.entity.id
            if (
                not keym.contains(chat)
                and int(f"-100{str(chat)}") not in NOSPAM_CHAT
                and chat not in BLACKLIST_GCAST  # Added blacklist check
                and (
                    (
                        event.text[2:7] != "admin"
                        or (x.entity.admin_rights or x.entity.creator)
                    )
                )
            ):
                try:
                    if btn:
                        bt = create_tl_btn(btn)
                        await something(
                            event,
                            msg,
                            reply.media if reply else None,
                            bt,
                            chat=chat,
                            reply=False,
                        )
                    else:
                        await event.client.send_message(
                            chat, msg, file=reply.media if reply else None
                        )
                    done += 1
                except FloodWaitError as fw:
                    await asyncio.sleep(fw.seconds + 10)
                    try:
                        if btn:
                            bt = create_tl_btn(btn)
                            await something(
                                event,
                                msg,
                                reply.media if reply else None,
                                bt,
                                chat=chat,
                                reply=False,
                            )
                        else:
                            await event.client.send_message(
                                chat, msg, file=reply.media if reply else None
                            )
                        done += 1
                    except Exception as rr:
                        err += f"• {rr}\n"
                        er += 1
                except BaseException as h:
                    err += f"• {str(h)}" + "\n"
                    er += 1
    text += f"Done in {done} chats, error in {er} chat(s)"
    if err != "":
        open("gcast-error.log", "w+").write(err)
        text += f"\nYou can do {HNDLR}ul gcast-error.log to know error report."
    await kk.edit(text)

# --- New functions for managing the gcast blacklist ---

BLACKLIST_GCAST = set()

@ultroid_cmd(pattern="addbl( (.*)|$)", fullsudo=True)
async def add_gblacklist(event):
    chat_id = event.pattern_match.group(1)
    if chat_id not in BLACKLIST_GCAST:
        BLACKLIST_GCAST.add(chat_id)
        await event.edit(f"Chat {chat_id} has been added to the gcast blacklist.")
    else:
        await event.edit(f"Chat {chat_id} is already in the gcast blacklist.")

@ultroid_cmd(pattern="unbl( (.*)|$)", fullsudo=True)
async def remove_gblacklist(event):
    chat_id = event.pattern_match.group(1)
    if chat_id in BLACKLIST_GCAST:
        BLACKLIST_GCAST.remove(chat_id)
        await event.edit(f"Chat {chat_id} has been removed from the gcast blacklist.")
    else:
        await event.edit(f"Chat {chat_id} is not in the gcast blacklist.")
