from types import NoneType

from pytdbot import Client, types

from src.database import db
from src.logger import LOGGER
from src.modules.utils import (
    Filter,
    SupportButton,
    get_audio_duration,
    play_button,
    sec_to_min,
)
from src.modules.utils.admins import load_admin_cache, is_admin
from src.modules.utils.buttons import update_progress_bar
from src.modules.utils.cacher import chat_cache
from src.modules.utils.play_helpers import (
    get_url,
    edit_text,
    user_status_cache,
    unban_ub,
    join_ub,
    extract_argument,
    check_user_status,
    del_msg,
)

from src.modules.utils.thumbnails import gen_thumb
from src.platforms.dataclass import CachedTrack, MusicTrack, PlatformTracks
from src.platforms.downloader import MusicServiceWrapper
from src.platforms.telegram import Telegram
from src.pytgcalls import call, CallError


def _get_platform_url(platform: str, track_id: str) -> str:
    platform = platform.lower()
    if platform == "telegram":
        return ""
    elif platform == "youtube":
        return f"https://youtube.com/watch?v={track_id}"
    elif platform == "spotify":
        return f"https://open.spotify.com/track/{track_id}"
    else:
        LOGGER.error(f"Unknown platform: {platform}")
        return ""


async def update_message_with_thumbnail(
        c: Client, msg: types.Message, text: str, thumbnail: str, button: types.ReplyMarkupInlineKeyboard
) -> None:
    """Update a message with a thumbnail and text."""
    if not thumbnail:
        reply = await edit_text(msg, text=text, reply_markup=button)
        if isinstance(reply, types.Error):
            LOGGER.warning(f"Error editing message: {reply}")
            return
        return

    parsed_text = await c.parseTextEntities(text, types.TextParseModeHTML())
    if isinstance(parsed_text, types.Error):
        return await edit_text(msg, text=str(parsed_text), reply_markup=button)

    input_content = types.InputMessagePhoto(
        photo=(
            types.InputFileRemote(thumbnail)
            if thumbnail.startswith("http")
            else types.InputFileLocal(thumbnail)
        ),
        caption=parsed_text,
    )

    reply_msg = await c.editMessageMedia(
        chat_id=msg.chat_id,
        message_id=msg.id,
        input_message_content=input_content,
        reply_markup=button,
    )

    if isinstance(reply_msg, types.Error):
        LOGGER.warning(f"Error editing message: {reply_msg}")
        reply_msg = await edit_text(msg, text=str(reply_msg), reply_markup=button)

    return reply_msg

def format_now_playing(song: CachedTrack) -> str:
    """Format the 'Now Playing' message."""
    return (
        f"🎵 <b>Now playing:</b>\n\n"
        f"‣ <b>Title:</b> {song.name}\n"
        f"‣ <b>Duration:</b> {sec_to_min(song.duration)}\n"
        f"‣ <b>Requested by:</b> {song.user}"
    )


async def play_music(
        c: Client,
        msg: types.Message,
        url_data: PlatformTracks,
        user_by: str,
        tg_file_path: str = None,
) -> None:
    """Handle playing music from a given URL or file."""
    if not url_data:
        return await edit_text(msg, "❌ Unable to retrieve song info.")

    tracks = url_data.tracks
    chat_id = msg.chat_id
    queue = await chat_cache.get_queue(chat_id)
    is_active = await chat_cache.is_active(chat_id)
    msg = await edit_text(msg, text="🎶 Song found. Downloading...")
    _track = tracks[0]
    platform = _track.platform

    if len(tracks) == 1:
        song = CachedTrack(
            name=_track.name,
            artist=_track.artist,
            track_id=_track.id,
            loop=0,
            duration=_track.duration,
            file_path=tg_file_path or "",
            thumbnail=_track.cover,
            user=user_by,
            platform=platform,
        )

        if not song.file_path:
            song.file_path = await call.song_download(song=song)

        if not song.file_path:
            return await edit_text(msg, "❌ Error downloading the song.")

        if song.duration == 0:
            song.duration = await get_audio_duration(song.file_path)

        if is_active:
            await chat_cache.add_song(chat_id, song)
            text = (
                f"<b>➻ Added to Queue at #{len(queue)}:</b>\n\n"
                f"‣ <b>Title:</b> {song.name}\n"
                f"‣ <b>Duration:</b> {sec_to_min(song.duration)}\n"
                f"‣ <b>Requested by:</b> {song.user}"
            )
            thumb = await gen_thumb(song)
            await update_message_with_thumbnail(c, msg, text, thumb, play_button(0, 0))
            return

        try:
            await call.play_media(chat_id, song.file_path)
        except CallError as e:
            return await edit_text(msg, f"⚠️ {e}")
        except Exception as e:
            LOGGER.error(f"Error playing media: {e}")
            return await edit_text(msg, f"⚠️ Error playing media: {e}")

        await chat_cache.add_song(chat_id, song)
        thumb = await gen_thumb(song)
        reply =await update_message_with_thumbnail(c, msg, format_now_playing(song), thumb, play_button(0, song.duration))
        if isinstance(reply, types.Error):
            LOGGER.warning(f"Error editing message: {reply}")
            return

        await update_progress_bar(c, reply, 3, song.duration)
        return

    # Handle multiple tracks (queueing playlist/album)
    text = "<b>➻ Added to Queue:</b>\n<blockquote expandable>\n"
    for index, track in enumerate(tracks):
        position = len(queue) + index
        await chat_cache.add_song(
            chat_id,
            CachedTrack(
                name=track.name,
                artist=track.artist,
                track_id=track.id,
                loop=1 if not is_active and index == 0 else 0,
                duration=track.duration,
                thumbnail=track.cover,
                user=user_by,
                file_path="",
                platform=track.platform,
            ),
        )

        text += f"<b>{position}.</b> {track.name}\n└ Duration: {sec_to_min(track.duration)}\n"
    text += "</blockquote>\n"

    total_duration = sum(track.duration for track in tracks)
    text += (
        f"<b>📋 Total Queue:</b> {len(await chat_cache.get_queue(chat_id))}\n"
        f"<b>⏱️ Total Duration:</b> {sec_to_min(total_duration)}\n"
        f"<b>👤 Requested by:</b> {user_by}"
    )

    if not is_active:
        await call.play_next(chat_id)

    # MESSAGE_TOO_LONG
    if len(text) > 4096:
        text = (
            f"<b>📋 Total Queue:</b> {len(await chat_cache.get_queue(chat_id))}\n"
            f"<b>⏱️ Total Duration:</b> {sec_to_min(total_duration)}\n"
            f"<b>👤 Requested by:</b> {user_by}"
        )

    curr_song = await chat_cache.get_current_song(chat_id)
    reply = await edit_text(msg, text, reply_markup=play_button(0, curr_song.duration))
    if isinstance(reply, types.Error):
        LOGGER.warning(f"Error sending message: {reply}")
        return

    await update_progress_bar(c, reply, 3, curr_song.duration)
    return


@Client.on_message(Filter.command("play"))
async def play_audio(c: Client, msg: types.Message) -> None:
    """Handle the /play command."""
    chat_id = msg.chat_id
    if chat_id > 0:
        return await msg.reply_text("This command is only available in supergroups.")

    await load_admin_cache(c, chat_id)
    admin = await is_admin(chat_id, c.options["my_id"] or c.me.id)
    if not admin:
        return await msg.reply_text(
            "I need to be an admin with invite user permission if the group is private.\n\n"
            "After promoting me, please try again or use /reload."
        )

    reply: types.Message = None
    url = await get_url(msg, None)
    if msg.reply_to_message_id:
        reply = await msg.getRepliedMessage()
        url = await get_url(msg, reply)

    reply_message = await msg.reply_text("🔎 Searching...")
    if isinstance(reply_message, types.Error):
        LOGGER.warning(f"Error sending reply message: {reply_message}")
        return

    ub = await call.get_client(chat_id)
    if isinstance(ub, (types.Error, NoneType)):
        return await edit_text(reply_message, "❌ Assistant not found for this chat.")

    if isinstance(ub.me, (types.Error, NoneType)):
        return await edit_text(reply_message, "❌ Assistant not found for this chat.")

    assistant_id = ub.me.id

    queue = await chat_cache.get_queue(chat_id)
    if len(queue) > 10:
        return await edit_text(
            reply_message,
            text=f"❌ Queue full! You have {len(queue)} tracks. Use /end to reset.",
        )

    # Check user status and handle bans/restrictions
    user_key = f"{chat_id}:{assistant_id}"
    user_status = user_status_cache.get(user_key) or await check_user_status(
        c, chat_id, assistant_id
    )

    if isinstance(user_status, types.Error):
        return await edit_text(reply_message, text=f"❌ {str(user_status)}")

    if user_status in {
        "chatMemberStatusBanned",
        "chatMemberStatusLeft",
        "chatMemberStatusRestricted",
    }:
        if user_status == "chatMemberStatusBanned":
            await unban_ub(c, chat_id, assistant_id)
        join = await join_ub(chat_id, c, ub)
        if isinstance(join, types.Error):
            return await edit_text(reply_message, text=f"❌ {str(join)}")

    args = extract_argument(msg.text)
    telegram = Telegram(reply)
    wrapper = MusicServiceWrapper(url or args)
    await del_msg(msg)

    if not args and not url and not telegram.is_valid():
        recommendations = await wrapper.get_recommendations()
        text = "ᴜsᴀɢᴇ: /play song_name\nSupports Spotify track, playlist, album, artist links.\n\n"
        if not recommendations:
            return await edit_text(reply_message, text=text, reply_markup=SupportButton)

        platform = recommendations.tracks[0].platform
        text += "Tap on a song name to play it."
        buttons = [
            [
                types.InlineKeyboardButton(
                    f"{track.name[:18]} - {track.artist}",
                    type=types.InlineKeyboardButtonTypeCallback(
                        f"play_{platform}_{track.id}".encode()
                    ),
                )
            ]
            for track in recommendations.tracks
        ]

        return await edit_text(
            reply_message,
            text=text,
            reply_markup=types.ReplyMarkupInlineKeyboard(buttons),
        )

    user_by = await msg.mention()
    if telegram.is_valid():
        _path = await telegram.dl()
        if isinstance(_path, types.Error):
            return await edit_text(reply_message, text=f"❌ {str(_path)}")

        file_path = _path.path
        if not file_path:
            return await edit_text(reply_message, text="❌ Error downloading the file.")

        _song = PlatformTracks(
            tracks=[
                MusicTrack(
                    name=telegram.get_file_name(),
                    artist="AshokShau",
                    id=reply.remote_unique_file_id,
                    year=0,
                    cover="",
                    duration=await get_audio_duration(file_path),
                    platform="telegram",
                )
            ]
        )

        return await play_music(c, reply_message, _song, user_by, file_path)

    if url:
        if wrapper.is_valid(url):
            _song = await wrapper.get_info()
            if not _song:
                return await edit_text(
                    reply_message,
                    text="❌ Unable to retrieve song info.\n\nPlease report this issue if you think it's a bug.",
                    reply_markup=SupportButton,
                )

            return await play_music(c, reply_message, _song, user_by)

        return await edit_text(
            reply_message,
            text="❌ Invalid URL! Provide a valid link.",
            reply_markup=SupportButton,
        )

    # Handle text-based search
    play_type = await db.get_play_type(chat_id)
    search = await wrapper.search()
    if not search:
        return await edit_text(
            reply_message,
            text="❌ No results found. Please report this issue if you think it's a bug.",
            reply_markup=SupportButton,
        )

    platform = search.tracks[0].platform

    if play_type == 0:
        _song_id = search.tracks[0].id
        url = _get_platform_url(platform, _song_id)
        if _song := await MusicServiceWrapper(url).get_info():
            return await play_music(c, reply_message, _song, user_by)

        return await edit_text(
            reply_message,
            text="❌ Unable to retrieve song info.",
            reply_markup=SupportButton,
        )

    buttons = [
        [
            types.InlineKeyboardButton(
                f"{rec.name[:18]} - {rec.artist}",
                type=types.InlineKeyboardButtonTypeCallback(
                    f"play_{platform}_{rec.id}".encode()
                ),
            )
        ]
        for rec in search.tracks[:4]
    ]

    reply = await edit_text(
        reply_message,
        text=f"{user_by}, select a song to play:",
        reply_markup=types.ReplyMarkupInlineKeyboard(buttons),
        disable_web_page_preview=True,
        parse_mode="html",
    )

    if isinstance(reply, types.Error):
        LOGGER.warning(f"Error sending message: {reply}")
        return
