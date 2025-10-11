from telethon import events
from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.functions.account import UpdateNotifySettingsRequest
import asyncio
from telethon.errors import FloodWaitError, UserAdminInvalidError, ChatAdminRequiredError
from . import ultroid_cmd
from . import *


@ultroid_cmd(pattern="limited$")
async def demn(ult):
    chat = "@SpamBot"
    await ult.edit("Checking If You Are Limited...")
    async with ult.client.conversation(chat) as conv:
        try:
            response = conv.wait_event(events.NewMessage(incoming=True, from_users=178220800))
            await ult.client.send_message(chat, "/start")
            response = await response
        except YouBlockedUserError:
            await ult.reply("Boss! Please Unblock @SpamBot ")
            return
        await eor(ult, f"<blockquote>{response.message.message}</blockquote>", parse_mode="html")


@ultroid_cmd(pattern="banall(?: (.*))?")
async def banall(event):
    """Ban all members in a specified group (Dangerous, use carefully)"""
    if event.is_private:
        return await event.edit("`This command can only be used in groups!`")
    
    args = event.pattern_match.group(1)
    
    if not args:
        return await event.edit("`Please provide a group ID!`")
    
    try:
        chat_id = int(args.strip())
    except ValueError:
        return await event.edit("`Invalid group ID! Please provide a valid numeric ID.`")
    
    try:
        # Get the chat entity to verify it exists and bot has access
        chat = await event.client.get_entity(chat_id)
        chat_title = chat.title
    except Exception as e:
        return await event.edit(f"`Couldn't access the group: {str(e)}`")
    
    # Confirmation message and counter
    await event.edit(f"`Getting members from {chat_title}...`")
    
    try:
        total = 0
        banned = 0
        failed = 0
        
        async for user in event.client.iter_participants(chat_id):
            total += 1
            # Skip banning the bot itself
            if user.id == event.client.uid:
                continue
                
            try:
                await event.client.edit_permissions(
                    chat_id, 
                    user.id, 
                    view_messages=False
                )
                banned += 1
                await event.edit(
                    f"`Banning members in {chat_title}...\n`"
                    f"Progress: {banned}/{total}\n"
                    f"Success: {banned} | Failed: {failed}"
                )
            except FloodWaitError as e:
                # Handle flood wait
                await event.edit(f"`Hit FloodWait restriction. Sleeping for {e.seconds} seconds.`")
                await asyncio.sleep(e.seconds)
            except (UserAdminInvalidError, ChatAdminRequiredError):
                # Can't ban admins
                failed += 1
            except Exception as e:
                failed += 1
                
            # Sleep briefly between bans to reduce flood chance
            await asyncio.sleep(0.2)
            
        await event.edit(
            f"`Operation completed in {chat_title}\n`"
            f"Total members: {total}\n"
            f"Successfully banned: {banned}\n"
            f"Failed to ban: {failed}"
        )
    except Exception as e:
        await event.edit(f"`An error occurred: {str(e)}`")

"""from telethon import events
from telethon.tl.types import (
    InputWebDocument,
    MessageMediaWebPage,
    WebDocument,
    InlineQuery,
    InputMediaDocument,
    DocumentAttributeFilename,
    DocumentAttributeAnimated,
    DocumentAttributeSticker,
    DocumentAttributeAudio,
    DocumentAttributeVideo,
    InputDocument,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telethon.errors.rpcerrorlist import YouBlockedUserError
# You would need to use a Telethon Client for a bot, not a user bot framework.

# Example structure for an Inline Query Handler
# ... import statements ...

@in_pattern("limit", owner=True)
async def limit(query):
    chat = "@SpamBot"
    
    # Pesan default jika terjadi kesalahan
    response_message = "⏳ Gagal mendapatkan status. Coba lagi atau pastikan @SpamBot tidak diblokir." 
    
    try:
        # Menggunakan conv (conversation) untuk interaksi.
        async with query.client.conversation(chat, timeout=5) as conv:
            # 1. Kirim perintah /start
            await conv.send_message("/start")
            
            # 2. Tunggu balasan dari SpamBot (maksimal 5 detik)
            response = await conv.get_response()
            
            # 3. Ambil teks status yang sebenarnya
            response_message = response.text 
            
    except YouBlockedUserError:
        response_message = "⛔️ Harap Unblock @SpamBot untuk melakukan pengecekan status."
    except TimeoutError:
        response_message = "⚠️ Pengecekan status @SpamBot gagal (Timeout). Coba lagi."
    except Exception as e:
        response_message = f"❌ Terjadi kesalahan saat memeriksa: {e.__class__.__name__}"

    # ... (Bagian builder.article di bawahnya sama) ...
    builder = query.builder
    await query.answer(
        [
            builder.article(
                title="Spam Limit Status",
                text=response_message,
                description="Tap to send your current account limit status."
            )
        ]
    )
"""
