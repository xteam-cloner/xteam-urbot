import asyncio
from collections import deque
from typing import Dict, Optional, Any


class ChatCacher:
    from src.platforms.dataclass import CachedTrack

    def __init__(self):
        self.chat_cache: Dict[int, Dict[str, Any]] = {}
        self.lock = asyncio.Lock()

    async def add_song(self, chat_id: int, song: CachedTrack) -> CachedTrack:
        async with self.lock:
            if chat_id not in self.chat_cache:
                self.chat_cache[chat_id] = {"is_active": True, "queue": deque()}
            self.chat_cache[chat_id]["queue"].append(song)
            return song

    async def get_next_song(self, chat_id: int) -> Optional[CachedTrack]:
        async with self.lock:
            queue = self.chat_cache.get(chat_id, {}).get("queue", deque())
            return queue[1] if len(queue) > 1 else None

    async def get_current_song(self, chat_id: int) -> Optional[CachedTrack]:
        async with self.lock:
            queue = self.chat_cache.get(chat_id, {}).get("queue", deque())
            return queue[0] if queue else None

    async def remove_current_song(self, chat_id: int) -> Optional[CachedTrack]:
        async with self.lock:
            queue = self.chat_cache.get(chat_id, {}).get("queue", deque())
            return queue.popleft() if queue else None

    async def is_active(self, chat_id: int) -> bool:
        async with self.lock:
            return self.chat_cache.get(chat_id, {}).get("is_active", False)

    async def set_active(self, chat_id: int, active: bool):
        async with self.lock:
            if chat_id in self.chat_cache:
                self.chat_cache[chat_id]["is_active"] = active
            else:
                self.chat_cache[chat_id] = {"is_active": active, "queue": deque()}

    async def clear_chat(self, chat_id: int):
        async with self.lock:
            self.chat_cache.pop(chat_id, None)

    async def clear_all(self):
        async with self.lock:
            self.chat_cache.clear()

    async def count(self, chat_id: int) -> int:
        async with self.lock:
            return len(self.chat_cache.get(chat_id, {}).get("queue", deque()))

    async def get_loop_count(self, chat_id: int) -> int:
        async with self.lock:
            queue = self.chat_cache.get(chat_id, {}).get("queue", deque())
            return queue[0].loop if queue else 0

    async def set_loop_count(self, chat_id: int, loop: int) -> bool:
        async with self.lock:
            if queue := self.chat_cache.get(chat_id, {}).get("queue", deque()):
                queue[0].loop = loop
                return True
            return False

    async def remove_track(self, chat_id: int, queue_index: int) -> bool:
        async with self.lock:
            queue = self.chat_cache.get(chat_id, {}).get("queue", deque())
            if len(queue) > queue_index:
                queue_list = list(queue)
                queue_list.pop(queue_index)
                self.chat_cache[chat_id]["queue"] = deque(queue_list)
                return True
            return False

    async def get_queue(self, chat_id: int) -> list[CachedTrack]:
        async with self.lock:
            return list(self.chat_cache.get(chat_id, {}).get("queue", deque()))

    async def get_active_chats(self) -> list[int]:
        async with self.lock:
            return [
                chat_id
                for chat_id, data in self.chat_cache.items()
                if data["is_active"]
            ]


chat_cache = ChatCacher()
