from typing import Optional

from cachetools import TTLCache
from motor.motor_asyncio import AsyncIOMotorClient

import config
from src.logger import LOGGER


class Database:
    def __init__(self):
        self.mongo_client = AsyncIOMotorClient(config.MONGO_URI)
        _db = self.mongo_client["MusicBot"]
        self.chat_db = _db["chats"]
        self.users_db = _db["users"]

        self.play_type_cache = TTLCache(maxsize=1000, ttl=600)
        self.assistant_cache = TTLCache(maxsize=1000, ttl=600)

    async def ping(self) -> None:
        """Ping the MongoDB server to check the connection."""
        try:
            await self.mongo_client.admin.command("ping")
            LOGGER.info("Database connection completed.")
        except Exception as e:
            LOGGER.error(f"Database connection failed: {e}")
            raise

    async def get_chat(self, chat_id: int) -> Optional[dict]:
        """Retrieve a chat document by chat_id."""
        try:
            return await self.chat_db.find_one({"_id": chat_id})
        except Exception as e:
            LOGGER.warning(f"Error getting chat: {e}")
            return None

    async def add_chat(self, chat_id: int) -> None:
        if await self.get_chat(chat_id) is None:
            LOGGER.info(f"Added chat: {chat_id}")
            await self.chat_db.insert_one({"_id": chat_id})

    async def set_play_type(self, chat_id: int, play_type: int) -> None:
        """Set the play type for a chat and cache it."""
        await self.chat_db.update_one(
            {"_id": chat_id}, {"$set": {"play_type": play_type}}, upsert=True
        )
        self.play_type_cache[chat_id] = play_type

    async def get_play_type(self, chat_id: int) -> int:
        """Retrieve the play type for a chat, using cache if available."""
        if chat_id in self.play_type_cache:
            return self.play_type_cache[chat_id]

        chat = await self.get_chat(chat_id)
        play_type = chat.get("play_type", 1) if chat else 1
        self.play_type_cache[chat_id] = play_type
        return play_type

    async def set_assistant(self, chat_id: int, assistant: str) -> None:
        """Set the assistant for a chat and cache it."""
        await self.chat_db.update_one(
            {"_id": chat_id}, {"$set": {"assistant": assistant}}, upsert=True
        )
        self.assistant_cache[chat_id] = assistant

    async def get_assistant(self, chat_id: int) -> Optional[str]:
        """Retrieve the assistant for a chat, using cache if available."""
        if chat_id in self.assistant_cache:
            return self.assistant_cache[chat_id]

        chat = await self.get_chat(chat_id)
        assistant = chat.get("assistant", None) if chat else None
        self.assistant_cache[chat_id] = assistant
        return assistant

    async def remove_assistant(self, chat_id: int) -> None:
        """Remove the assistant for a chat and clear it from the cache."""
        await self.chat_db.update_one({"_id": chat_id}, {"$set": {"assistant": None}})
        self.assistant_cache.pop(chat_id, None)

    async def add_auth_user(self, chat_id: int, auth_user: int) -> None:
        """Add an authorized user to a chat."""
        await self.chat_db.update_one(
            {"_id": chat_id}, {"$addToSet": {"auth_users": auth_user}}, upsert=True
        )

    async def remove_auth_user(self, chat_id: int, auth_user: int) -> None:
        """Remove an authorized user from a chat."""
        await self.chat_db.update_one(
            {"_id": chat_id},
            {"$pull": {"auth_users": auth_user}},
        )

    async def get_auth_users(self, chat_id: int) -> list[int]:
        """Retrieve the list of authorized users for a chat."""
        chat = await self.get_chat(chat_id)
        return chat.get("auth_users", []) if chat else []

    async def remove_chat(self, chat_id: int) -> None:
        """Remove a chat and clear its cache."""
        await self.chat_db.delete_one({"_id": chat_id})
        self.play_type_cache.pop(chat_id, None)
        self.assistant_cache.pop(chat_id, None)

    async def reset_auth_users(self, chat_id: int) -> None:
        """Reset the list of authorized users for a chat."""
        await self.chat_db.update_one({"_id": chat_id}, {"$set": {"auth_users": []}})

    async def is_auth_user(self, chat_id: int, user_id: int) -> bool:
        """Check if a user is authorized in a chat."""
        return user_id in await self.get_auth_users(chat_id)

    async def add_user(self, user_id: int) -> None:
        """Add a user to the users collection if they don't already exist."""
        if await self.is_user_exist(user_id):
            return
        LOGGER.info(f"Added user: {user_id}")
        await self.users_db.insert_one({"_id": user_id})

    async def remove_user(self, user_id: int) -> None:
        """Remove a user from the user's collection."""
        await self.users_db.delete_one({"_id": user_id})

    async def is_user_exist(self, user_id: int) -> bool:
        """Check if a user exists in the user's collection."""
        return await self.users_db.find_one({"_id": user_id}) is not None

    async def get_all_users(self) -> list[int]:
        """Retrieve all user IDs from the users collection."""
        return [user["_id"] async for user in self.users_db.find()]

    async def get_all_chats(self) -> list[int]:
        """Retrieve all chat IDs from the chats collection."""
        return [chat["_id"] async for chat in self.chat_db.find()]

    async def close(self) -> None:
        """Close the MongoDB connection."""
        self.mongo_client.close()
        LOGGER.info("Database connection closed.")


db: Database = Database()
