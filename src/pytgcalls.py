import asyncio
import os
import random
import re
from types import NoneType
from typing import Optional

from telethon import TelegramClient, events
from telethon.errors import ChatAdminRequiredError
from telethon.tl.functions.phone import CreateGroupCallRequest, DiscardGroupCallRequest
from telethon.tl.types import InputPeerChannel, InputPeerChat
from pytgcalls import PyTgCalls, exceptions
from pytgcalls.types import (
    MediaStream,
    Update,
    stream,
    VideoQuality,
    AudioQuality,
    ChatUpdate,
    UpdatedGroupCallParticipant,
)

from pyUltroid.configs import Var
from src.database import db
from src.logger import LOGGER
from src.modules.utils import sec_to_min, get_audio_duration
from src.modules.utils.buttons import play_button, update_progress_bar
from src.modules.utils.cacher import chat_cache
from src.modules.utils.thumbnails import gen_thumb
from src.platforms.dataclass import CachedTrack
from src.platforms.downloader import MusicServiceWrapper, YouTubeData, SpotifyData

async def start_clients() -> None:
    """Start Telethon clients."""
    session = [s for s in Var.SESSION if s]
    if not session_strings:
        LOGGER.error("No STRING session provided. Exiting...")
        raise SystemExit(1)

    try:
        await asyncio.gather(
            *[
                call.start_client(Var.API_ID, Var.API_HASH, s)
                for s in session
            ]
        )
        LOGGER.info("✅ Clients started successfully.")
    except Exception as exc:
        LOGGER.error(f"Error starting clients: {exc}", exc_info=True)
        raise SystemExit(1) from exc


class CallError(Exception):
    def __init__(self, errr: str):
        super().__init__(errr)


class MusicBot:
    def __init__(self):
        self.calls: dict[str, TelegramClient] = {}
        self.client_counter: int = 1
        self.available_clients: list[str] = []
        self.bot: Optional[TelegramClient] = None

    async def add_bot(self, c: TelegramClient):
        """Add the main bot client."""
        self.bot = c

    async def _get_client_name(self, chat_id: int) -> str:
    """Get the associated client for a specific chat ID."""
    if chat_id == 1:
        # if chat_id is 1, return a random available client
        if self.available_clients:
            return random.choice(self.available_clients)
        else:
            LOGGER.error("No available clients to assign for chat_id 1")
            raise RuntimeError("No available clients to assign!")

    # for groups
    _ub = await db.get_assistant(chat_id)
    if _ub and _ub in self.available_clients:
        return _ub

    if self.available_clients:
        new_client = random.choice(self.available_clients)
        await db.set_assistant(chat_id, assistant=new_client)
        return new_client

    LOGGER.error(f"No available clients to assign for chat_id {chat_id}")
    
        raise RuntimeError("No available clients to assign!")

    async def get_client(self, chat_id: int) -> TelegramClient:
        """Get the Telethon client for a specific chat ID."""
        client_name = await self._get_client_name(chat_id)
        return self.calls[client_name]

    async def start_client(
            self, api_id: int, api_hash: str, session_string: str
    ) -> None:
        client_name = f"client{self.client_counter}"
        user_bot = TelegramClient(session_string, api_id, api_hash)
        await user_bot.start()
        self.calls[client_name] = user_bot
        self.available_clients.append(client_name)
        self.client_counter += 1
        LOGGER.info(f"Client {client_name} started successfully")

    async def register_decorators(self):
        """Register event handlers for all clients."""
        for client in self.calls.values():

            @client.on(events.Raw)
            async def general_handler(event):
                LOGGER.debug(f"Received event: {event}")
                # Add your event handling logic here

    async def play_media(
            self,
            chat_id: int,
            file_path: str,
            video: bool = False,
            ffmpeg_parameters: Optional[str] = None,
    ):
        """Play media on a specific client."""
        LOGGER.info(f"Playing media for chat {chat_id}: {file_path}")
        
        try:
            client = await self.get_client(chat_id)
            await client(CreateGroupCallRequest(
                peer=InputPeerChat(chat_id),
                title="Music Bot Call",
            ))
            # Implement the logic to play media using ffmpeg and ffmpeg_parameters
        except (ChatAdminRequiredError) as e:
            await chat_cache.clear_chat(chat_id)
            raise CallError(
                "No active group call \nPlease start a call and try again"
            ) from e
        except Exception as e:
            LOGGER.exception(
                f"Error playing media for chat {chat_id}: {e}", exc_info=True
            )
            raise CallError(f"Error playing media: {e}") from e

    async def play_next(self, chat_id: int):
        """Handles song queue logic."""
        LOGGER.info(f"Playing next song for chat {chat_id}")
        loop = await chat_cache.get_loop_count(chat_id)
        if loop > 0:
            await chat_cache.set_loop_count(chat_id, loop - 1)
            if current_song := await chat_cache.get_current_song(chat_id):
                await self._play_song(chat_id, current_song)
                return

        if next_song := await chat_cache.get_next_song(chat_id):
            await chat_cache.remove_current_song(chat_id)
            await self._play_song(chat_id, next_song)
        else:
            await self._handle_no_songs(chat_id)

    async def _play_song(self, chat_id: int, song):
        """Download and play a song."""
        LOGGER.info(f"Playing song for chat {chat_id}")
        try:
            reply = await self.bot.send_message(
                chat_id, "⏹️ Loading... Please wait."
            )

            file_path = song.file_path or await self.song_download(song)
            if not file_path:
                await reply.edit("❌ Error downloading song. Playing next...")
                await self.play_next(chat_id)
                return

            await self.play_media(chat_id, file_path)
            text = f"<b>Now playing <a href='{song.thumbnail or 'https://t.me/FallenProjects'}'>:</a></b>\n\n‣ <b>Title:</b> {song.name}\n‣<b>Duration:</b> {sec_to_min(song.duration) or await get_audio_duration(file_path)}\n‣<b>Requested by:</b> {song.user}"
            thumb = await gen_thumb(song)
            reply = await self.bot.edit_message(
                chat_id,
                reply.id,
                file=thumb,
                text=text,
                buttons=play_button(0, song.duration),
            )

            await update_progress_bar(self.bot, reply, 3, song.duration)
        except Exception as e:
            LOGGER.error(f"Error playing song for chat {chat_id}: {e}")

    @staticmethod
    async def song_download(song: CachedTrack) -> Optional[str]:
        """Handles song downloading."""
        _track_id = song.track_id
        _platform = song.platform
        if _platform == "telegram":
            pass
        elif _platform == "youtube":
            youtube = YouTubeData(_track_id)
            if track := await youtube.get_track():
                return await youtube.download_track(track)
        elif _platform == "spotify":
            spotify = SpotifyData(_track_id)
            if track := await spotify.get_track():
                return await spotify.download_track(track)
        else:
            LOGGER.error(f"Unknown platform: {_platform}")

        return None

    async def _handle_no_songs(self, chat_id: int):
        """Handles the case when there are no songs left in the queue."""
        try:
            await self.end(chat_id)
            if recommendations := await MusicServiceWrapper().get_recommendations():
                platform = recommendations.tracks[0].platform
                buttons = [
                    [
                        types.InlineKeyboardButton(
                            f"{track.name[:18]} - {track.artist}",
                            data=f"play_{platform}_{track.id}".encode()
                        )
                    ]
                    for track in recommendations.tracks
                ]

                reply = await self.bot.send_message(
                    chat_id,
                    text="No more songs in queue. Here are some recommendations for you:\n\n",
                    buttons=buttons,
                )

                return

            reply = await self.bot.send_message(
                chat_id, text="No more songs in queue. Use /play to add some."
            )

        except Exception as e:
            LOGGER.warning(
                f"Error handling empty queue for chat {chat_id}: {e}", exc_info=True
            )

    async def end(self, chat_id: int):
        """Ends the current call."""
        LOGGER.info(f"Ending call for chat {chat_id}")
        try:
            await chat_cache.clear_chat(chat_id)
            client = await self.get_client(chat_id)
            await client(DiscardGroupCallRequest(
                call=InputPeerChat(chat_id)
            ))
        except Exception as e:
            LOGGER.error(f"Error ending call for chat {chat_id}: {e}")

    async def seek_stream(self, chat_id, file_path_or_url, to_seek, duration):
        """Seek to a specific position in the stream."""

        def is_url(path):
            return bool(re.match(r"http(s)?://", path))

        if is_url(file_path_or_url) or not os.path.isfile(file_path_or_url):
            ffmpeg_params = f"-ss {to_seek} -i {file_path_or_url} -to {duration}"
        else:
            ffmpeg_params = f"-ss {to_seek} -to {duration}"

        await self.play_media(
            chat_id, file_path_or_url, ffmpeg_parameters=ffmpeg_params
        )

    async def speed_change(self, chat_id, speed=1.0):
        """
        Change the speed of the current call.
        Supports speed factors from 0.5x to 4.0x.
        """
        if speed < 0.5 or speed > 4.0:
            raise ValueError("Speed must be between 0.5 and 4.0.")

        curr_song = await chat_cache.get_current_song(chat_id)
        if not curr_song:
            raise ValueError("No song is currently playing in this chat!")

        file_path = curr_song.file_path
        return await self.play_media(chat_id, file_path, ffmpeg_parameters=f"-atend -filter:v setpts=0.5*PTS -filter:a atempo={speed}")

    async def change_volume(self, chat_id, volume):
        """Change the volume of the current call."""
        client = await self.get_client(chat_id)
        # Implement volume change logic using ffmpeg or another method

    async def mute(self, chat_id):
        """Mute the current call."""
        client = await self.get_client(chat_id)
        await client.mute_call()

    async def unmute(self, chat_id):
        """Unmute the current call."""
        LOGGER.info(f"un-mute stream for chat {chat_id}")
        client = await self.get_client(chat_id)
        await client.unmute_call()

    async def resume(self, chat_id):
        """Resume the current call."""
        LOGGER.info(f"Resuming stream for chat {chat_id}")
        client = await self.get_client(chat_id)
        await client.resume_call()

    async def pause(self, chat_id):
        """Pause the current call."""
        LOGGER.info(f"Pausing stream for chat {chat_id}")
        client = await self.get_client(chat_id)
        await client.pause_call()

    async def played_time(self, chat_id):
        """Get the played time of the current call."""
        LOGGER.info(f"Getting played time for chat {chat_id}")
        client = await self.get_client(chat_id)

        try:
            return await client.get_played_time(chat_id)
        except Exception as e:
            await chat_cache.clear_chat(chat_id)
            return 0

    async def vc_users(self, chat_id):
        """Get the list of participants in the current call."""
        LOGGER.info(f"Getting VC users for chat {chat_id}")
        client = await self.get_client(chat_id)
        return await client.get_participants(chat_id)

    async def stats_call(self, chat_id: int) -> tuple[float, float]:
        """Get call statistics (ping and CPU usage)."""
        client = await self.get_client(chat_id)
        return client.ping, await client.cpu_usage()


call: MusicBot = MusicBot()
