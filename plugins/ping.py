import asyncio
import os
import sys
import time
import random
import datetime 
from telethon.errors import FloodWaitError
from telethon import Button
from telethon import events, TelegramClient
from telethon.tl.types import (
    InputMessagesFilterVideo,
    InputMessagesFilterVoice,
    InputMessagesFilterPhotos,
)
from . import (
    ultroid_bot,  
    client,       
    clients,      
    start_time,
    udB,
    OWNER_ID,
    OWNER_NAME,
    OWNER_USERNAME,
    time_formatter,
    ultroid_cmd as xteam_cmd,
    get_string,
    eor,
    call_back,
    callback,
)
from xteam._misc import SUDO_M, owner_and_sudos, sudoers
from xteam.fns.custom_markdown import CustomMarkdown
from xteam.fns.helper import download_file, inline_mention
from ._inline import *


async def mention_user(user_id):
    try:
        user_entity = await ultroid_bot.get_entity(user_id)
        first_name = user_entity.first_name
        mention_text = f"[{first_name}](tg://user?id={user_id})"
        return mention_text
    except Exception as e:
        print(f"Failed to mention user: {e}")
        return str(user_id)


async def test_additional_clients(clients_list):
    results = {}
    for c in clients_list:
        try:
            start = time.time()
            temp_msg = await c.send_message("me", "ping_test", schedule=datetime.timedelta(days=1))
            end = round((time.time() - start) * 1000)
            
            await c.delete_messages("me", [temp_msg.id])

            user_entity = await c.get_me()
            user_info = f"@{user_entity.username}" if user_entity.username else user_entity.first_name or f"ID {user_entity.id}"
            
            results[user_info] = f"{end}ms"
        except Exception as e:
            user_info = c.session.get_entity_string().split(':')[0]
            results[user_info] = f"❌ Error ({e.__class__.__name__})"
            
    return results


@xteam_cmd(pattern="ping(|x|s)$", chats=[], type=["official", "assistant"])
async def consolidated_ping(event):
    
    ultroid_bot.parse_mode = "html" 
    user_id = event.sender_id
    prem = event.pattern_match.group(1)
    
    start = time.time()
    x = await event.reply("ping")
    end = round((time.time() - start) * 1000)
    uptime = time_formatter(time.time() - start_time) 
    
    if prem == "x":
        await x.edit(get_string("pping").format(end, uptime))
        return
        
    elif prem == "s":
        await x.edit(get_string("iping").format(end))
        return

    is_owner = user_id == OWNER_ID
    is_full_sudo = user_id in SUDO_M.fullsudos 
    is_standard_sudo = user_id in sudoers()

    if is_owner:
        user_role = "OWNER"
        owner_html_mention = f"<a href='tg://user?id={OWNER_ID}'>{OWNER_NAME}</a>"
        display_name = f"👑 {user_role} : {owner_html_mention}" 
        
    elif is_full_sudo or is_standard_sudo:
        current_user_entity = await client.get_entity(user_id)
        current_user_name = current_user_entity.first_name or current_user_entity.title
        user_role = "FULLSUDO" if is_full_sudo else "SUDOUSER"
        user_html_mention = f"<a href='tg://user?id={user_id}'>{current_user_name}</a>"
        display_name = f"⚡️ {user_role} : {user_html_mention}"
        
    else:
        owner_html_mention = f"<a href='tg://user?id={OWNER_ID}'>{OWNER_NAME}</a>"
        display_name = f"👤 User : {owner_html_mention}" 

    pic = udB.get_key("PING_PIC")
    emoji_ping_base = udB.get_key("EMOJI_PING"); emoji_ping_html = (str(emoji_ping_base) if emoji_ping_base else "🏓") + " "
    emoji_uptime_base = udB.get_key("EMOJI_UPTIME"); emoji_uptime_html = (str(emoji_uptime_base) if emoji_uptime_base else "⏰") + " "
    
    bot_header_text = "<b><a href='https://github.com/xteam-cloner/xteam-urbot'>𖤓⋆xᴛᴇᴀᴍ ᴜʀʙᴏᴛ⋆𖤓</a></b>" 
    
    additional_client_results = ""
    if clients: 
        additional_ping_data = await test_additional_clients(clients)
        
        additional_client_results += "\n\n<b>⚡️ Multi-Client Latency:</b>\n"
        for user_info, latency in additional_ping_data.items():
            additional_client_results += f"  • <code>{user_info}</code>: <b>{latency}</b>\n"
    
    ping_message = f"""
<blockquote>
<b>{bot_header_text}</b></blockquote>
<blockquote>{emoji_ping_html} Ping : <b>{end}ms</b>
{emoji_uptime_html} Uptime : {uptime}
{display_name}
{additional_client_results}</blockquote>
"""
        
    await asyncio.sleep(0.5)
    await x.edit(ping_message, file=pic, parse_mode='html')
    
