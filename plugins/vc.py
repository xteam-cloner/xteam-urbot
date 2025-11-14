# plugins/groupcall_plugin.py
# Implementasi Join/Leave VC menggunakan TL Request langsung, tanpa patch eksternal.

from xteam import *
from telethon.tl import functions, types
from telethon.tl.functions.phone import (
    JoinGroupCallRequest, LeaveGroupCallRequest, GetGroupCallRequest
)
from telethon.errors import InvalidArgumentError
import logging
from . import *
# --- HELPER FUNCTION: Konversi GroupCall ke InputGroupCall ---
# Diambil dari kode Anda, dengan penanganan error yang disempurnakan.
def _raise_cast_fail(entity, target_type):
    """Raises an InvalidArgumentError when entity casting fails."""
    raise InvalidArgumentError(
        f'Could not convert {type(entity).__name__} to {target_type}.'
    )

def get_input_group_call(call):
    """Similar to get_input_peer, but for input calls."""
    
    # ID CRC32 untuk pengecekan tipe objek
    INPUT_GROUP_CALL_ID = 0x58611ab1 
    GROUP_CALL_ID = 0x20b4f320        
    
    try:
        if call.SUBCLASS_OF_ID == INPUT_GROUP_CALL_ID:
            return call
        elif call.SUBCLASS_OF_ID == GROUP_CALL_ID:
            return types.InputGroupCall(id=call.id, access_hash=call.access_hash)
        else:
            _raise_cast_fail(call, 'InputGroupCall')

    except AttributeError:
        # Menangkap error jika objek tidak memiliki SUBCLASS_OF_ID
        _raise_cast_fail(call, 'InputGroupCall')
# ------------------------------------------------------------


# --- Perintah: .joinvc ---
@ultroid_cmd(pattern="joinvc$")
async def join_voice_chat_in_current_chat(event):
    """Bergabung ke VC aktif di grup saat ini."""
    client = event.client
    
    target_peer = await client.get_input_entity(event.to_id)
    await event.eor("`Mencoba bergabung ke Voice Chat di grup ini...`")
    
    try:
        # 1. Dapatkan objek Group Call menggunakan TL Request langsung
        # Note: GetGroupCallRequest menerima TypeInputPeer di argumen 'call'
        call_info_result = await client(GetGroupCallRequest(call=target_peer, limit=1))
        
        if not hasattr(call_info_result, 'call') or call_info_result.call is None:
             return await event.eor("`❌ Tidak ada Voice Chat yang aktif di grup ini.`")
        
        my_call_input = call_info_result.call
        
        # 2. Konversi objek ke InputGroupCall (Mencegah TypeError)
        my_call_input = get_input_group_call(my_call_input)
        
        join_as = await client.get_input_entity("me") 
        media_params = types.DataJSON(data='{}') 
        
        # 3. Panggil JoinGroupCallRequest secara langsung
        await client(
            JoinGroupCallRequest(
                call=my_call_input,
                join_as=join_as,
                params=media_params,
                muted=False,
                video_stopped=True
            )
        )
        
        await event.eor(f"`✅ Berhasil bergabung ke Voice Chat di grup ini!`")

    except InvalidArgumentError as e:
        await event.eor(f"**❌ Gagal Konversi!**\n`Kesalahan: {e}`")
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
        call_info_result = await client(GetGroupCallRequest(call=target_peer, limit=1))
        
        if not hasattr(call_info_result, 'call') or call_info_result.call is None:
             return await event.eor("`❌ Tidak ada Voice Chat yang aktif di grup ini untuk ditinggalkan.`")
        
        my_call_input = call_info_result.call
        
        # 2. Konversi objek ke InputGroupCall (Mencegah TypeError)
        my_call_input = get_input_group_call(my_call_input)
        
        source_id = 0 
        
        # 3. Panggil LeaveGroupCallRequest secara langsung
        await client(
            LeaveGroupCallRequest(
                call=my_call_input, 
                source=source_id
            )
        )
        
        await event.eor(f"`👋 Berhasil meninggalkan Voice Chat di grup ini!`")

    except InvalidArgumentError as e:
        await event.eor(f"**❌ Gagal Konversi!**\n`Kesalahan: {e}`")
    except Exception as e:
        logging.exception("Error during leavevc")
        await event.eor(f"**❌ Gagal meninggalkan VC!**\n`Kesalahan: {type(e).__name__}: {e}`")
    
