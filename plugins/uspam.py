# < Source - t.me/testingpluginnn >
# < https://github.com/TeamUltroid/Ultroid >

"""
✘ Unlimited SPAM!

•  **your account might get limited or banned!**
•  **use on your own risk !**

• **CMD:**
>  `{i}uspam <text>`
>  `{i}stopuspam`  ->  To stop spam.
"""

from asyncio import sleep
from telethon.errors import FloodWaitError

from . import udB, NOSPAM_CHAT as noU


udB.del_key("USPAM")

@ultroid_cmd(
    pattern="uspam(?: |$)((?:.|\n)*)",
    fullsudo=True,
)
async def uspam(ult):
    eris = await ult.eor("...")
    input = ult.pattern_match.group(1)
    if not input:
        return await eod(eris, "`Give some text as well..`")

    # ult-spam and testingplug
    noU.extend([-1001212184059, -1001451324102])
    if ult.chat_id in noU:
        return await eris.edit("**I don't feel so good right now**")

    await eris.delete()
    udB.set_key("USPAM", True)
    while bool(udB.get_key("USPAM")):
        try:
            await ult.respond(str(input))
        except FloodWaitError as fw:
            udB.del_key("USPAM")
            await sleep(fw.seconds)
            return


@ultroid_cmd(pattern="s(top)?uspam$")
async def stopuspam(e):
    udB.del_key("USPAM")
    await e.eor("Unlimited spam stopped")
  
