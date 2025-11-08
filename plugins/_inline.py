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
from platform import python_version as pyver
from pyrogram import __version__ as pver
from xteam.version import __version__
from xteam.version import ultroid_version
from telegram import __version__ as lver
from telethon import __version__ as tver
from pytgcalls import __version__ as pytver
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
from .alive import format_message_text
import asyncio

from . import *
from asyncio import sleep
from telethon.errors import FloodWaitError
from . import udB, NOSPAM_CHAT as noU

udB.del_key("USPAM")

active_spam_tasks = {} 

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

ALIVE_BUTTONS = [
    [
        Button.inline("🏡 PING 🏡", data="ping"),
    ],

]

SPAM_DELAY = 1.5 # Jeda antar pesan spam (dalam detik)

# Variabel Global/Konstanta yang digunakan
noU = [-1001212184059, -1001451324102] # Daftar chat terlarang (asumsi dari kode 2 asli)

SPAM_BUTTONS = [
    [
        Button.inline("🔴 Mulai Spam", data="spam_start"),
        Button.inline("⏹️ Hentikan Spam", data="spam_stop")
    ],
    [
        Button.inline("🔄 Uptime Bot", data="alive_btn")
    ]
]

active_spam_tasks = {} 

# --- FUNGSI UTAMA LOOP SPAM (Background Task) ---
# Mengambil logika loop dari command uspam asli
async def run_unlimited_spam(client, chat_id, text_spam):
    
    while udB.get_key("USPAM", False):
        try:
            # Menggunakan client.send_message (karena ult.respond hanya ada di handler)
            await client.send_message(chat_id, text_spam)
            
            # Wajib: Jeda sebentar agar tidak langsung FloodWait
            await asyncio.sleep(1) 
            
        except FloodWaitError as fw:
            # Logika FloodWait dari kode asli Anda
            udB.del_key("USPAM")
            await client.send_message(chat_id, f"Spam dihentikan karena FloodWait. Tunggu {fw.seconds} detik.")
            break 
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"ERROR SAAT SPAM di {chat_id}: {e}")
            break
            
    # Cleanup task setelah loop berakhir
    if chat_id in active_spam_tasks:
        del active_spam_tasks[chat_id]
        
    # Pastikan status DB terhapus
    udB.del_key("USPAM")
    
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
    nav_buttons.append(Button.inline("🏡", data="alive_btn"))
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
        new_.append([Button.inline("🏡", data="alive_btn")])

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
#------------------------------------------------------    
@ultroid_cmd(pattern="ping$")
async def _(event):
    client = event.client     
    try:
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


#--------------------------------------------

@ultroid_cmd(pattern="alive$")
async def alive(event):
    client = event.client
    
    # Nilai "alive" digunakan secara langsung
    
    try:
        # Menggunakan "alive" untuk inline query
        results = await client.inline_query(asst.me.username, "aliv")
        
        if results:
            await results[0].click(
                event.chat_id, 
                reply_to=event.id, 
                hide_via=True
            )
            
            await event.delete() 
            
        else:
            await event.reply(f"❌ Gagal mendapatkan status **alive** melalui inline query. Tidak ada hasil ditemukan.")

    except Exception as e:
        print(f"Error saat menjalankan alive command (inline): {e}")
        await event.reply(f"Terjadi kesalahan saat memanggil inline **alive**: `{type(e).__name__}: {e}`")
        


@in_pattern("aliv", owner=False)
async def inline_alive_query_handler(ult):
    # Hitung uptime (gunakan blok try/except yang lebih aman)
    try:
        # Masih perlu memastikan time_formatter dan start_time tidak None!
        uptime = time_formatter((time.time() - start_time) * 1000) 
        # Panggil fungsi-fungsi berisiko di sini dan simpan hasilnya
        # current_python_version = pyver() # Contoh
    except NameError:
        uptime = "N/A" 
        
    # Asumsikan format_message_text sudah Anda gabungkan atau dipindahkan ke __init__.py
    message_text = format_message_text(uptime) # Ganti dengan logika yang sudah diperbaiki

    
    # --- Panggilan article ---
    result = await ult.builder.article(
        text=message_text, 
        buttons=ALIVE_BUTTONS,
        title="✰ xᴛᴇᴀᴍ ᴜʀʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ ✰", 
        description=f"Uptime: {uptime}",
        parse_mode="html",
    )
    
    # Menjawab inline query (Seperti yang Anda inginkan di kode awal)
    await ult.answer([result], cache_time=0)

import re
import time
# Asumsikan impor lain seperti time_formatter, start_time, format_message_text, ALIVE_BUTTONS, 
# get_string, _strings, OWNER_NAME, HELP, page_num, dll. sudah tersedia.

# Mengganti @in_pattern dengan dekorator callback dan pola regex baru
# Pola ini akan mencocokkan 'alive_btn' diikuti oleh data apa pun (group 1)
@callback(re.compile("alive_btn(.*)"), owner=False)
async def callback_alive_handler(ult):
    
    # Meniru cara Kode 2 mengambil data: key, count = ult.data_match.group(1).decode("utf-8").split("_")
    # Di sini, kita asumsikan 'ult.data_match.group(1)' berisi data tambahan, jika ada
    # Jika tidak ada, kita bisa mengosongkannya.
    
    # Ambil data yang cocok dari regex group 1.
    match_data = ult.data_match.group(1).decode("utf-8") if ult.data_match.group(1) else ""
    
    # --- LOGIKA KODE 1 DIMODIFIKASI UNTUK CALLBACK ---
    
    # Hitung uptime 
    try:
        # Masih perlu memastikan time_formatter dan start_time tidak None!
        uptime = time_formatter((time.time() - start_time) * 1000) 
    except NameError:
        uptime = "N/A" 
        
    # Asumsikan format_message_text sudah Anda gabungkan
    message_text = format_message_text(uptime) 

    
    # --- Tindakan Callback (Edit Message) ---
    # Di callback handler, kita biasanya mengedit pesan yang sudah ada, 
    # bukan mengirim artikel inline baru.
    
    # Meniru ult.edit dari Kode 2:
    await ult.edit(
        message_text, 
        buttons=ALIVE_BUTTONS, # Gunakan tombol ALIVE_BUTTONS yang sudah ada
        link_preview=False,
        parse_mode="html"
    )
    
    # Opsional: Menjawab callback query (pop-up atau notifikasi)
    await ult.answer(f"Status ALIVE diperbarui. Uptime: {uptime}", alert=False)

#---------------------------------------------

import asyncio
from telethon.errors import FloodWaitError
# Asumsikan 'ultroid_cmd', 'asst', dan modul lain sudah diimpor

@ultroid_cmd(pattern="spammenu$", fullsudo=True) 
async def send_spam_menu(ult):
    
    eris = await ult.eor("⏳ Mengambil menu kontrol spam...")
    
    try:
        results = await asst.inline_query(asst.me.username, "spammenu")
        
        if results:
            await results[0].click(
                ult.chat_id,         
                reply_to=ult.id,     
                hide_via=True
            )
            
            await ult.delete() 
            
        else:
            await eris.edit("❌ Gagal mendapatkan menu kontrol spam melalui inline query. Tidak ada hasil ditemukan.")

    except Exception as e:
        print(f"Error saat menjalankan spammenu command (inline): {e}")
        await eris.edit(f"Terjadi kesalahan saat memanggil inline spam menu: `{type(e).__name__}: {e}`")


@in_pattern("spammenu", owner=False)
async def spam_menu_inline_handler(ult):
    
    # --- LOGIKA ISI PESAN ---
    
    # PERBAIKAN: Menggunakan get_key tanpa nilai default di argumen
    # dan menerapkan default value (False) secara eksternal.
    # Jika udB.get_key("USPAM") adalah None/False/dll., maka False yang akan digunakan.
    is_spamming = udB.get_key("USPAM") or False 
    
    message_text = "**Kontrol Unlimited Spam (via Callback)**\n\n"
    
    if is_spamming:
        message_text += "Status: 🟢 **AKTIF**"
        description_text = "Status: AKTIF"
    else:
        message_text += "Status: 🔴 **TIDAK AKTIF**"
        description_text = "Status: TIDAK AKTIF"
        
    # PERBAIKAN: Menggunakan get_key tanpa nilai default di argumen
    # dan menerapkan default value secara eksternal.
    spam_text = udB.get_key("DEFAULT_SPAM_TEXT") or "Spam Ulang Alik! 🚀"
    message_text += f"\nTeks Spam: `{spam_text}`"
    
    # --- Mengembalikan Inline Result (MENGGANTIKAN SEMUA ult.eor) ---
    await ult.answer(
        results=[
            await ult.builder.article(
                title="⚙️ Menu Kontrol Spam",
                text=message_text,
                description=description_text,
                buttons=SPAM_BUTTONS, 
                parse_mode="markdown"
            )
        ]
    )
    

@callback("spam_start", owner=False) # <--- DIUBAH!
async def spam_start_handler(ult):
    chat_id = ult.chat_id
    
    await ult.answer("Memproses aksi: START...", alert=False)
    
    # Cek chat terlarang
    noU_list = [-1001212184059, -1001451324102] 
    if ult.chat_id in noU_list:
        await ult.answer("Tidak diizinkan di chat ini!", alert=True)
        return
        
    if chat_id in active_spam_tasks:
        await ult.answer("Spam sudah AKTIF di chat ini!", alert=True)
        return

    # Ambil teks spam 
    input_text = udB.get_key("DEFAULT_SPAM_TEXT", "Spam Ulang Alik! 🚀")
    
    # 1. Set Status
    udB.set_key("USPAM", True)
    
    # 2. **JALANKAN BACKGROUND TASK** (Non-blocking)
    task = asyncio.create_task(run_unlimited_spam(ult.client, chat_id, input_text))
    active_spam_tasks[chat_id] = task 
    
    # 3. Berikan Feedback dan HAPUS TOMBOL
    await ult.edit(
        "**Spam dimulai.** Status diatur ke AKTIF.\n"
        f"Teks Spam: `{input_text}`",
        buttons=None, 
        link_preview=False,
        parse_mode="markdown"
    )


@callback("spam_stop", owner=False) # <--- DIUBAH!
async def spam_stop_handler(ult):
    chat_id = ult.chat_id
    
    await ult.answer("Memproses aksi: STOP...", alert=False)
    
    # 1. Hentikan task jika ada
    if chat_id in active_spam_tasks:
        active_spam_tasks[chat_id].cancel()
        
    # 2. Hentikan spam (Hapus Status di DB)
    udB.del_key("USPAM")
    
    # 3. Berikan Feedback dan HAPUS TOMBOL
    await ult.edit(
        "**Spam dihentikan.** Status diatur ke TIDAK AKTIF.",
        buttons=None, 
        link_preview=False,
        parse_mode="markdown"
    )
