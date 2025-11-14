# plugins/groupcall_plugin.py

from xteam import *
from telethon.tl import types
from telethon.errors import *
from . import *
# --- PENTING: Impor yang Anda inginkan ---
# Impor ini menjalankan semua kode di methods.py (termasuk setattr)
# dan juga mengimpor objek fungsi mentah.
try:
    from telethonpatch.methods import join_group_call, leave_group_call
except ImportError:
    print("WARNING: Could not import voice call methods from telethonpatch.methods.")

# --- Perintah: .joinvc ---
@ultroid_cmd(pattern="joinvc$")
async def join_voice_chat_in_current_chat(event):
    """Bergabung ke VC aktif di grup saat ini."""
    client = event.client
    
    target_peer = await client.get_input_entity(event.to_id)
    await event.eor("`Mencoba bergabung ke Voice Chat di grup ini...`")
    
    try:
        call_info_result = await client.get_group_call(target_peer, limit=1)
        
        if not hasattr(call_info_result, 'call') or not call_info_result.call:
             return await event.eor("`❌ Tidak ada Voice Chat yang aktif di grup ini.`")
        
        my_call_input = call_info_result.call
        
        join_as = await client.get_input_entity("me") 
        media_params = types.DataJSON(data='{}') 
        
        # Panggil client.join_group_call yang sudah di-patch
        await client.join_group_call(
            call=my_call_input,
            join_as=join_as,
            params=media_params,
            muted=False,
            video_stopped=True
        )
        
        await event.eor(f"`✅ Berhasil bergabung ke Voice Chat di grup ini!`")

    except Exception as e:
        await event.eor(f"**❌ Gagal bergabung!**\n`Kesalahan: {type(e).__name__}: {e}`")

# --- Perintah: .leavevc ---
@ultroid_cmd(pattern="leavevc$")
async def leave_voice_chat_in_current_chat(event):
    """Meninggalkan VC aktif di grup saat ini."""
    client = event.client
    
    target_peer = await client.get_input_entity(event.to_id)

    await event.eor("`Mencoba meninggalkan Voice Chat...`")
    
    try:
        call_info_result = await client.get_group_call(target_peer, limit=1)
        
        if not hasattr(call_info_result, 'call') or not call_info_result.call:
             return await event.eor("`❌ Tidak ada Voice Chat yang aktif di grup ini untuk ditinggalkan.`")
        
        my_call_input = call_info_result.call
        
        source_id = 0 
        
        # Panggil client.leave_group_call yang sudah di-patch
        await client.leave_group_call(
            call=my_call_input,
            source=source_id
        )
        
        await event.eor(f"`👋 Berhasil meninggalkan Voice Chat di grup ini!`")

    except Exception as e:
        await event.eor(f"**❌ Gagal meninggalkan VC!**\n`Kesalahan: {type(e).__name__}: {e}`")
