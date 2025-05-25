# Moon-Userbot - telegram userbot
# Copyright (C) 2020-present Moon Userbot Organization
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.

#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import os
import shutil
import subprocess
import sys
from telethon import TelegramClient, events
from telethon.tl.types import Message
from utils import config

from utils.misc import modules_help, prefix
from utils.scripts import format_exc, ultroid_cmd, import_library
from utils.db import db

import_library("psutil")
import psutil


ALLOWED_HANDLERS = [".", ",", "!", ";", "@", "#"]


@ultroid_cmd(command="musicbot", allow_sudo=True)
async def musicbot(event: events.NewMessage.Event):
    client = event.client
    user = await client.get_me()
    user_id = user.id
    music_handler = db.get("custom.musicbot", "music_handler", "")
    if config.second_session == "":
        return await event.edit("<code>Second session string is not set.</code>")
    if music_handler == "":
        return await event.edit(
            "<b>Music handler is not set.</b>\nYou can set it using <code>.set_mhandler [your handler]</code> command.\nAllowed handlers are <code>. , ! ; @ #</code>"
        )
    if music_handler not in ALLOWED_HANDLERS:
        return await event.edit(
            "<code>Invalid music handler in config, please update.</code>"
        )
    if music_handler == str(prefix):
        return await event.edit(
            "<code>Music handler cannot be the same as main prefix.</code>"
        )
    if shutil.which("termux-setup-storage"):
        return await event.edit("<code>Termux is not supported.</code>")

    try:
        await event.edit("<code>Processing...</code>")
        if (
            not os.path.exists("musicbot")
            or len(event.text.split()) > 1
            and event.text.split()[1] == "re"
        ):
            await event.edit("Setting up music bot...")
            if os.path.exists("musicbot"):
                shutil.rmtree("musicbot")
            subprocess.run(
                ["git", "clone", "https://github.com/The-MoonTg-project/musicbot.git"]
            )
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    "requirements.txt",
                ],
                cwd="musicbot",
            )
            with open("musicbot/config/config.py", "w") as f:
                f.write(f"API_ID: int = {config.api_id}\n")
                f.write(f"API_HASH: str = '{config.api_hash}'\n")
                f.write(f"SESSION_STRING: str = '{config.second_session}'\n")
                f.write(f"PREFIX: str = str('{music_handler}')\n")
                f.write("RPREFIX: str = str('$')\n")
                f.write(f"OWNER_ID: list[int] = [int('{user_id}')]\n")
                f.write("LOG_FILE_NAME: str = 'musicbot.txt'\n")
            return await event.edit("Music bot setup completed.")

        if len(event.text.split()) == 1:
            return await event.edit("Music bot is already set up.")

        if len(event.text.split()) > 1 and event.text.split()[1] in ["on", "start"]:
            music_bot_pid = db.get("custom.musicbot", "music_bot_pid", None)
            if music_bot_pid is None:
                await event.edit("Starting music bot...")
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "-r",
                        "requirements.txt",
                    ],
                    cwd="musicbot",
                )
                music_bot_process = subprocess.Popen(
                    [sys.executable, "-m", "YMusic"], cwd="musicbot"
                )
                await asyncio.sleep(3)
                db.set("custom.musicbot", "music_bot_pid", music_bot_process.pid)
                return await event.edit("Music bot started in the background.")
            return await event.edit("Music bot is already running.")
        elif len(event.text.split()) > 1 and event.text.split()[1] in ["off", "stop"]:
            music_bot_pid = db.get("custom.musicbot", "music_bot_pid", None)
            if music_bot_pid is None:
                return await event.edit(
                    "Music bot is not running. Please turn on musicbot first."
                )
            try:
                music_bot_process = psutil.Process(music_bot_pid)
                music_bot_process.terminate()
                db.remove("custom.musicbot", "music_bot_pid")
            except psutil.NoSuchProcess:
                db.remove("custom.musicbot", "music_bot_pid")
                return await event.edit(
                    "Music bot is not running. Please turn on musicbot first."
                )
            db.remove("custom.musicbot", "music_bot_pid")
            return await event.edit("Music bot stopped.")
        elif len(event.text.split()) > 1 and event.text.split()[1] == "restart":
            music_bot_pid = db.get("custom.musicbot", "music_bot_pid", None)
            if music_bot_pid is None:
                return await event.edit(
                    "Music bot is not running. Please turn on musicbot first."
                )
            try:
                music_bot_process = psutil.Process(music_bot_pid)
                music_bot_process.terminate()
            except psutil.NoSuchProcess:
                pass
            music_bot_process = subprocess.Popen(
                [sys.executable, "-m", "YMusic"], cwd="musicbot"
            )
            await asyncio.sleep(3)
            db.set("custom.musicbot", "music_bot_pid", music_bot_process.pid)
            return await event.edit("Music bot restarted in the background.")
    except Exception as e:
        return await event.edit(format_exc(e))


@ultroid_cmd(command="set_mhandler", allow_sudo=True)
async def set_mhandler(event: events.NewMessage.Event):
    if len(event.text.split()) < 2:
        return await event.edit("Please provide a new music handler.")
    new_handler = event.text.split()[1]
    if new_handler not in ALLOWED_HANDLERS:
        return await event.edit(
            "Invalid music handler provided! \n Allowed handlers: <code>.</code> <code>,</code> <code>!</code> <code>;</code> <code>@</code> <code>#</code>"
        )
    db.set("custom.musicbot", "music_handler", new_handler)
    return await event.edit(f"Music handler set to {new_handler}")
