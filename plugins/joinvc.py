from xteam.vcbot import *
from . import ultroid_cmd, eor as edit_or_reply, eod as edit_delete
from telethon.errors.rpcerrorlist import UserAlreadyParticipantError

@ultroid_cmd(pattern="joinvc", group_only=True)
async def join_voice_chat(event):
    chat_id = event.chat_id
    
    try:
        await event.client.join_group_call(
            chat_id 
        ) 

        await edit_or_reply(event, "**Berhasil bergabung ke Obrolan Suara!** (Akun Utama)")

    except UserAlreadyParticipantError:
        await edit_delete(event, "**Akun Utama sudah berada di Obrolan Suara.**", time=10)
    except Exception as e:
        await edit_delete(event, f"**Gagal bergabung ke VC (Akun Utama):** `{e}`", time=20)


@ultroid_cmd(pattern="leavevc", group_only=True)
async def leave_voice_chat(event):
    chat_id = event.chat_id

    try:
        await event.client.leave_group_call(chat_id)
        
        await edit_or_reply(event, "**Akun Utama telah meninggalkan Obrolan Suara.**")
    
    except Exception:
        await edit_delete(event, "**Akun Utama tidak sedang berada di Obrolan Suara.**", time=10)
        
