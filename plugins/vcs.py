# Nama File: joincall.py

from . import *
from telethon import functions, types
from telethon.tl.types import InputGroupCall, DataJSON, InputPeerEmpty, InputPeerChat, InputPeerChannel
from telethon.errors import (
    GroupcallAddParticipantsFailedError,
    GroupcallSsrcDuplicateMuchError,
    GroupCallNotFoundError # Tambahkan error yang mungkin terjadi
)

# Sesuaikan dengan prefiks perintah Anda jika bukan '.'
@ultroid_cmd(pattern="joincall(?: |$)(.*)")
async def join_group_call_cmd(event):
    """
    Bergabung ke Panggilan Grup.
    Contoh Penggunaan: .joincall <call_id> <access_hash> <join_as_id_atau_username> <params_json> [muted|unmuted] [video_stopped|video_on] [invite_hash]
    CATATAN: Fungsi ini membutuhkan Data JSON WebRTC (params) yang valid untuk koneksi penuh.
    """
    if event.fwd_from:
        return

    # Ambil argumen dari perintah
    args = event.pattern_match.group(1).split()
    
    if len(args) < 4:
        await event.edit(
            "**Penggunaan:** `.joincall <call_id> <access_hash> <join_as_id_atau_username> <params_json> [muted|unmuted] [video_stopped|video_on] [invite_hash]`\n"
            "**Contoh:** `.joincall 12345 67890 @join_entity '{\"data\": \"webrtc_payload\"}' muted video_stopped`"
        )
        return

    try:
        call_id = int(args[0])
        call_access_hash = int(args[1])
        join_as_peer_str = args[2]
        params_json = args[3]
        
        # Optional Arguments
        muted = True
        video_stopped = True
        invite_hash = None
        
        # Parse optional arguments
        if len(args) > 4:
            muted = args[4].lower() == 'muted'
        if len(args) > 5:
            video_stopped = args[5].lower() == 'video_stopped'
        if len(args) > 6:
            invite_hash = args[6]

        await event.edit("Memproses... Mendapatkan entitas...")

        # Dapatkan entitas untuk join_as
        try:
            join_as_peer = await event.client.get_input_entity(join_as_peer_str)
        except Exception:
            await event.edit("⚠️ Tidak dapat menemukan entitas `join_as` yang valid.")
            return

        # Buat objek TypeInputGroupCall dan TypeDataJSON
        input_call = InputGroupCall(
            id=call_id, 
            access_hash=call_access_hash
        )
        input_params = DataJSON(data=params_json)

        await event.edit(f"Mencoba bergabung ke Panggilan Grup (ID: `{call_id}`)...")

        # Panggil fungsi Telethon
        result = await event.client(
            functions.phone.JoinGroupCallRequest(
                call=input_call,
                join_as=join_as_peer,
                params=input_params,
                muted=muted,
                video_stopped=video_stopped,
                invite_hash=invite_hash,
            )
        )

        # Proses hasil
        await event.edit("✅ Berhasil mengirim permintaan bergabung ke Panggilan Grup.")
        # Anda bisa menampilkan detail hasil, misalnya:
        # await event.edit(f"✅ Berhasil bergabung!\n**Updates:** ```{result.stringify()}```")

    except GroupCallNotFoundError:
        await event.edit("❌ Panggilan Grup tidak ditemukan atau sudah berakhir.")
    except GroupcallAddParticipantsFailedError:
        await event.edit("❌ Gagal menambahkan partisipan (mungkin tidak ada izin).")
    except GroupcallSsrcDuplicateMuchError:
        await event.edit("❌ Error SSRC. Coba lagi dengan SSRC baru.")
    except ValueError:
        await event.edit("❌ Masukkan `call_id` dan `access_hash` sebagai angka.")
    except Exception as e:
        await event.edit(f"❌ Terjadi kesalahan: `{e}`")

