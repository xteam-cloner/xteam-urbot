from telethon.tl.types import Channel, Chat, User
from . import ultroid_cmd, ultroid_bot 

client = ultroid_bot 

@ultroid_cmd(pattern="totalgroup( (.*)|$)", fullsudo=True)
async def hitung_total_grup_plugin(event):
    await event.edit("🔄 Mulai menghitung semua dialog...")

    total_grup_kecil = 0
    total_supergroup = 0
    total_channel_broadcast = 0
    total_chat_pribadi = 0 
    
    async for dialog in event.client.iter_dialogs(): 
        entity = dialog.entity
        
        if isinstance(entity, User):
            total_chat_pribadi += 1
        elif isinstance(entity, Channel):
            if entity.megagroup:
                total_supergroup += 1
            elif entity.broadcast:
                total_channel_broadcast += 1
        elif isinstance(entity, Chat): 
            total_grup_kecil += 1
            
    total_semua_grup = total_grup_kecil + total_supergroup
    total_grup_channel = total_semua_grup + total_channel_broadcast
    
    output = (
        "<blockquote>📊 Hasil Total Entitas\n"
        "--------------------------------------------------\n"
        f"👤 Total Obrolan Pribadi : {total_chat_pribadi}\n"
        f"👥 Total Group : {total_semua_grup}\n"
        f"📣 Total Channel : {total_channel_broadcast}\n"
        "--------------------------------------------------\n"
        f"✨ TOTAL SELURUH GRUP & CHANNEL: {total_grup_channel} entitas</blockquote>"
    )

    await event.edit(output, parse_mode="html")
