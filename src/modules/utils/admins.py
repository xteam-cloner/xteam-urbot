from typing import Optional, Tuple

from cachetools import TTLCache
from pytdbot import types, Client

from src.logger import LOGGER
from plugins import ultroid_cmd
from typing import Optional, Tuple, List

from telethon import TelegramClient, events, types
from cachetools import TTLCache



# Configure logging


# Replace with your API credentials and session string

admin_cache = TTLCache(maxsize=1000, ttl=30 * 60) # 30 minutes TTL

class AdminCacheData:
    def __init__(self, chat_id: int, user_info: List[types.ChatParticipant], cached: bool = True):
        self.chat_id = chat_id
        self.user_info = user_info
        self.cached = cached

async def load_admin_cache(client: TelegramClient, chat_id: int, force_reload: bool = False) -> Tuple[bool, AdminCacheData]:
    """
    Load the admin list from Telegram and cache it, unless already cached.
    Set force_reload to True to bypass the cache and reload the admin list.
    """
    if not force_reload and chat_id in admin_cache:
        return True, admin_cache[chat_id]  # Return cached data if available

    try:
        admins = await client.get_participants(chat_id, filter=types.ChannelParticipantsAdmins)
        admin_cache[chat_id] = AdminCacheData(chat_id, admins)
        return True, admin_cache[chat_id]
    except Exception as e:
        logger.warning(f"Error loading admin cache for chat_id {chat_id}: {e}")
        return False, AdminCacheData(chat_id, [], cached=False)

async def get_admin_cache_user(chat_id: int, user_id: int) -> Tuple[bool, Optional[types.ChatParticipant]]:
    """
    Check if the user is an admin using cached data.
    """
    admin_data = admin_cache.get(chat_id)
    if admin_data is None:
        return False, None  # Cache miss

    for user_info in admin_data.user_info:
        if user_info.id == user_id:
            return True, user_info
    return False, None

async def is_owner(chat_id: int, user_id: int) -> bool:
    """
    Check if the user is the owner of the chat.
    """
    is_cached, user = await get_admin_cache_user(chat_id, user_id)
    if user:
        return isinstance(user.participant, types.ChannelParticipantCreator)
    return False

async def is_admin(chat_id: int, user_id: int) -> bool:
    """
    Check if the user is an admin (including the owner) in the chat.
    """
    is_cached, user = await get_admin_cache_user(chat_id, user_id)
    if user:
        return isinstance(user.participant, (types.ChannelParticipantCreator, types.ChannelParticipantAdmin))
    return False

# Example usage within a command handler
@ultroid_cmd(pattern="checkadmin")
async def check_admin(event):
    chat_id = event.chat_id
    user_id = event.sender_id

    is_admin_result = await is_admin(chat_id, user_id)
    is_owner_result = await is_owner(chat_id, user_id)

    await event.respond(f"Admin: {is_admin_result}, Owner: {is_owner_result}")
