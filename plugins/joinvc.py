from xteam.vcbot import * 
from xteam import call_py
from . import ultroid_cmd, eor as edit_or_reply, eod as edit_delete
from telethon.errors.rpcerrorlist import UserAlreadyParticipantError

@ultroid_cmd(pattern="joinvc", group_only=True)
async def join_voice_chat(event):
    chat_id = event.chat_id
    
    try:
        if await call_py.get_group_call(chat_id):
            return await edit_delete(event, "**Bot sudah berada di Obrolan Suara.**", time=10)
    except Exception:
        pass

    try:
        await join_call(chat_id) 
        

        await edit_or_reply(event, "Berhasil bergabung ke Obrolan")

    except UserAlreadyParticipantError:
        await edit_delete(event, "**Bot sudah berada di Obrolan Suara.**", time=10)
    except Exception as e:
        await edit_delete(event, f"**Gagal bergabung ke VC:** `{e}`", time=20)


@ultroid_cmd(pattern="leavevc", group_only=True)
async def leave_voice_chat(event):
    chat_id = event.chat_id

    try:
        await call_py.leave_call(chat_id)
        
        
        await edit_or_reply(event, "**Bot telah meninggalkan Obrolan Suara.**")
    
    except Exception:
        await edit_delete(event, "**Bot tidak sedang berada di Obrolan Suara.**", time=10)
      
