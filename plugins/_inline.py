# Ultroid - UserBot
# Copyright (C) 2021-2023 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.

import re
import time
from datetime import datetime
from os import remove
import resources
from git import Repo
from telethon import Button
from telethon.tl.types import InputWebDocument, Message
from telethon.utils import resolve_bot_file_id
from assistant import *
from xteam._misc._assistant import callback, in_pattern
from xteam.dB._core import HELP, LIST
from xteam.fns.helper import gen_chlog, time_formatter, updater
from xteam.fns.misc import split_list
from . import OWNER_ID
from . import (
    HNDLR,
    LOGS,
    OWNER_NAME,
    InlinePlugin,
    asst,
    get_string,
    inline_pic,
    split_list,
    start_time,
    udB,
ultroid_cmd,
)
from ._help import _main_help_menu

# ================================================#

helps = get_string("inline_1")

add_ons = udB.get_key("ADDONS")
PREFIX = udB.get_key("HNDLR")

zhelps = get_string("inline_3") if add_ons is False else get_string("inline_2")
PLUGINS = HELP.get("Official", [])
ADDONS = HELP.get("Addons", [])
upage = 0
# ============================================#

# --------------------BUTTONS--------------------#

SUP_BUTTONS = [
    [
        Button.url("• Repo •", url="https://github.com/xteam-cloner/Userbotx"),
    ],
]

PING_BUTTONS = [
    [
        Button.inline("🏡 Modules 🏡", data="uh_Official_"),
    ],

]
# --------------------BUTTONS--------------------#


@in_pattern("repo",owner=False)
async def inline_alive(o):
    TLINK = inline_pic() or "https://telegra.ph/file/cad7038fe82e47f79c609.jpg"
    MSG = "**What are you looking for?**"
    WEB0 = InputWebDocument(
        "https://telegra.ph/file/cad7038fe82e47f79c609.jpg", 0, "image/jpg", []
    )
    RES = [
        await o.builder.article(
            type="photo",
            text=MSG,
            include_media=True,
            buttons=SUP_BUTTONS,
            title="Userbot",
            description="Userbot",
            url=TLINK,
            thumb=WEB0,
            content=InputWebDocument(TLINK, 0, "image/jpg", []),
        )
    ]
    await o.answer(
        RES,
        private=True,
        cache_time=300,
        switch_pm="xteam-userbot",
        switch_pm_param="start",
    )

@in_pattern("ultd", owner=True)
async def inline_handler(event):
    z = []
    for x in LIST.values():
        z.extend(x)
    text = get_string("inline_4").format(
        OWNER_NAME,
        PREFIX,
        len(HELP.get("Official", [])),
        len(HELP.get("Addons", [])),
        len(z),
    )
    if inline_pic():
        result = await event.builder.photo(
            file=inline_pic(),
            link_preview=False,
            text=text,
            buttons=_main_help_menu,
        )
    else:
        result = await event.builder.article(
            title="Ultroid Help Menu", text=text, buttons=_main_help_menu
        )
    await event.answer([result], private=True, cache_time=300, gallery=True)
    

@in_pattern("helper", owner=False)
async def inline_handler(ult):
    key = "Official"
    count = 0
    text = get_string("inline_4", key).format(
        len(HELP.get("Official", [])),
        len(HELP.get("Addons", [])),
        len(key),
        PREFIX,
    )
    result = await ult.builder.article(
        title="Menu Help", text=text, buttons=page_num(count, key)
    )
    await ult.answer([result], cache_time=0)


@in_pattern("help", owner=False)
async def inline_handler(ult):
    key = "Official"
    count = 0  
    official_count = len(HELP.get("Official", []))
    addon_count = len(HELP.get("Addons", []))
    total_modules = official_count + addon_count 
    prefix_to_display = PREFIX 
    if prefix_to_display is None or prefix_to_display == "NO_HNDLR" or prefix_to_display == "":
        prefix_to_display = "None"     
    text = get_string("inline_4", key).format(
        prefix_to_display,
        total_modules
    ) 
    result = await ult.builder.article(
        title="Menu Help", text=text, buttons=page_num(count, key)
    )
    await ult.answer([result], cache_time=0)


@in_pattern("pasta", owner=True)
async def _(event):
    ok = event.text.split("-")[1]
    link = f"https://spaceb.in/{ok}"
    raw = f"https://spaceb.in/api/v1/documents/{ok}/raw"
    result = await event.builder.article(
        title="Paste",
        text="Pasted to Spacebin 🌌",
        buttons=[
            [
                Button.url("SpaceBin", url=link),
                Button.url("Raw", url=raw),
            ],
        ],
    )
    await event.answer([result])


@callback("ownr", owner=False)
async def setting(event):
    z = []
    for x in LIST.values():
        z.extend(x)
    await event.edit(
        get_string("inline_4").format(
            len(HELP.get("Official", [])),
            len(HELP.get("Addons", [])),
            len(z),
        ),
        file=inline_pic(),
        link_preview=False,
        buttons=[
            [
                Button.inline("🏡 Modules 🏡", data="uh_Official_")
            ],
        ],
    )


_strings = {"Official": helps, "Addons": zhelps, "VCBot": get_string("inline_6")}

@callback(re.compile("uh_(.*)"), owner=False)
async def help_func(ult):
    key, count = ult.data_match.group(1).decode("utf-8").split("_")
    if key == "VCBot" and HELP.get("VCBot") is None:
        return await ult.answer(get_string("help_12"), alert=True)
    elif key == "Addons" and HELP.get("Addons") is None:
        return await ult.answer(get_string("help_13").format(HNDLR), alert=True)
    if "|" in count:
        _, count = count.split("|")
    count = int(count) if count else 0
    text = _strings.get(key, "").format(OWNER_NAME, len(HELP.get(key)))
    await ult.edit(text, buttons=page_num(count, key), link_preview=False)


@callback(re.compile("uplugin_(.*)"), owner=False)
async def uptd_plugin(ult):
    key, file = ult.data_match.group(1).decode("utf-8").split("_")
    index = None
    if "|" in file:
        file, index = file.split("|")
    key_ = HELP.get(key, [])
    hel_p = f"Plugin Name - `{file}`\n"
    help_ = ""
    try:
        for i in key_[file]:
            help_ += i
    except BaseException:
        if file in LIST:
            help_ = get_string("help_11").format(file)
            for d in LIST[file]:
                help_ += "" + d
                help_ += "\n"
    if not help_:
        help_ = f"{file} has no Detailed Help!"
    help_ += "\n© @xteam_cloner"
    buttons = []
    if inline_pic():
        data = f"sndplug_{key}_{file}"
        if index is not None:
            data += f"|{index}"
        buttons.append(
            [
                Button.inline(
                    "« Sᴇɴᴅ Pʟᴜɢɪɴ »",
                    data=data,
                )
            ]
        )
    data = f"uh_{key}_"
    if index is not None:
        data += f"|{index}"
    buttons.append(
        [
            Button.inline("<<", data=data),
        ]
    )
    try:
        await ult.edit(help_, buttons=buttons)
    except Exception as er:
        LOGS.exception(er)
        help = f"Do `{HNDLR}help {key}` to get list of commands."
        await ult.edit(help, buttons=buttons)


@callback(data="doupdate", owner=True)
async def _(event):
    if not await updater():
        return await event.answer(get_string("inline_9"), cache_time=0, alert=True)
    if not inline_pic():
        return await event.answer(f"Do '{HNDLR}update' to update..")
    repo = Repo.init()
    changelog, tl_chnglog = await gen_chlog(
        repo, f"HEAD..upstream/{repo.active_branch}"
    )
    changelog_str = changelog + "\n\n" + get_string("inline_8")
    if len(changelog_str) > 1024:
        await event.edit(get_string("upd_4"))
        with open("ultroid_updates.txt", "w+") as file:
            file.write(tl_chnglog)
        await event.edit(
            get_string("upd_5"),
            file="ultroid_updates.txt",
            buttons=[
                [Button.inline("• Uᴘᴅᴀᴛᴇ Nᴏᴡ •", data="updatenow")],
                [Button.inline("<<", data="ownr")],
            ],
        )
        remove("ultroid_updates.txt")
    else:
        await event.edit(
            changelog_str,
            buttons=[
                [Button.inline("Update Now", data="updatenow")],
                [Button.inline("<<", data="ownr")],
            ],
            parse_mode="html",
        )


@callback(data="pkng", owner=True)
async def _(event):
    start = datetime.now()
    end = datetime.now()
    ms = (end - start).microseconds
    pin = f"🌋Pɪɴɢ = {ms} ms"
    await event.answer(pin, cache_time=0, alert=True)


@callback(data="upp", owner=True)
async def _(event):
    uptime = time_formatter((time.time() - start_time) * 1000)
    pin = f"🙋Uᴘᴛɪᴍᴇ = {uptime}"
    await event.answer(pin, cache_time=0, alert=True)


@callback(data="inlone", owner=True)
async def _(e):
    _InButtons = [
        Button.switch_inline(_, query=InlinePlugin[_], same_peer=True)
        for _ in list(InlinePlugin.keys())
    ]
    InButtons = split_list(_InButtons, 2)

    button = InButtons.copy()
    button.append(
        [
            Button.inline("<<", data="open"),
        ],
    )
    await e.edit(buttons=button, link_preview=False)


@callback(data="pmclose")
async def pmclose(event):
    await event.delete()

def page_num(index, key):
    rows = udB.get_key("HELP_ROWS") or 5
    cols = udB.get_key("HELP_COLUMNS") or 2
    loaded = HELP.get(key, [])
    emoji = udB.get_key("EMOJI_IN_HELP") or ""
    List = [
        Button.inline(f"{emoji} {x} {emoji}", data=f"uplugin_{key}_{x}|{index}")
        for x in sorted(loaded)
    ]
    all_ = split_list(List, cols)
    fl_ = split_list(all_, rows)
    try:
        new_ = fl_[index]
    except IndexError:
        new_ = fl_[0] if fl_ else []
        index = 0

    nav_buttons = []
    if len(fl_) > 1:
        nav_buttons.append(
            Button.inline(
                "<",
                data=f"uh_{key}_{index-1}",
            )
        )
    nav_buttons.append(Button.inline("×", data="pkng"))
    if len(fl_) > 1:
        nav_buttons.append(
            Button.inline(
                ">",
                data=f"uh_{key}_{index+1}",
            )
        )

    if nav_buttons:
        new_.append(nav_buttons)
    elif not new_:  # Tambahkan tombol close jika tidak ada tombol lain dan tidak ada item bantuan
        new_.append([Button.inline("×", data="upp")])

    return new_


@callback("closeit")
async def closet(lol):
    try:
        await lol.delete()
    except MessageDeleteForbiddenError:
        await lol.answer("MESSAGE_TOO_OLD", alert=True)
# --------------------------------------------------------------------------------- #


STUFF = {}


@in_pattern("stf(.*)", owner=True)
async def ibuild(e):
    n = e.pattern_match.group(1).strip()
    builder = e.builder
    if not (n and n.isdigit()):
        return
    ok = STUFF.get(int(n))
    txt = ok.get("msg")
    pic = ok.get("media")
    btn = ok.get("button")
    if not (pic or txt):
        txt = "Hey!"
    if pic:
        try:
            include_media = True
            mime_type, _pic = None, None
            cont, results = None, None
            try:
                ext = str(pic).split(".")[-1].lower()
            except BaseException:
                ext = None
            if ext in ["img", "jpg", "png"]:
                _type = "photo"
                mime_type = "image/jpg"
            elif ext in ["mp4", "mkv", "gif"]:
                mime_type = "video/mp4"
                _type = "gif"
            else:
                try:
                    if "telethon.tl.types" in str(type(pic)):
                        _pic = pic
                    else:
                        _pic = resolve_bot_file_id(pic)
                except BaseException:
                    pass
                if _pic:
                    results = [
                        await builder.document(
                            _pic,
                            title="Ultroid Op",
                            text=txt,
                            description="@TeamUltroid",
                            buttons=btn,
                            link_preview=False,
                        )
                    ]
                else:
                    _type = "article"
                    include_media = False
            if not results:
                if include_media:
                    cont = InputWebDocument(pic, 0, mime_type, [])
                results = [
                    await builder.article(
                        title="Ultroid Op",
                        type=_type,
                        text=txt,
                        description="@TeamUltroid",
                        include_media=include_media,
                        buttons=btn,
                        thumb=cont,
                        content=cont,
                        link_preview=False,
                    )
                ]
            return await e.answer(results)
        except Exception as er:
            LOGS.exception(er)
    result = [
        await builder.article("Ultroid Op", text=txt, link_preview=False, buttons=btn)
    ]
    await e.answer(result)


async def something(e, msg, media, button, reply=True, chat=None):
    if e.client._bot:
        return await e.reply(msg, file=media, buttons=button)
    num = len(STUFF) + 1
    STUFF.update({num: {"msg": msg, "media": media, "button": button}})
    try:
        res = await e.client.inline_query(asst.me.username, f"stf{num}")
        return await res[0].click(
            chat or e.chat_id,
            reply_to=bool(isinstance(e, Message) and reply),
            hide_via=True,
            silent=True,
        )

    except Exception as er:
        LOGS.exception(er)


#--------------------------------------

import time 

# Asumsi fungsi time_formatter, udB, dan class Button sudah diimpor/didefinisikan
# Asumsi start_time dan OWNER_ID sudah didefinisikan

def ping_buttons():
    # Mengganti tombol refresh dengan tombol tutup/hapus
    #close_data = "closeit" 
    return [[Button.inline("🏡", data="ultd")]]

async def get_ping_message_and_buttons(client): # Parameter latency_ms dihapus
    
    # --- KODE BARU UNTUK MENGUKUR PING ---
    start_time_ping = time.time()
    await client.get_me() # Mengirim permintaan ringan ke server untuk mengukur latency
    latency_ms = round((time.time() - start_time_ping) * 100)
    # --- AKHIR KODE PENGUKURAN PING ---
    
    uptime = time_formatter((time.time() - start_time) * 100)
    
    # end sekarang menggunakan hasil pengukuran latency_ms
    end = latency_ms # Nilai 50 default dihilangkan
    ping_label = "Ping"
    
    owner_entity = await client.get_entity(OWNER_ID)
    owner_name = owner_entity.first_name 
    
    emoji_ping_html = (str(udB.get_key("EMOJI_PING")) if udB.get_key("EMOJI_PING") else "🏓") + " "
    emoji_uptime_html = (str(udB.get_key("EMOJI_UPTIME")) if udB.get_key("EMOJI_UPTIME") else "⏰") + " "
    emoji_owner_html = (str(udB.get_key("EMOJI_OWNER")) if udB.get_key("EMOJI_OWNER") else "👑") + " "
    
    bot_header_text = "<b><a href='https://github.com/xteam-cloner/xteam-urbot'>𖤓⋆xᴛᴇᴀᴍ ᴜʀʙᴏᴛ⋆𖤓</a></b>" 
    owner_html_mention = f"<a href='tg://user?id={OWNER_ID}'>{owner_name}</a>"
    display_name = f"OWNER : {owner_html_mention} | UB" # Menambahkan '| UB' agar sesuai gambar
    
    ping_message = f"""
<blockquote>
<b>{bot_header_text}</b></blockquote>
<blockquote>{emoji_ping_html} {ping_label} : {end}ms
{emoji_uptime_html} Uptime : {uptime}
{emoji_owner_html} {display_name}
</blockquote>
"""
    
    return ping_message, ping_buttons()
    

@in_pattern("ping", owner=False) 
async def inline_ping_handler(ult):
    
    ping_message, buttons = await get_ping_message_and_buttons(ult.client)
    pic = udB.get_key("PING_PIC")
        
    result = await ult.builder.article(
        title="Bot Status", 
        text=ping_message, 
        buttons=PING_BUTTONS, 
        link_preview=bool(pic),
        parse_mode="html"
    )
    
    await ult.answer([result], cache_time=0)

@callback("closeit")
async def closet(lol):
    # Coba hapus
    try:
        await lol.delete()
    except Exception as e:
        # Jika gagal, tampilkan notifikasi error umum (tanpa pesan "too old" spesifik)
        # dan cetak error-nya ke konsol untuk debugging
        print(f"Gagal menghapus pesan: {e}") 
        await lol.answer("Gagal menghapus pesan. Periksa izin bot.", alert=True) 

# --- Handler Perintah Chat (/ping) ---
# Menggunakan asst.me.username seperti pada kode /help
@ultroid_cmd(pattern="ping(|x|s)$", chats=[], type=["official", "assistant"])
async def _(event):
    client = event.client 
    
    try:
        # 1. Lakukan inline query
        # CATATAN: Menggunakan asst.me.username seperti di kode /help
        results = await client.inline_query(asst.me.username, "ping")
        
        # 2. Kirim hasil inline query yang pertama (indeks [0]) ke chat
        if results:
            # Menggunakan .click() mirip dengan /help untuk mengirimkan hasil inline
            # event.reply_to_msg_id mungkin perlu diganti dengan event.id jika ingin membalas pesan /ping
            await results[0].click(
                event.chat_id, 
                reply_to=event.id, # Menggunakan event.id untuk membalas pesan perintah
                hide_via=True
            )
            # Hapus pesan perintah asli jika berhasil (opsional)
            await event.delete() 
        else:
            await event.reply("❌ Gagal mendapatkan hasil status bot melalui inline query. Tidak ada hasil ditemukan.")

    except Exception as e:
        print(f"Error saat menjalankan ping command: {e}")
        await event.reply(f"Terjadi kesalahan saat memanggil inline ping: `{type(e).__name__}: {e}`")
        

@in_pattern("alive", owner=False)
async def inline_alive_handler(ult):
    # Hitung uptime (asumsi 'start_time' global tersedia)
    try:
        uptime = time_formatter((time.time() - start_time) * 1000)
    except NameError:
        uptime = "N/A (Define start_time)" 
        
    message_text = format_message_text(uptime)
    
    # Logika untuk menentukan gambar (tetap sama)
    xpic = udB.get_key("ALIVE_PIC")
    xnone = ["false", "0", "none"] 
    xdefault = "resources/extras/IMG_20251027_112615_198.jpg"
    
    pic = None
    if xpic and str(xpic).lower() in xnone:
        pic = None    
    elif xpic and str(xpic).lower() in ["true", "1"]:
        pic = xdefault
    elif xpic:
        pic = xpic  
    else:
        pic = xdefault
        
    # Membangun artikel inline, sekarang menyertakan tombol
    result = await ult.builder.article(
        title="Userbot Alive", 
        text=message_text, 
        description=f"Uptime: {uptime}", 
        buttons=PING_BUTTONS, # <-- **TAMBAHAN PENTING DI SINI**
        thumb=pic if pic else None
    )
    
    # Menjawab inline query
    await ult.answer([result], cache_time=0)

# Catatan: Pastikan Anda juga mengimpor 'Button' dari library yang sesuai (misalnya, telethon.tl.custom)
