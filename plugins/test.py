import asyncio
import importlib
from datetime import datetime
from dateutil.relativedelta import relativedelta
from telethon import TelegramClient, functions, types, errors
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
from . import ultroid_bot as client 
from . import * # Asumsikan ubot adalah modul A
from telethon import TelegramClient, events, Button
import os
import asyncio



async def need_api(event):
    await event.edit("This function requires API credentials.") #example response. replace with actual logic.

async def payment_userbot(event):
    await event.edit("Payment processing initiated.") #example response. replace with actual logic.

async def bikin_ubot(event):
    await event.edit("Creating a new userbot...") #example response. replace with actual logic.

async def cek_ubot(event):
     await event.respond("Checking userbots...") #example response. replace with actual logic.

async def cek_userbot_expired(event):
    await event.edit("Checking userbot expiration...")#example response. replace with actual logic.

async def tools_userbot(event):
    action = event.data.decode() #get the callback data
    if action == "get_otp":
        await event.edit("Getting OTP...")
    elif action == "get_phone":
        await event.edit("Getting phone number...")
    elif action == "get_faktor":
        await event.edit("Getting 2FA factor...")
    elif action == "ub_deak":
        await event.edit("Deactivating userbot...")
    elif action == "deak_akun":
        await event.edit("Deactivating account...")
    else:
        await event.edit(f"Unknown tool: {action}") #example response. replace with actual logic.

async def hapus_ubot(event):
    await event.edit("Deleting userbot...") #example response. replace with actual logic.

async def next_prev_ubot(event):
    action = event.data.decode()
    if action == "prev_ub":
        await event.edit("Showing previous userbot...")
    elif action == "next_ub":
        await event.edit("Showing next userbot...")
    else:
        await event.edit(f"Unknown navigation: {action}") #example response. replace with actual logic.

from telethon.sessions import StringSession

@client.on(events.CallbackQuery(data="bahan"))
async def handler_bahan(event):
    await need_api(event)

@client.on(events.CallbackQuery(data="bayar_dulu"))
async def handler_bayar_dulu(event):
    await payment_userbot(event)

@client.on(events.CallbackQuery(data="add_ubot"))
async def handler_add_ubot(event):
    await bikin_ubot(event)

@client.on(events.NewMessage(pattern="/getubot"))
async def handler_getubot(event):
    await cek_ubot(event)

@client.on(events.CallbackQuery(data="cek_masa_aktif"))
async def handler_cek_masa_aktif(event):
    await cek_userbot_expired(event)

@client.on(events.CallbackQuery(pattern=r"^(get_otp|get_phone|get_faktor|ub_deak|deak_akun)$"))
async def handler_tools_userbot(event):
    await tools_userbot(event)

@client.on(events.CallbackQuery(data="del_ubot"))
async def handler_del_ubot(event):
    await hapus_ubot(event)

@client.on(events.CallbackQuery(pattern=r"^(prev_ub|next_ub)$"))
async def handler_next_prev_ubot(event):
    await next_prev_ubot(event)


async def need_api(client, callback_query):
    user_id = callback_query.sender_id
    if len(ubot._ubot) > MAX_BOT:
        buttons = [[types.KeyboardButtonCallback("Tutup", data=b"0_cls")]]
        await client.delete_messages(callback_query.chat_id, callback_query.id)
        return await client.send_message(
            user_id,
            f"""
<b>❌ Tidak Membuat Userbot !</b>

<b>📚 Karena Telah Mencapai Yang Telah Di Tentukan : {len(ubot._ubot)}</b>

<b>👮‍♂ Silakan Hubungi Admin . </b>
""",
            parse_mode="html",
            buttons=buttons,
        )
    if user_id not in await get_prem():
        buttons = [
            [types.KeyboardButtonCallback("➡️ Lanjutkan", data=b"bayar_dulu")],
            [types.KeyboardButtonCallback("❌ Batalkan", data=f"home {user_id}".encode())],
        ]
        await client.delete_messages(callback_query.chat_id, callback_query.id)
        return await client.send_message(
            user_id,
            MSG.POLICY(),
            parse_mode="html",
            buttons=buttons,
        )
    else:
        await bikin_ubot(client, callback_query)


async def payment_userbot(client, callback_query):
    user_id = callback_query.sender_id
    buttons = Button.plus_minus(1, user_id)
    await client.delete_messages(callback_query.chat_id, callback_query.id)
    return await client.send_message(
        user_id,
        MSG.TEXT_PAYMENT(30, 30, 1),
        parse_mode="html",
        buttons=buttons,
    )


async def bikin_ubot(client, callback_query):
    user_id = callback_query.sender_id
    try:
        await client.delete_messages(callback_query.chat_id, callback_query.id)
        api_id_msg = await client.send_message(
            user_id,
            (
                "<b>Silahkan masukkan API ID anda.</b>\n"
                "\n<b>Gunakan /cancel untuk Membatalkan Proses Membuat Userbot</b>"
            ),
            parse_mode="html",
        )
        api_id_msg = await client.get_response(user_id, timeout=300)
    except asyncio.TimeoutError:
        return await client.send_message(user_id, "Waktu Telah Habis")
    if await is_cancel(client, api_id_msg.message):
        return
    try:
        api_id = int(api_id_msg.message)
    except ValueError:
        return await client.send_message(user_id, "API ID Haruslah berupa angka.")
    await client.delete_messages(callback_query.chat_id, callback_query.id)
    api_hash_msg = await client.send_message(
        user_id,
        (
            "<b>Silahkan masukkan API HASH anda.</b>\n"
            "\n<b>Gunakan /cancel untuk Membatalkan Proses Membuat Userbot</b>"
        ),
        parse_mode="html",
    )
    api_hash_msg = await client.get_response(user_id, timeout=300)
    if await is_cancel(client, api_hash_msg.message):
        return
    api_hash = api_hash_msg.message
    try:
        await client.delete_messages(callback_query.chat_id, callback_query.id)
        phone = await client.send_message(
            user_id,
            (
                "<b>Silahkan Masukkan Nomor Telepon Telegram Anda Dengan Format Kode Negara.\nContoh: +628xxxxxxx</b>\n"
                "\n<b>Gunakan /cancel untuk Membatalkan Proses Membuat Userbot</b>"
            ),
            parse_mode="html",
        )
        phone = await client.get_response(user_id, timeout=300)
    except asyncio.TimeoutError:
        return await client.send_message(user_id, "Waktu Telah Habis")
    if await is_cancel(client, phone.message):
        return
    phone_number = phone.message
    new_client = TelegramClient(
        StringSession(),
        api_id,
        api_hash,
        in_memory=True,
        system_version="4.16.30-vxCUSTOM",
        device_model="Custom Device",
        app_version="3.7.10-NekoX",
    )
    get_otp = await client.send_message(user_id, "<b>Mengirim Kode OTP...</b>", parse_mode="html")
    await new_client.connect()
    try:
        code = await new_client.send_code_request(phone_number.strip())
    except errors.ApiIdInvalid as AID:
        await client.delete_messages(callback_query.chat_id, get_otp.id)
        return await client.send_message(user_id, str(AID))
    except errors.PhoneNumberInvalid as PNI:
        await client.delete_messages(callback_query.chat_id, get_otp.id)
        return await client.send_message(user_id, str(PNI))
    except errors.PhoneNumberFlood as PNF:
        await client.delete_messages(callback_query.chat_id, get_otp.id)
        return await client.send_message(user_id, str(PNF))
    except errors.PhoneNumberBanned as PNB:
        await client.delete_messages(callback_query.chat_id, get_otp.id)
        return await client.send_message(user_id, str(PNB))
    except errors.PhoneNumberUnoccupied as PNU:
        await client.delete_messages(callback_query.chat_id, get_otp.id)
        return await client.send_message(user_id, str(PNU))
    except Exception as error:
        await client.delete_messages(callback_query.chat_id, get_otp.id)
        return await client.send_message(user_id, f"<b>ERROR:</b> {error}", parse_mode="html")

    await client.delete_messages(callback_query.chat_id, get_otp.id)
    otp = await client.send_message(
        user_id,
        (
            "<b>Silakan Periksa Kode OTP dari <a href=tg://openmessage?user_id=777000>Akun Telegram</a> Resmi. Kirim Kode OTP ke sini setelah membaca Format di bawah ini.</b>\n"
            "\nJika Kode OTP adalah <code>12345</code> Tolong <b>[ TAMBAHKAN SPASI ]</b> kirimkan Seperti ini <code>1 2 3 4 5</code>\n"
            "\n<b>Gunakan /cancel untuk Membatalkan Proses Membuat Userbot</b>"
        ),
        parse_mode="html",
    )
    otp = await client.get_response(user_id, timeout=300)
    if await is_cancel(client, otp.message):
        return
    otp_code = otp.message
    try:
        await new_client.sign_in(phone_number.strip(), code.phone_code_hash, phone_code=" ".join(str(otp_code)))
    except errors.PhoneCodeInvalid as PCI:
        return await client.send_message(user_id, str(PCI))
    except errors.PhoneCodeExpired as PCE:
        return await client.send_message(user_id, str(PCE))
    except errors.BadRequest as error:
        return await client.send_message(user_id, f"<b>ERROR:</b> {error}", parse_mode="html")
    except errors.SessionPasswordNeeded:
        try:
            two_step_code = await client.send_message(
                user_id,
                "<b>Akun anda Telah mengaktifkan Verifikasi Dua Langkah. Silahkan Kirimkan Passwordnya.\n\nGunakan /cancel untuk Membatalkan Proses Membuat Userbot</b>",
                