# Ultroid - UserBot
# Copyright (C) 2021-2023 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.
"""
✘ Commands Available -

•`{i}addnsfw <ban/mute/kick>`
   If someone sends 18+ content it will be deleted and action will be taken.

•`{i}detect`
   Detect nsfw.
•`{i}remnsfw`
   Remove Chat from nsfw filtering.
"""

import os
import requests
from . import LOGS

try:
    from ProfanityDetector import detector
except ImportError:
    detector = None
    LOGS.error("nsfwfilter: 'Profanitydetector' not installed!")
from xteam.dB.nsfw_db import is_nsfw, nsfw_chat, rem_nsfw

from . import HNDLR, async_searcher, eor, events, udB, ultroid_bot, ultroid_cmd


@ultroid_cmd(pattern="addnsfw( (.*)|$)", admins_only=True)
async def addnsfw(e):
    if not udB.get_key("DEEP_API"):
        return await eor(
            e, f"Get Api from deepai.org and Add It `{HNDLR}setdb DEEP_API your-api`"
        )
    action = e.pattern_match.group(1).strip()
    if not action or ("ban" or "kick" or "mute") not in action:
        action = "mute"
    nsfw_chat(e.chat_id, action)
    ultroid_bot.add_handler(nsfw_check, events.NewMessage(incoming=True))
    await e.eor("Added This Chat To Nsfw Filter")


@ultroid_cmd(pattern="remnsfw", admins_only=True)
async def remnsfw(e):
    rem_nsfw(e.chat_id)
    await e.eor("Removed This Chat from Nsfw Filter.")


NWARN = {}


async def nsfw_check(e):
    chat = e.chat_id
    action = is_nsfw(chat)
    if action and udB.get_key("DEEP_API") and e.media:
        pic, name, nsfw = "", "", 0
        try:
            pic = await e.download_media(thumb=-1)
        except BaseException:
            pass
        if e.file:
            name = e.file.name
        if detector and name:
            x, y = detector(name)
            if y:
                nsfw += 1
        if pic and not nsfw:
            r = await async_searcher(
                "https://api.deepai.org/api/nsfw-detector",
                data={
                    "image": open(pic, "rb"),
                },
                post=True,
                re_json=True,
                headers={"api-key": udB.get_key("DEEP_API")},
            )
            try:
                k = float((r["output"]["nsfw_score"]))
            except KeyError as er:
                LOGS.exception(er)
                LOGS.info(r)
                return
            score = int(k * 100)
            if score > 45:
                nsfw += 1
            os.remove(pic)
        if nsfw:
            await e.delete()
            if NWARN.get(e.sender_id):
                count = NWARN[e.sender_id] + 1
                if count < 3:
                    NWARN.update({e.sender_id: count})
                    return await ultroid_bot.send_message(
                        chat,
                        f"**NSFW Warn {count}/3** To [{e.sender.first_name}](tg://user?id={e.sender_id})\nNSFW prohibited! Repeated violation would lead to {action}",
                    )
                if "mute" in action:
                    try:
                        await ultroid_bot.edit_permissions(
                            chat, e.sender_id, until_date=None, send_messages=False
                        )
                        await ultroid_bot.send_message(
                            chat,
                            f"NSFW Warn 3/3 to [{e.sender.first_name}](tg://user?id={e.sender_id})\n\n**Action Taken** : {action}",
                        )
                    except BaseException:
                        await ultroid_bot.send_message(
                            chat,
                            f"NSFW Warn 3/3 to [{e.sender.first_name}](tg://user?id={e.sender_id})\n\nUnable to {action}.",
                        )
                elif "ban" in action:
                    try:
                        await ultroid_bot.edit_permissions(
                            chat, e.sender_id, view_messages=False
                        )
                        await ultroid_bot.send_message(
                            chat,
                            f"NSFW Warn 3/3 to [{e.sender.first_name}](tg://user?id={e.sender_id})\n\n**Action Taken** : {action}",
                        )
                    except BaseException:
                        await ultroid_bot.send_message(
                            chat,
                            f"NSFW Warn 3/3 to [{e.sender.first_name}](tg://user?id={e.sender_id})\n\nUnable to {action}.",
                        )
                elif "kick" in action:
                    try:
                        await ultroid_bot.kick_participant(chat, e.sender_id)
                        await ultroid_bot.send_message(
                            chat,
                            f"NSFW Warn 3/3 to [{e.sender.first_name}](tg://user?id={e.sender_id})\n\n**Action Taken** : {action}",
                        )
                    except BaseException:
                        await ultroid_bot.send_message(
                            chat,
                            f"NSFW Warn 3/3 to [{e.sender.first_name}](tg://user?id={e.sender_id})\n\nUnable to {action}.",
                        )
                NWARN.pop(e.sender_id)
            else:
                NWARN.update({e.sender_id: 1})
                return await ultroid_bot.send_message(
                    chat,
                    f"**NSFW Warn 1/3** To [{e.sender.first_name}](tg://user?id={e.sender_id})\nNSFW prohibited! Repeated violation would lead to {action}",
                )


if udB.get_key("NSFW"):
    ultroid_bot.add_handler(nsfw_check, events.NewMessage(incoming=True))

"""@ultroid_cmd(pattern="detect$", outgoing=True)
async def detect(event):
    if not udB.get_key("DEEP_API"):
        return await eor(
            event, "Add VAR DEEP_AI get Api Key from https://deepai.org/", time=5
        )
    reply = await event.get_reply_message()
    if not reply:
        return await eor(
            event, "Reply to any image or non animated sticker !", time=5
        )
    snku = await eor(event, "Downloading the file to check...")
    media = await event.client.download_media(reply)
    if not media.endswith(("png", "jpg", "webp")):
        return await eor(
            event, "Reply to any image or non animated sticker !", time=5
        )
    snku = await eor(event, "Detecting NSFW limit...")
    r = requests.post(
        "https://api.deepai.org/api/nsfw-detector",
        files={
            "image": open(media, "rb"),
        },
        headers={"api-key": udB.get_key("DEEP_API")},
    )
    os.remove(media)
    if "status" in r.json():
        return await eor(snku, r.json()["status"])
    r_json = r.json()["output"]
    pic_id = r.json()["id"]
    percentage = r_json["nsfw_score"] * 100
    detections = r_json["detections"]
    link = f"https://api.deepai.org/job-view-file/{pic_id}/inputs/image.jpg"
    result = f"<b>Detected Nudity :</b>\n<a href='{link}'>>>></a> <code>{percentage:.3f}%</code>\n\n"
    if detections:
        for parts in detections:
            name = parts["name"]
            confidence = int(float(parts["confidence"]) * 100)
            result += f"<b>• {name}:</b>\n   <code>{confidence} %</code>\n"
    await eor(
        snku, result
    )
"""
