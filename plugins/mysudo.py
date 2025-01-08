from . import eor, SUDO_HNDLR, ultroid_cmd
from os import mkdir, listdir as ls
from pyUltroid.fns.helper import inline_mention
from . import HNDLR, get_string, inline_mention, udB, ultroid_bot, ultroid_cmd, eor, SUDO_HNDLR

@ultroid_cmd(pattern="sur")
async def szudo(e):
  reply = await e.get_reply_message()
  rid = "{}".format(reply.sender_id)
  udB.set_key("SUDOS",list(rid))
  udB.set_key("FULLSUDO",rid)
  name = await e.client.get_entity(int(rid))
  una = name.username
  fn = name.first_name
  ln = name.last_name
  men = inline_mention(name)
  ii = udB.get_key("FULLSUDO")
  await e.reply(f"""**Added** {men} **as FULLSUDO and SUDO User**

First name : {fn}
Last name : {ln}
id : {ii}
username : {una}
HNDLR : {HNDLR}
SUDO_HNDLR : {SUDO_HNDLR}
""")


from pyUltroid._misc import sudoers


@ultroid_cmd(
    pattern="su$",
)
async def _(ult):
    x = await ult.eor("**Adding Sudo or Fullsodo.....**")
    n = udB.get_key("SUDOS") or []
    async for m in ult.client.iter_participants(ult.chat_id):
      if not (m.bot or m.deleted):
        n.append(m.id)

    n = list(set(n))
    udB.set_key('SUDOS', n)
    udB.set_key('FULLSUDO', " ".join(str(i) for i in n))
    reply_to_id = ult.reply_to_msg_id or ult.id
    await x.edit(f"""
<b>List of Sudo and Fullsudo users</b>
<pre>1. All members in this group</pre>

<b>Info</b>
<pre>My <code>HNDLR : {HNDLR}</code>
My <code>SUDO_HNDLR : {SUDO_HNDLR}</code>
</pre>
<b>List of some commands<b>
<pre>1. ping = p
2. alive = a
3. eval = e
4. bash = b
5. sysinfo = sys
6. rename = r
7. web = wb
8. writer = aw
9. uninstall plugins/addons = un
10. load = lo
11. semd = sd
12. added -- sgb, high
13. help = h
14. restart = rs
15. open = op
16. speedtest = sp
17. del = d 
</pre>
""",parse_mode="html")
  
