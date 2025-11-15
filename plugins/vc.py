from . import *
from telethon.tl import functions, types
from telethon.tl.functions.phone import (
    JoinGroupCallRequest, LeaveGroupCallRequest
)
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import FloodWaitError, UserNotParticipantError
from telethon.errors.rpcerrorlist import GroupcallSsrcDuplicateMuchError # Diperlukan untuk SSRC error
import logging
import json
import random # Diperlukan untuk SSRC acak

# --- HELPER FUNCTION: MENGATASI NAME ERROR DAN KONVERSI ---

def _raise_cast_fail(entity, target_type):
    """Raises a ValueError when entity casting fails (pengganti InvalidArgumentError)."""
    # Menggunakan ValueError yang dapat diakses daripada InvalidArgumentError
    raise ValueError(
        f'Could not convert {type(entity).__name__} to {target_type}.'
    )

def get_input_group_call(call):
    """Mendapatkan InputGroupCall dari objek panggilan."""
    
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
    await event.eor("`Mencoba bergabung ke Voice Chat...`")
    
    # Logika Retry untuk SSRC
    max_retries = 3
    retries = 0

    while retries < max_retries:
        try:
            # 1. Dapatkan objek Group Call menggunakan GetFullChannelRequest
            full_info = await client(GetFullChannelRequest(target_peer))
            active_call = full_info.full_chat.call 
            
            if not active_call:
                 return await event.eor("`❌ Tidak ada Voice Chat yang aktif di grup ini.`")
            
            # 2. Konversi objek GroupCall menjadi InputGroupCall
            my_call_input = get_input_group_call(active_call)
            
            join_as = await client.get_input_entity("me") 
            
            # GENERATE SSRC ACAK BARU UNTUK MENGHINDARI DUPLIKAT
            ssrc_value = random.getrandbits(32)
            json_data = json.dumps({"ssrc": ssrc_value})
            media_params = types.DataJSON(data=json_data) 
            
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
            
            await event.eor(f"`✅ Berhasil bergabung ke Voice Chat (SSRC: {ssrc_value})!`")
            return # Keluar dari loop dan fungsi jika berhasil

        # TANGANI KESALAHAN SSRC DUPLIKAT KHUSUS
        except GroupcallSsrcDuplicateMuchError:
            retries += 1
            logging.warning(f"SSRC conflict detected. Retrying with new SSRC ({retries}/{max_retries}).")
            await event.edit(f"`⚠️ SSRC bentrok. Mencoba lagi ({retries}/{max_retries})...`")
            # Loop akan berjalan kembali dan menghasilkan SSRC baru
            
        # TANGANI ERROR LAINNYA
        except ValueError as e:
            await event.eor(f"**❌ Gagal Konversi Objek!**\n`Kesalahan: {e}`")
            return
        except (UserNotParticipantError, FloodWaitError) as e:
            await event.eor(f"**❌ Gagal!** Bot tidak memiliki akses atau sedang dibatasi. `{e}`")
            return
        except Exception as e:
            logging.exception("Error during joinvc")
            await event.eor(f"**❌ Gagal bergabung!**\n`Kesalahan: {type(e).__name__}: {e}`")
            return

    # Jika loop selesai tanpa berhasil bergabung
    await event.eor(f"**❌ Gagal bergabung!** Melebihi batas percobaan SSRC ({max_retries} kali).")


# --- Perintah: .leavevc ---
@ultroid_cmd(pattern="leavevc$")
async def leave_voice_chat_in_current_chat(event):
    """Meninggalkan VC aktif di grup saat ini."""
    client = event.client
    target_peer = await client.get_input_entity(event.to_id)
    await event.eor("`Mencoba meninggalkan Voice Chat...`")
    
    try:
        # 1. Dapatkan objek Group Call
        full_info = await client(GetFullChannelRequest(target_peer))
        active_call = full_info.full_chat.call
        
        if not active_call:
             return await event.eor("`❌ Tidak ada Voice Chat yang aktif di grup ini untuk ditinggalkan.`")
        
        # 2. Konversi objek ke InputGroupCall
        my_call_input = get_input_group_call(active_call)
        
        source_id = 0 
        
        # 3. Panggil LeaveGroupCallRequest secara langsung
        await client(
            LeaveGroupCallRequest(
                call=my_call_input, 
                source=source_id
            )
        )
        
        await event.eor(f"`👋 Berhasil meninggalkan Voice Chat di grup ini!`")

    except ValueError as e:
        await event.eor(f"**❌ Gagal Konversi Objek!**\n`Kesalahan: {e}`")
    except Exception as e:
        logging.exception("Error during leavevc")
        await event.eor(f"**❌ Gagal meninggalkan VC!**\n`Kesalahan: {type(e).__name__}: {e}`")
        
