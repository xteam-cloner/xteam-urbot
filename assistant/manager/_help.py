# Ultroid - UserBot
# Copyright (C) 2021-2023 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.

from . import *
from plugins import *

START = """
🪅 **Help Menu** 🪅

✘  /start : Check I am Alive or not.
✘  /help : Get This Message.
✘  /repo : Get Bot's Repo..

🧑‍💻 Join **@TeamUltroid**
"""

ADMINTOOLS = """✘ **AdminTools** ✘

• /pin : Pins the Replied Message
• /pinned : Get Pinned message in chat.
• /unpin : Unpin the Replied message
• /unpin all : Unpin all Pinned Messages.

• /ban (username/id/reply) : Ban the User
• /unban (username/id/reply) : UnBan the User.

• /mute (username/id/reply) : Mute the User.
• /unmute (username/id/reply) : Unmute the User.

• /tban (username/id/reply) (time) : Temporary ban a user
• /tmute (username/id/reply) (time) : temporary Mutes a User.

• /purge (purge messages)

• /setgpic (reply photo) : keep Chat Photo of Group.
• /delgpic : remove current chat Photo."""

UTILITIES = """
✘ ** Utilities ** ✘

• /info (reply/username/id) : get detailed info of user.
• /id : get chat/user id.
• /tr : Translate Languages..
• /q : Create Quotes.

• /paste (reply file/text) : paste content on Spaceb.in
• /meaning (text) : Get Meaning of that Word.
• /google (query) : Search Something on Google..

• /suggest (query/reply) : Creates a Yes / No Poll.
"""

LOCKS = """
✘ ** Locks ** ✘

• /lock (query) : lock particular content in chat.
• /unlock (query) : Unlock some content.

• All Queries
- `msgs` : for messages.
- `inlines` : for inline queries.
- `media` : for all medias.
- `games` : for games.
- `sticker` : for stickers.
- `polls` : for polls.
- `gif` : for gifs.
- `pin` : for pins.
- `changeinfo` : for change info right.
"""

MISC = """
✘  **Misc**  ✘

• /joke : Get Random Jokes.
• /decide : Decide Something..

**✘ Stickertools ✘**
• /kang : add sticker to your pack.
• /listpack : get all of yours pack..
"""

STRINGS = {"Admintools": ADMINTOOLS, "locks": LOCKS, "Utils": UTILITIES, "Misc": MISC}

MNGE = udB.get_key("MNGR_EMOJI") or "•"


def get_buttons():
    BTTS = []
    keys = STRINGS.copy()
    while keys:
        BT = []
        for i in list(keys)[:2]:
            text = f"{MNGE} {i} {MNGE}"
            BT.append(Button.inline(text, f"hlp_{i}"))
            del keys[i]
        BTTS.append(BT)
    url = f"https://t.me/{asst.me.username}?startgroup=true"
    BTTS.append([Button.url("Add me to Group", url)])
    return BTTS


@asst_cmd(pattern="help")
async def helpish(event):
    if not event.is_private:
        url = f"https://t.me/{asst.me.username}?start=start"
        return await event.reply(
            "Contact me in PM for help!", buttons=Button.url("Click me for Help", url)
        )
    if str(event.sender_id) in owner_and_sudos() and (
        udB.get_key("DUAL_MODE") and (udB.get_key("DUAL_HNDLR") == "/")
    ):
        return
    await event.reply(START, buttons=get_buttons())


@callback("mngbtn", owner=True)
async def ehwhshd(e):
    buttons = get_buttons()
    buttons.append([Button.inline("<< Back", "open")])
    await e.edit(buttons=buttons)


@callback("mnghome")
async def home_aja(e):
    await e.edit(START, buttons=get_buttons())


@callback(re.compile("hlp_(.*)"))
async def do_something(event):
    match = event.pattern_match.group(1).strip().decode("utf-8")
    await event.edit(STRINGS[match], buttons=Button.inline("<< Back", "mnghome"))


@asst_cmd(pattern="asping$")
async def assistant_ping(event):
    client = event.client 
    ultroid_bot.parse_mode = "html" 
    user_id = event.sender_id
    start = time.time()
    x = await event.reply("Pong!") 
    end = round((time.time() - start) * 1000)
    uptime = time_formatter((time.time() - start_time) * 1000)
    is_owner = user_id == OWNER_ID
    is_full_sudo = user_id in SUDO_M.fullsudos 
    is_standard_sudo = user_id in sudoers()
    owner_entity = await client.get_entity(OWNER_ID)
    owner_name = owner_entity.first_name 
    pic = udB.get_key("PING_PIC")
    emoji_ping_base = udB.get_key("EMOJI_PING") 
    emoji_ping_html = (str(emoji_ping_base) if emoji_ping_base else "🏓") + " "
    emoji_uptime_base = udB.get_key("EMOJI_UPTIME")
    emoji_uptime_html = (str(emoji_uptime_base) if emoji_uptime_base else "⏰") + " "
    
    emoji_owner_base = udB.get_key("EMOJI_OWNER")
    emoji_owner_html = (str(emoji_owner_base) if emoji_owner_base else "👑") + " "
    
    bot_header_text = "<b><a href='https://github.com/xteam-cloner/xteam-urbot'>𖤓⋆xᴛᴇᴀᴍ ᴜʀʙᴏᴛ⋆𖤓</a></b>" 
    
    if is_full_sudo or is_standard_sudo:
        current_user_entity = await client.get_entity(user_id)
        current_user_name = current_user_entity.first_name or getattr(current_user_entity, 'title', 'User')
        user_html_mention = f"<a href='tg://user?id={user_id}'>{current_user_name}</a>"
    else:
        user_html_mention = f"{owner_name}" 

    owner_html_mention = f"<a href='tg://user?id={OWNER_ID}'>{owner_name}</a>"
    
    if is_owner:
        user_role = "OWNER"
        display_name = f"{user_role} : {owner_html_mention}" 
        
    elif is_full_sudo:
        user_role = "FULLSUDO" 
        display_name = f"{user_role} : {user_html_mention}"
        
    elif is_standard_sudo:
        user_role = "SUDOUSER" 
        display_name = f"{user_role} : {user_html_mention}"
        
    else:
        user_role = ""
        display_name = f"{owner_html_mention}" 
        
    ping_message = f"""
<blockquote>
<b>{bot_header_text}</b></blockquote>
<blockquote>{emoji_ping_html} Ping : {end}ms
{emoji_uptime_html} Uptime : {uptime}
{emoji_owner_html} {display_name}
</blockquote>
"""
        
    await asyncio.sleep(0.5)
    
    await x.edit(ping_message, file=pic, parse_mode='html')
        
