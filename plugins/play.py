from telethon import TelegramClient, events, Button
from telethon.tl.types import InputMediaPhoto
from . import ultroid_cmd
from src.database import db
from src.logger import LOGGER
from src.modules.utils import (
    Filter,
    SupportButton,
    get_audio_duration,
    play_button,
    sec_to_min,
)
from pyUltroid.fns.admins import admin_check, is_admin
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


async def update_message_with_thumbnail(client: TelegramClient, event, text: str, thumbnail: str, buttons):
    """Update a message with a thumbnail and text."""
    if not thumbnail:
        await event.edit(text, buttons=buttons)
        return

    await client.send_file(
        event.chat_id,
        file=thumbnail,
        caption=text,
        buttons=buttons,
        parse_mode='html'
    )


def format_now_playing(song: CachedTrack) -> str:
    """Format the 'Now Playing' message."""
    return (
        f"🎵 <b>Now playing:</b>\n\n"
        f"‣ <b>Title:</b> {song.name}\n"
        f"‣ <b>Duration:</b> {sec_to_min(song.duration)}\n"
        f"‣ <b>Requested by:</b> {song.user}"
    )


async def play_music(client: TelegramClient, event, url_data: PlatformTracks, user_by: str, tg_file_path: str = None):
    """Handle playing music from a given URL or file."""
    if not url_data:
        await event.edit("❌ Unable to retrieve song info.")
        return

    tracks = url_data.tracks
    chat_id = event.chat_id
    queue = await chat_cache.get_queue(chat_id)
    is_active = await chat_cache.is_active(chat_id)
    await event.edit("🎶 Song found. Downloading...")
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
            await event.edit("❌ Error downloading the song.")
            return

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
            await update_message_with_thumbnail(client, event, text, thumb, play_button(0, 0))
            return

        try:
            await call.play_media(chat_id, song.file_path)
        except CallError as e:
            await event.edit(f"⚠️ {e}")
            return
        except Exception as e:
            LOGGER.error(f"Error playing media: {e}")
            await event.edit(f"⚠️ Error playing media: {e}")
            return

        await chat_cache.add_song(chat_id, song)
        thumb = await gen_thumb(song)
        await update_message_with_thumbnail(client, event, format_now_playing(song), thumb, play_button(0, song.duration))
        await update_progress_bar(client, event, 3, song.duration)
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
    await event.edit(text, buttons=play_button(0, curr_song.duration))
    await update_progress_bar(client, event, 3, curr_song.duration)
    return


@ultroid_cmd(pattern="play")
async def play_audio(event):
    """Handle the /play command."""
    chat_id = event.chat_id
    if chat_id > 0:
        await event.respond("This command is only available in supergroups.")
        return

    await admin_check(event, chat_id)
    admin = await is_admin(chat_id, event.get_me().id)
    if not admin:
        await event.respond(
            "I need to be an admin with invite user permission if the group is private.\n\n"
            "After promoting me, please try again or use /reload."
        )
        return

    reply = None
    url = await get_url(event, None)
    if event.reply_to:
        reply = await event.get_reply_message()
        url = await get_url(event, reply)

    reply_message = await event.respond("🔎 Searching...")

    ub = await call.get_client(chat_id)
    if not ub:
        await reply_message.edit("❌ Assistant not found for this chat.")
        return

    assistant_id = (await ub.get_me()).id

    queue = await chat_cache.get_queue(chat_id)
    if len(queue) > 10:
        await reply_message.edit(
            f"❌ Queue full! You have {len(queue)} tracks. Use /end to reset.",
        )
        return

    # Check user status and handle bans/restrictions
    user_key = f"{chat_id}:{assistant_id}"
    user_status = user_status_cache.get(user_key) or await check_user_status(
        client, chat_id, assistant_id
    )

    if not user_status:
        await reply_message.edit(f"❌ {str(user_status)}")

    if user_status in {
        "chatMemberStatusBanned",
        "chatMemberStatusLeft",
        "chatMemberStatusRestricted",
    }:
        if user_status == "chatMemberStatusBanned":
            await unban_ub(client, chat_id, assistant_id)
        join = await join_ub(chat_id, client, ub)
        if not join:
            await reply_message.edit(f"❌ {str(join)}")

    args = extract_argument(event.raw_text)
    telegram = Telegram(reply)
    wrapper = MusicServiceWrapper(url or args)
    await del_msg(event.message)

    if not args and not url and not telegram.is_valid():
        recommendations = await wrapper.get_recommendations()
        text = "Usage: /play song_name\nSupports Spotify track, playlist, album, artist links.\n\n"
        if not recommendations:
            await reply_message.edit(text, buttons=SupportButton)
            return

        platform = recommendations.tracks[0].platform
        text += "Tap on a song name to play it."
        buttons = [
            [Button.inline(f"{track.name[:18]} - {track.artist}", data=f"play_{platform}_{track.id}")]
            for track in recommendations.tracks
        ]

        await reply_message.edit(text, buttons=buttons)
        return

    user_by = event.sender.username
    if telegram.is_valid():
        _path = await telegram.dl()
        if not _path:
            await reply_message.edit(f"❌ {str(_path)}")
            return

        file_path = _path.path
        if not file_path:
            await reply_message.edit("❌ Error downloading the file.")
            return

        _song = PlatformTracks(
            tracks=[
                MusicTrack(
                    name=telegram.get_file_name(),
                    artist="AshokShau",
                    id=reply.media.document.id,
                    year=0,
                    cover="",
                    duration=await get_audio_duration(file_path),
                    platform="telegram",
                )
            ]
        )

        await play_music(client, reply_message, _song, user_by, file_path)
        return

    if url:
        if wrapper.is_valid(url):
            _song = await wrapper.get_info()
            if not _song:
                await reply_message.edit(
                    "❌ Unable to retrieve song info.\n\nPlease report this issue if you think it's a bug.",
                    buttons=SupportButton,
                )
                return

            await play_music(client, reply_message, _song, user_by)
            return

        await reply_message.edit(
            "❌ Invalid URL! Provide a valid link.",
            buttons=SupportButton,
        )
        return

    # Handle text-based search
    play_type = await db.get_play_type(chat_id)
    search = await wrapper.search()
    if not search:
        await reply_message.edit(
            "❌ No results found. Please report this issue if you think it's a bug.",
            buttons=SupportButton,
        )
        return

    platform = search.tracks[0].platform

    if play_type == 0:
        _song_id = search.tracks[0].id
        url = _get_platform_url(platform, _song_id)
        if _song := await MusicServiceWrapper(url).get_info():
            await play_music(client, reply_message, _song, user_by)
            return

        await reply_message.edit(
            "❌ Unable to retrieve song info.",
            buttons=SupportButton,
        )
        return

    buttons = [
        [Button.inline(f"{rec.name[:18]} - {rec.artist}", data=f"play_{platform}_{rec.id}")]
        for rec in search.tracks[:4]
    ]

    await reply_message.edit(
        f"{user_by}, select a song to play:",
        buttons=buttons,
        link_preview=False,
        parse_mode='html',
)
