# Ultroid - UserBot
# Copyright (C) 2021-2023 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.
"""
✘ Commands Available -

• `{i}startvc`
    Start Group Call in a group.

• `{i}stopvc`
    Stop Group Call in a group.

• `{i}vctitle <title>`
    Change the title Group call.

• `{i}vcinvite`
    Invite all members of group in Group Call.
    (You must be joined)

• `{i}joinvc`
    Join an ongoing Group Call.

• `{i}leavevc`
    Leave an ongoing Group Call.
"""

from telethon.tl.functions.channels import GetFullChannelRequest as getchat
from telethon.tl.functions.phone import CreateGroupCallRequest as startvc
from telethon.tl.functions.phone import DiscardGroupCallRequest as stopvc
from telethon.tl.functions.phone import EditGroupCallTitleRequest as settitle
from telethon.tl.functions.phone import GetGroupCallRequest as getvc
from telethon.tl.functions.phone import InviteToGroupCallRequest as invitetovc
from telethon.tl.functions.phone import JoinGroupCallRequest
from telethon.tl.functions.phone import LeaveGroupCallRequest

from . import get_string, ultroid_cmd


async def get_call(event):
    mm = await event.client(getchat(event.chat_id))
    xx = await event.client(getvc(mm.full_chat.call, limit=1))
    return xx.call


def user_list(l, n):
    for i in range(0, len(l), n):
        yield l[i : i + n]


@ultroid_cmd(
    pattern="stopvc$",
    admins_only=True,
    groups_only=True,
)
async def _(e):
    try:
        await e.client(stopvc(await get_call(e)))
        await e.eor(get_string("vct_4"))
    except Exception as ex:
        await e.eor(f"`{ex}`")


@ultroid_cmd(
    pattern="vcinvite$",
    groups_only=True,
)
async def _(e):
    ok = await e.eor(get_string("vct_3"))
    users = []
    z = 0
    async for x in e.client.iter_participants(e.chat_id):
        if not x.bot:
            users.append(x.id)
    hmm = list(user_list(users, 6))
    for p in hmm:
        try:
            await e.client(invitetovc(call=await get_call(e), users=p))
            z += 6
        except BaseException:
            pass
    await ok.edit(get_string("vct_5").format(z))


@ultroid_cmd(
    pattern="startvc$",
    admins_only=True,
    groups_only=True,
)
async def _(e):
    try:
        await e.client(startvc(e.chat_id))
        await e.eor(get_string("vct_1"))
    except Exception as ex:
        await e.eor(f"`{ex}`")


@ultroid_cmd(
    pattern="vctitle(?: |$)(.*)",
    admins_only=True,
    groups_only=True,
)
async def _(e):
    title = e.pattern_match.group(1).strip()
    if not title:
        return await e.eor(get_string("vct_6"), time=5)
    try:
        await e.client(settitle(call=await get_call(e), title=title.strip()))
        await e.eor(get_string("vct_2").format(title))
    except Exception as ex:
        await e.eor(f"`{ex}`")



@ultroid_cmd(
    pattern="joinvc$",
    groups_only=True,
)
async def _(e):
    try:
        call = await get_call(e)
        
        # 'join_as' biasanya adalah ID chat atau channel saat ini.
        # 'params' dapat ditemukan dari objek 'call' yang didapat.
        await e.client(JoinGroupCallRequest(
            call=call,
            join_as=e.chat.id,  # Menggunakan ID chat sebagai entitas yang bergabung
            params=call.params, # Mengambil parameter dari objek panggilan
        ))
        
        await e.eor("`Berhasil bergabung ke Group Call.`")
    except Exception as ex:
        await e.eor(f"`{ex}`")
        

@ultroid_cmd(
    pattern="leavevc$",
    groups_only=True,
)
async def _(e):
    try:
        call = await get_call(e)
        
        # Menggunakan LeaveGroupCallRequest untuk meninggalkan panggilan.
        # Fungsi ini hanya membutuhkan objek 'call' sebagai argumen.
        await e.client(LeaveGroupCallRequest(call=call))
        
        await e.eor("`Berhasil meninggalkan Group Call.`")
    except Exception as ex:
        await e.eor(f"`{ex}`")
