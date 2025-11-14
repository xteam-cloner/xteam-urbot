# plugins/vc.py
# Implementasi Join/Leave VC menggunakan TL Request langsung.

from . import *
from telethon.tl import functions, types
from telethon.tl.functions.phone import (
    JoinGroupCallRequest, LeaveGroupCallRequest
)
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import FloodWaitError, UserNotParticipantError
import logging 

# plugins/vc.py (Hanya bagian yang dimodifikasi)

# ... (Import pyUltroid, types, functions, etc.)
from telethon.errors import FloodWaitError, UserNotParticipantError
# TAMBAHKAN IMPOR INI
from telethon.errors.rpcerrorlist import GroupcallSsrcDuplicateMuchError 
import json
import random
# ...

# --- Perintah: .joinvc ---
@ultroid_cmd(pattern="joinvc$")
async def join_voice_chat_in_current_chat(event):
    """Bergabung ke VC aktif di grup saat ini."""
    client = event.client
    target_peer = await client.get_input_entity(event.to_id)
    await event.eor("`Mencoba bergabung ke Voice Chat...`")
    
    # Inisiasi retry counter
    max_retries = 3
    retries = 0

    while retries < max_retries:
        try:
            # 1. Dapatkan objek Group Call
            full_info = await client(GetFullChannelRequest(target_peer))
            active_call = full_info.full_chat.call 
            
            if not active_call:
                 return await event.eor("`❌ Tidak ada Voice Chat yang aktif di grup ini.`")
            
            my_call_input = get_input_group_call(active_call)
            join_as = await client.get_input_entity("me") 

            # GENERATE SSRC ACAK BARU (nilai 32-bit acak)
            ssrc_value = random.getrandbits(32)
            
            # Buat DataJSON dengan SSRC baru
            json_data = json.dumps({"ssrc": ssrc_value})
            media_params = types.DataJSON(data=json_data) 
            
            # 2. Panggil JoinGroupCallRequest
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
            return # Keluar dari loop jika berhasil

        # TANGANI KESALAHAN SSRC DUPLIKAT KHUSUS
        except GroupcallSsrcDuplicateMuchError:
            retries += 1
            logging.warning(f"SSRC conflict detected. Retrying with new SSRC ({retries}/{max_retries}).")
            await event.edit(f"`⚠️ SSRC bentrok. Mencoba lagi ({retries}/{max_retries})...`")
            # Loop akan berjalan kembali dan menghasilkan SSRC baru
            
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
    await event.eor(f"**❌ Gagal bergabung!** Melebihi batas percobaan SSRC.")
            
