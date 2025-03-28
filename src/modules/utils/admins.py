from typing import Optional, Tuple

from cachetools import TTLCache
from pytdbot import types, Client

from src.logger import LOGGER

admin_cache = TTLCache(maxsize=1000, ttl=30 * 60)


class AdminCache:
    def __init__(
            self, chat_id: int, user_info: list[types.ChatMember], cached: bool = True
    ):
        self.chat_id = chat_id
        self.user_info = user_info
        self.cached = cached


async def load_admin_cache(
        c: Client, chat_id: int, force_reload: bool = False
) -> Tuple[bool, AdminCache]:
    """
    Load the admin list from Telegram and cache it, unless already cached.
    Set force_reload to True to bypass the cache and reload the admin list.
    """
    if not force_reload and chat_id in admin_cache:
        return True, admin_cache[chat_id]  # Return cached data if available

    admin_list = await c.searchChatMembers(
        chat_id, filter=types.ChatMembersFilterAdministrators()
    )
    if isinstance(admin_list, types.Error):
        LOGGER.warning(f"Error loading admin cache for chat_id {chat_id}: {admin_list}")
        return False, AdminCache(chat_id, [], cached=False)

    admin_cache[chat_id] = AdminCache(chat_id, admin_list["members"])
    return True, admin_cache[chat_id]


async def get_admin_cache_user(
        chat_id: int, user_id: int
) -> Tuple[bool, Optional[dict]]:
    """
    Check if the user is an admin using cached data.
    """
    admin_list = admin_cache.get(chat_id)
    if admin_list is None:
        return False, None  # Cache miss

    return next(
        (
            (True, user_info)
            for user_info in admin_list.user_info
            if user_info["member_id"]["user_id"] == user_id
        ),
        (False, None),
    )


async def is_owner(chat_id: int, user_id: int) -> bool:
    """
    Check if the user is the owner of the chat.
    """
    is_cached, user = await get_admin_cache_user(chat_id, user_id)
    user_status = user["status"]["@type"] if user else None
    return is_cached and user_status == "chatMemberStatusCreator"


async def is_admin(chat_id: int, user_id: int) -> bool:
    """
    Check if the user is an admin (including the owner) in the chat.
    """
    is_cached, user = await get_admin_cache_user(chat_id, user_id)
    user_status = user["status"]["@type"] if user else None
    if chat_id == user_id:
        return True  # Anon Admin

    return is_cached and user_status in [
        "chatMemberStatusCreator",
        "chatMemberStatusAdministrator",
    ]
