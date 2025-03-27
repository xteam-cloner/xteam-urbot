__all__ = [
    "Filter",
    "sec_to_min",
    "get_audio_duration",
    "play_button",
    "PauseButton",
    "ResumeButton",
    "SupportButton",
]

import re
from typing import Union

from mutagen import File
from pytdbot import filters, types

from src.logger import LOGGER
from .buttons import play_button, PauseButton, ResumeButton, SupportButton


def sec_to_min(seconds):
    """Convert seconds to minutes:seconds format."""
    try:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}:{remaining_seconds:02}"
    except Exception as e:
        LOGGER.warning(f"Failed to convert seconds to minutes:seconds format: {e}")
        return None


async def get_audio_duration(file_path):
    try:
        audio = File(file_path)
        return int(audio.info.length)
    except Exception as e:
        LOGGER.warning(f"Failed to get audio duration: {e}")
        return 0


class Filter:
    @staticmethod
    def command(commands: Union[str, list[str]]):
        """Filter for commands, supports multiple commands"""
        if isinstance(commands, str):
            commands = [commands]

        async def filter_func(_, event) -> bool:
            if isinstance(event, types.Message) and isinstance(
                    event.content, types.MessageText
            ):
                return any(
                    event.content.text.text.startswith(f"/{cmd.lower()}")
                    for cmd in commands
                )

            if isinstance(event, types.UpdateNewMessage) and isinstance(
                    event.message, types.MessageText
            ):
                return any(
                    event.message.text.text.startswith(f"/{cmd.lower()}")
                    for cmd in commands
                )

            return False

        return filters.create(filter_func)

    @staticmethod
    def regex(pattern: str):
        """Filter for messages matching a regex pattern."""

        async def filter_func(_, event) -> bool:
            if isinstance(event, types.Message) and isinstance(
                    event.content, types.MessageText
            ):
                return bool(re.search(pattern, event.content.text))

            if isinstance(event, types.UpdateNewMessage) and isinstance(
                    event.message, types.MessageText
            ):
                return bool(re.search(pattern, event.message.text.text))

            if isinstance(event, types.UpdateNewCallbackQuery):
                data = event.payload.data.decode() if event.payload else ""
                return bool(re.search(pattern, data))

            return False

        return filters.create(filter_func)

    @staticmethod
    def user(user_ids: Union[int, list[int]]):
        """Filter for specific user IDs."""
        if isinstance(user_ids, int):
            user_ids = [user_ids]

        async def filter_func(_, event) -> bool:
            if isinstance(event.sender_id, types.MessageSenderChat):
                return event.sender_id.chat_id in user_ids
            elif isinstance(event.sender_id, types.MessageSenderUser):
                return event.sender_id.user_id in user_ids

            return False

        return filters.create(filter_func)

    @staticmethod
    def chat(chat_ids: Union[int, list[int]]):
        """Filter for specific chat IDs."""
        if isinstance(chat_ids, int):
            chat_ids = [chat_ids]

        async def filter_func(_, event) -> bool:
            return event.chat_id in chat_ids if hasattr(event, "chat_id") else False

        return filters.create(filter_func)
