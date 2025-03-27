import asyncio
import inspect
import io
import os
import platform
import re
import socket
import sys
import traceback
import uuid
from html import escape
from sys import version as pyver
from typing import Any, Optional, Tuple

import psutil
from meval import meval
from ntgcalls import __version__ as ntgver
from pyrogram import __version__ as pyrover
from pytdbot import VERSION as py_td_ver
from pytdbot import types, Client
from pytgcalls import __version__ as pytgver

from config import OWNER_ID
from src.database import db
from src.logger import LOGGER
from src.modules.utils import Filter
from src.modules.utils.play_helpers import del_msg


def format_exception(
        exp: BaseException, tb: Optional[list[traceback.FrameSummary]] = None
) -> str:
    """Formats an exception traceback as a string, similar to the Python interpreter."""

    if tb is None:
        tb = traceback.extract_tb(exp.__traceback__)

    # Replace absolute paths with relative paths
    cwd = os.getcwd()
    for frame in tb:
        if cwd in frame.filename:
            frame.filename = os.path.relpath(frame.filename)

    stack = "".join(traceback.format_list(tb))
    msg = str(exp)
    if msg:
        msg = f": {msg}"

    return f"Traceback (most recent call last):\n{stack}{type(exp).__name__}{msg}"


@Client.on_message(Filter.command("eval"))
async def exec_eval(c: Client, m: types.Message):
    if int(m.from_id) != OWNER_ID:
        return None

    text = m.text.split(None, 1)
    if len(text) <= 1:
        return await m.reply_text("Usage: /eval &lt code &gt")

    code = text[1]
    out_buf = io.StringIO()

    async def _eval() -> Tuple[str, Optional[str]]:
        async def send(*args: Any, **kwargs: Any) -> types.Message:
            return await m.reply_text(*args, **kwargs)

        def _print(*args: Any, **kwargs: Any) -> None:
            if "file" not in kwargs:
                kwargs["file"] = out_buf
                return print(*args, **kwargs)

        eval_vars = {
            "loop": c.loop,
            "client": c,
            "stdout": out_buf,
            "c": c,
            "m": m,
            "msg": m,
            "types": types,
            "send": send,
            "print": _print,
            "inspect": inspect,
            "os": os,
            "re": re,
            "sys": sys,
            "traceback": traceback,
            "uuid": uuid,
            "io": io,
        }

        try:
            return "", await meval(code, globals(), **eval_vars)
        except Exception as e:
            first_snip_idx = -1
            tb = traceback.extract_tb(e.__traceback__)
            for i, frame in enumerate(tb):
                if frame.filename == "<string>" or frame.filename.endswith("ast.py"):
                    first_snip_idx = i
                    break

            # Re-raise exception if it wasn't caused by the snippet
            if first_snip_idx == -1:
                raise e

            # Return formatted stripped traceback
            stripped_tb = tb[first_snip_idx:]
            formatted_tb = format_exception(e, tb=stripped_tb)
            return "⚠️ Error:\n\n", formatted_tb

    prefix, result = await _eval()

    if not out_buf.getvalue() or result is not None:
        print(result, file=out_buf)

    out = out_buf.getvalue()
    if out.endswith("\n"):
        out = out[:-1]

    result = f"""{prefix}<b>In:</b>
<pre language="python">{escape(code)}</pre>
<b>ᴏᴜᴛ:</b>
<pre language="python">{escape(out)}</pre>"""

    if len(result) > 4096:
        filename = f"/tmp/{uuid.uuid4().hex}.txt"
        with open(filename, "w", encoding="utf-8") as file:
            file.write(out)

        caption = f"""{prefix}<b>ᴇᴠᴀʟ:</b>
    <pre language="python">{escape(code)}</pre>
    """
        await m.reply_document(
            document=types.InputFileLocal(filename),
            caption=caption,
            disable_notification=True,
            parse_mode="html",
        )
        return None

    await m.reply_text(str(result), parse_mode="html")


REQUEST = 10
semaphore = asyncio.Semaphore(REQUEST)


@Client.on_message(Filter.command("broadcast"))
async def broadcast(_: Client, message: types.Message):
    LOGGER.info(f"Broadcast command used by {message.from_id}")
    if int(message.from_id) != OWNER_ID:
        await del_msg(message)
        return None

    all_users: list[int] = await db.get_all_users()
    all_chats: list[int] = await db.get_all_chats()
    if reply := message.reply_to_message_id:
        reply = await message.getRepliedMessage()
        if isinstance(reply, types.Error):
            await message.reply_text(f"Failed to get reply message.{str(reply)}")
            return

    if not reply:
        await message.reply_text("Reply to a message to broadcast it.")
        return

    if not all_users and not all_chats:
        await message.reply_text("No users or chats to broadcast to.")
        return

    async def broadcast_target(target_list, reply_message: types.Message, _semaphore):
        sent, failed = 0, 0
        for target_id in target_list:
            try:
                async with _semaphore:
                    _reply = await reply_message.forward(target_id)
                    if isinstance(_reply, types.Error):
                        if _reply.code == 429:
                            retry_after = _reply.message.split("retry after ")[1]
                            await asyncio.sleep(int(retry_after))
                            _reply = await reply_message.forward(target_id)
                        elif _reply.code == 400:
                            if target_id < 0:
                                await db.remove_chat(target_id)
                            else:
                                await db.remove_user(target_id)
                            failed += 1
                            continue
                        LOGGER.error(f"Failed to send to {target_id}: {_reply}")
                        failed += 1
                        continue
                sent += 1
            except Exception as e:
                LOGGER.error(f"Failed to send to {target_id}: {e}")
                failed += 1
        return sent, failed

    user_sent, user_failed = await broadcast_target(all_users, reply, semaphore)
    await asyncio.sleep(5)
    chat_sent, chat_failed = await broadcast_target(all_chats, reply, semaphore)

    total_sent = user_sent + chat_sent
    total_failed = user_failed + chat_failed

    await message.reply_text(
        f"Broadcast completed:\n"
        f"- Sent: {total_sent} (Users: {user_sent}, Chats: {chat_sent})\n"
        f"- Failed: {total_failed} (Users: {user_failed}, Chats: {chat_failed})"
    )


@Client.on_message(Filter.command("stats"))
async def sys_stats(client: Client, message: types.Message):
    if int(message.from_id) != OWNER_ID:
        await del_msg(message)
        return None

    sysroot = await message.reply_text(
        f"ɢᴇᴛᴛɪɴɢ {client.me.first_name} sʏsᴛᴇᴍ sᴛᴀᴛs, ɪᴛ'ʟʟ ᴛᴀᴋᴇ ᴀ ᴡʜɪʟᴇ..."
    )

    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(socket.gethostname())
    architecture = platform.machine()
    mac_address = ":".join(re.findall("..", "%012x" % uuid.getnode()))
    sp = platform.system()
    ram = f"{str(round(psutil.virtual_memory().total / 1024.0 ** 3))} ɢʙ"
    p_core = psutil.cpu_count(logical=False)
    t_core = psutil.cpu_count(logical=True)

    try:
        cpu_freq = psutil.cpu_freq().current
        if cpu_freq >= 1000:
            cpu_freq = f"{round(cpu_freq / 1000, 2)}ɢʜᴢ"
        else:
            cpu_freq = f"{round(cpu_freq, 2)}ᴍʜᴢ"
    except Exception as e:
        LOGGER.warning(f"Error getting CPU frequency: {e}")
        cpu_freq = "ғᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ"

    hdd = psutil.disk_usage("/")
    total = hdd.total / (1024.0 ** 3)
    used = hdd.used / (1024.0 ** 3)
    free = hdd.free / (1024.0 ** 3)
    platform_release = platform.release()
    platform_version = platform.version()
    chats = len(await db.get_all_chats())
    users = len(await db.get_all_users())

    await sysroot.edit_text(
        f"""
<b><u>{client.me.first_name} sʏsᴛᴇᴍ sᴛᴀᴛs</u></b>

<b>Chats:</b> {chats}
<b>Users:</b> {users}

<b>Python:</b> {pyver.split()[0]}
<b>Pyrogram:</b> {pyrover}
<b>Py-TgCalls:</b> {pytgver}
<b>NTGCalls:</b> {ntgver}
<b>PyTdBot:</b> {py_td_ver}


<b>IP:</b> {ip_address}
<b>MAC:</b> {mac_address}
<b>Hostname:</b> {hostname}
<b>Platform:</b> {sp}
<b>Architecture:</b> {architecture}
<b>Platform Release:</b> {platform_release}
<b>Platform Version:</b> {platform_version}

<b><u>Storage</u></b>
<b>Available:</b> {total:.2f} GiB
<b>Used:</b> {used:.2f} GiB
<b>Free:</b> {free:.2f} GiB

<b>RAM:</b> {ram}
<b>Physical Cores:</b> {p_core}
<b>Total Cores:</b> {t_core}
<b>CPU Frequency:</b> {cpu_freq}""",
        parse_mode="html",
    )


@Client.on_message(Filter.command("json"))
async def _json(_: Client, msg: types.Message) -> None:
    if int(msg.from_id) != OWNER_ID:
        await del_msg(msg)
        return None

    reply = msg.reply_to_message_id
    if reply:
        reply_msg = await msg.getRepliedMessage()
        await msg.reply_text(str(reply_msg))
    await msg.reply_text(str(msg))
