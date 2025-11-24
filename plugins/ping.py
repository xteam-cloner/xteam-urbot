import asyncio
import os
import sys
import time
import random
import datetime 
from datetime import timedelta
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
    devs,
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
        mention_text = f"<a href='tg://user?id={user_id}'>{first_name}</a>"
        return mention_text
    except Exception as e:
        print(f"Failed to mention user: {e}")
        return str(user_id)


async def get_client_display_data(cl, client_count=0):
    user_info_display = f"Client {client_count}"
    user_id = None
    try:
        user_entity = await cl.get_me()
        user_id = user_entity.id
        user_info_display = user_entity.first_name or user_entity.title or f"Client {client_count}"
        
        if client_count == 1 and user_info_display == "Client 1":
            user_info_display = "ᴄᴀᴛʜ ᴀꜱꜱɪꜱᴛᴀɴᴛꜱ"
            
        mention = await mention_user(user_id)
        return user_info_display, mention, user_id
    except Exception:
        return user_info_display, user_info_display, user_id


async def test_additional_clients(clients_list):
    results = {}
    client_count = 1 
    for c in clients_list:
        user_info_display, user_mention, user_id = await get_client_display_data(c, client_count)
        
        try:
            start = time.time()
            temp_msg = await c.send_message("me", "ping_test", schedule=timedelta(days=1))
            end = round((time.time() - start) * 1000)
            
            await c.delete_messages("me", [temp_msg.id])

            ping_text = f"🏓  Ping : <b>{end}ms</b>\n⏰  Uptime : {time_formatter(time.time() - start_time)}\n👑 OWNER : {user_mention}"
            
            results[user_info_display] = ping_text
        except Exception as e:
            error_text = f"❌ Error ({e.__class__.__name__})"
            results[user_info_display] = error_text
        
        client_count += 1
            
    return results


@xteam_cmd(pattern="ping$", chats=[], type=["official"])
async def consolidated_ping(event):
    
    ultroid_bot.parse_mode = "html" 
    user_id = event.sender_id
    
    # Menetapkan nama/mention Klien Utama secara manual
    main_client_display_name = "ᴊɪʏᴏ ᴠx | ᴜʙ"
    main_client_mention = f"<a href='tg://user?id={OWNER_ID}'>{main_client_display_name}</a>" 

    bot_header_text = "𖤓⋆xᴛᴇᴀᴍ ᴜʀʙᴏᴛ⋆𖤓"

    x = await event.reply("ping...") 
    
    start = time.time()
    try:
        temp_msg = await client.send_message("me", "main_ping_test", schedule=timedelta(days=1))
        end = round((time.time() - start) * 1000)
        await client.delete_messages("me", [temp_msg.id])
    except Exception:
        end = "Err"
        
    uptime = time_formatter(time.time() - start_time) 
    
    
    # 1. PESAN KLIEN UTAMA (Menggunakan mention yang diset secara manual)
    main_client_message = f"""
<b>{main_client_display_name}</b>
**{bot_header_text}**
<blockquote>🏓  Ping : <b>{end}ms</b>
⏰  Uptime : {uptime}
👑 OWNER : {main_client_mention}</blockquote>
"""
    
    
    # 2. KLIEN TAMBAHAN (Menggunakan mention dari test_additional_clients)
    if clients: 
        additional_ping_data = await test_additional_clients(clients)
        
        for user_info, detail_text in additional_ping_data.items():
            
            
            additional_client_message = f"""
<b>{user_info}</b>
**{bot_header_text}**
<blockquote>{detail_text}</blockquote>
"""
            
            await client.send_message(
                event.chat_id,
                additional_client_message,
                reply_to=event.id, 
                parse_mode='html'
            )

    
    
    await asyncio.sleep(0.5)
    await x.edit(main_client_message, parse_mode='html')
