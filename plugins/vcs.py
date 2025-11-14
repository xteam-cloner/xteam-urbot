# plugins/groupcall_plugin.py
# Perbaikan untuk mengatasi TypeError pada join_group_call

from xteam import *
from telethon.tl import types
from telethon.errors import *
import logging # Tambahkan logging untuk debugging
from . import *
# Optional: Impor patch untuk memastikan eksekusi (meskipun Ultroid seharusnya sudah melakukannya)
try:
    from telethonpatch import methods
except ImportError:
    logging.warning("telethonpatch.methods not found. Voice call methods may be missing.")


# --- Perintah: .joinvc ---
@ultroid_cmd(pattern="joinvc$")
async def join_voice_chat_in_current_chat(event):
    """Bergabung ke VC aktif di grup saat ini."""
    client = event.client
    
    target_peer = await client.get_input_entity(event.to_id)
    await event.eor("`Mencoba bergabung ke Voice Chat di grup ini...`")
    
    try:
        # 1. Dapatkan objek Group Call
        # client.get_group_call memerlukan TypeInputPeer
        call_info_result = await client.get_group_call(target_peer, limit=1)
        
        # Periksa apakah ada objek 'call' yang valid
        if not hasattr(call_info_result, 'call') or call_info_result.call is None:
             return await event.eor("`❌ Tidak ada Voice Chat yang aktif di grup ini.`")
        
        my_call_input = call_info_result.call
        
        # KUNCI PERBAIKAN: Pastikan objek call berjenis TypeInputGroupCall
        if not isinstance(my_call_input, types.InputGroupCall):
             # Jika bukan objek TL yang benar, cetak jenis objek untuk debugging
             logging.error(f"Join VC failed: call object is {type(my_call_input)}, expected InputGroupCall")
             return await event.eor(f"`❌ Kesalahan Jenis Objek Panggilan: {type(my_call_input).__name__}`")
        
        join_as = await client.get_input_entity("me") 
        media_params = types.DataJSON(data='{}') 
        
        # 2. Panggil client.join_group_call
        await client.join_group_call(
            call=my_call_input,
            join_as=join_as,
            params=media_params,
            muted=False,
            video_stopped=True
        )
        
        await event.eor(f"`✅ Berhasil bergabung ke Voice Chat di grup ini!`")

    except Exception as e:
        logging.exception("Error during joinvc")
        await event.eor(f"**❌ Gagal bergabung!**\n`Kesalahan: {type(e).__name__}: {e}`")


# --- Perintah: .leavevc ---
@ultroid_cmd(pattern="leavevc$")
async def leave_voice_chat_in_current_chat(event):
    """Meninggalkan VC aktif di grup saat ini."""
    client = event.client
    
    target_peer = await client.get_input_entity(event.to_id)

    await event.eor("`Mencoba meninggalkan Voice Chat...`")
    
    try:
        # 1. Dapatkan objek Group Call
        call_info_result = await client.get_group_call(target_peer, limit=1)
        
        if not hasattr(call_info_result, 'call') or call_info_result.call is None:
             return await event.eor("`❌ Tidak ada Voice Chat yang aktif di grup ini untuk ditinggalkan.`")
        
        my_call_input = call_info_result.call
        
        # KUNCI PERBAIKAN: Pastikan objek call berjenis TypeInputGroupCall
        if not isinstance(my_call_input, types.InputGroupCall):
             logging.error(f"Leave VC failed: call object is {type(my_call_input)}, expected InputGroupCall")
             return await event.eor(f"`❌ Kesalahan Jenis Objek Panggilan: {type(my_call_input).__name__}`")
        
        source_id = 0 
        
        # 2. Panggil client.leave_group_call
        await client.leave_group_call(
            call=my_call_input,
            source=source_id
        )
        
        await event.eor(f"`👋 Berhasil meninggalkan Voice Chat di grup ini!`")

    except Exception as e:
        logging.exception("Error during leavevc")
        await event.eor(f"**❌ Gagal meninggalkan VC!**\n`Kesalahan: {type(e).__name__}: {e}`")
        
