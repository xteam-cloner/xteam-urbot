import asyncio

from pytdbot import Client, types

from src.logger import LOGGER
from src.modules.utils.cacher import chat_cache


def play_button(current_seconds: int, total_seconds: int) -> types.ReplyMarkupInlineKeyboard:
    # Calculate progress (scaled to 10 slots)
    if total_seconds == 0:
        button_text = " 🎵 Playing"
    else:
        progress = round((current_seconds / total_seconds) * 10) if total_seconds > 0 else 0
        bar = ["—"] * 10
        bar[min(progress, 9)] = "◉"  # Ensure index is within range
        progress_bar_text = "".join(bar)  # Convert list to string
        button_text = f"{current_seconds // 60}:{current_seconds % 60} {progress_bar_text} {total_seconds // 60}:{total_seconds % 60}"
    return types.ReplyMarkupInlineKeyboard(
        [
            [
                types.InlineKeyboardButton(
                    text=button_text,
                    type=types.InlineKeyboardButtonTypeCallback(b"timer"),
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text="▶️ Skip", type=types.InlineKeyboardButtonTypeCallback(b"play_skip")
                ),
                types.InlineKeyboardButton(
                    text="⏹️ End", type=types.InlineKeyboardButtonTypeCallback(b"play_stop")
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text="⏸️ Pause",
                    type=types.InlineKeyboardButtonTypeCallback(b"play_pause"),
                ),
                types.InlineKeyboardButton(
                    text="⏯️ Resume",
                    type=types.InlineKeyboardButtonTypeCallback(b"play_resume"),
                ),
            ],
        ]
    )


async def update_progress_bar(
        client: Client,
        message: types.Message,
        current_seconds: int,
        total_seconds: int,
) -> None:
    """Updates the progress bar in the message at regular intervals.

    Args:
        client: The PyTd Client
        message: The message to update
        current_seconds: Current playback position in seconds
        total_seconds: Total duration in seconds
    """
    message_id = message.id
    chat_id = message.chat_id
    error_count = 0
    update_interval = total_seconds // 15 if total_seconds > 150 else 6
    max_errors = 3

    while current_seconds <= total_seconds and not not await chat_cache.is_active(chat_id):
        keyboard = play_button(current_seconds, total_seconds)
        edit = await client.editMessageReplyMarkup(
            chat_id,
            message_id,
            reply_markup=keyboard
        )
    
        if isinstance(edit, types.Error):
            error_count += 1
            LOGGER.error(f"Error updating progress bar: {edit}")
            if error_count >= max_errors:
                LOGGER.warning(f"Max errors ({max_errors}) reached, stopping updates")
                break
            continue
    
        error_count = 0  # Reset on successful update
        await asyncio.sleep(update_interval)
        current_seconds += update_interval


PauseButton = types.ReplyMarkupInlineKeyboard(
    [
        [
            types.InlineKeyboardButton(
                text="▶️ Skip", type=types.InlineKeyboardButtonTypeCallback(b"play_skip")
            ),
            types.InlineKeyboardButton(
                text="⏹️ End", type=types.InlineKeyboardButtonTypeCallback(b"play_stop")
            ),
        ],
        [
            types.InlineKeyboardButton(
                text="⏯️ Resume",
                type=types.InlineKeyboardButtonTypeCallback(b"play_resume"),
            ),
        ],
    ]
)

ResumeButton = types.ReplyMarkupInlineKeyboard(
    [
        [
            types.InlineKeyboardButton(
                text="▶️ Skip", type=types.InlineKeyboardButtonTypeCallback(b"play_skip")
            ),
            types.InlineKeyboardButton(
                text="⏹️ End", type=types.InlineKeyboardButtonTypeCallback(b"play_stop")
            ),
        ],
        [
            types.InlineKeyboardButton(
                text="⏸️ Pause",
                type=types.InlineKeyboardButtonTypeCallback(b"play_pause"),
            ),
        ],
    ]
)

SupportButton = types.ReplyMarkupInlineKeyboard(
    [
        [
            types.InlineKeyboardButton(
                text="❄ Channel",
                type=types.InlineKeyboardButtonTypeUrl("https://t.me/FallenProjects"),
            ),
            types.InlineKeyboardButton(
                text="✨ Group",
                type=types.InlineKeyboardButtonTypeUrl("https://t.me/GuardxSupport"),
            ),
        ]
    ]
)

AddMeButton = types.ReplyMarkupInlineKeyboard(
    [
        [
            types.InlineKeyboardButton(
                text="Add me to your group",
                type=types.InlineKeyboardButtonTypeUrl(
                    "https://t.me/FallenBeatzBot?startgroup=true"
                ),
            ),
        ],
        [
            types.InlineKeyboardButton(
                text="❄ Channel",
                type=types.InlineKeyboardButtonTypeUrl("https://t.me/FallenProjects"),
            ),
            types.InlineKeyboardButton(
                text="✨ Group",
                type=types.InlineKeyboardButtonTypeUrl("https://t.me/GuardxSupport"),
            ),
        ],
    ]
)
