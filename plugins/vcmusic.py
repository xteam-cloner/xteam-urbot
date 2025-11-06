# Ultroid VC Music Plugin using PyTgCalls + Bitflow/yt-dlp resolver
# Drop this file into your Ultroid plugins folder as `vc_music.py`.
#
# Requirements (install globally or in venv used by Ultroid):
#   pip install pyrogram tgshell pytgcalls yt-dlp httpx youtubesearchpython
#
# Commands (send from your user account):
#   .vcjoin                      — init VC context (stream starts on first play)
#   .vcleave                     — leave VC & clear state for this chat
#   .vcplay <url|query>|(reply)  — download (via API/yt-dlp) & play audio
#   .vcpause / .vcresume         — pause/resume stream
#   .vcskip                      — skip current track
#   .vcstop                      — stop playback & clear queue
#   .vcnp                        — show now playing
#   .vcqueue                     — show upcoming queue
#   .vcvol <0-200>               — set volume (applies to next track)


from __future__ import annotations

import asyncio
import os
import re
import tempfile
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import httpx

from telethon import events, TelegramClient
from telethon.tl.types import Message
from telethon.sessions import StringSession

# ⚠️ BLOCK IMPOR PYTGCALLS
try:
    from pytgcalls import PyTgCalls
    from pytgcalls import filters as fl
    from ntgcalls import TelegramServerError
    from pytgcalls.exceptions import NoActiveGroupCall
    from pytgcalls.types import (
        ChatUpdate, MediaStream, StreamEnded, GroupCallConfig,
        GroupCallParticipant, UpdatedGroupCallParticipant, AudioQuality,
        VideoQuality,
    )
except Exception:
    PyTgCalls = None
    MediaStream = None
    NoActiveGroupCall = Exception
    class TelegramServerError(Exception): pass
# ⚠️ END BLOCK IMPOR PYTGCALLS

# ⚠️ BLOCK IMPOR PYROGRAM
try:
    from pyrogram import Client
except Exception as e:
    Client = None
    # Jika gagal, pastikan pyrogram sudah terinstal
# ⚠️ END BLOCK IMPOR PYROGRAM


try:
    import yt_dlp
except Exception:
    yt_dlp = None

try:
    from youtubesearchpython.__future__ import VideosSearch
except Exception:
    VideosSearch = None

from . import ultroid_cmd

YOUTUBE_REGEX = r"(?:youtube\.com|youtu\.be)"
BITFLOW_API = "https://bitflow.in/api/youtube"
BITFLOW_API_KEY = "youtube321bot"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")

# ─────────────────────────────────────────────────────────────
# Queue/State
# ─────────────────────────────────────────────────────────────

@dataclass
class Track:
    title: str
    source: str
    requested_by: str

class Queue:
    def __init__(self):
        self._q = []
    def push(self, t: Track):
        self._q.append(t)
    def pop(self) -> Optional[Track]:
        return self._q.pop(0) if self._q else None
    def peek(self) -> Optional[Track]:
        return self._q[0] if self._q else None
    def clear(self):
        self._q.clear()
    def __len__(self):
        return len(self._q)
    def as_list(self):
        return list(self._q)

class VCState:
    def __init__(self):
        self.queue = Queue()
        self.now_playing: Optional[Track] = None
        self.lock = asyncio.Lock()
        self.volume = 100

# ─────────────────────────────────────────────────────────────
# Resolver: Bitflow API + yt-dlp
# ─────────────────────────────────────────────────────────────

class YouTubeResolver:
    def __init__(self):
        if yt_dlp is None:
            raise RuntimeError("yt-dlp is required. Install with: pip install yt-dlp")
        if not os.path.isdir(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    async def _bitflow(self, url: str, want_video: bool = False) -> Optional[dict]:
        params = {
            "query": url,
            "format": "video" if want_video else "audio",
            "download": True,
            "api_key": BITFLOW_API_KEY,
        }
        try:
            async with httpx.AsyncClient(timeout=150) as cli:
                r = await cli.get(BITFLOW_API, params=params)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and data.get("status") in ("ok", True):
                    return data
        except Exception:
            pass
        return None

    async def _search_to_url(self, query: str) -> str:
        if re.search(r"^https?://", query):
            return query
        q = f"ytsearch1:{query.strip()}"
        return q

    async def download_audio_to_path(self, query_or_url: str) -> Tuple[str, bool]:
        target = await self._search_to_url(query_or_url)
        bf = await self._bitflow(target, want_video=False)
        if bf and bf.get("url") and bf.get("videoid"):
            filename = os.path.join(DOWNLOAD_DIR, f"{bf['videoid']}.{bf.get('ext','m4a')}")
            if not os.path.exists(filename):
                opts = {
                    "format": "bestaudio/best",
                    "outtmpl": filename,
                    "geo_bypass": True,
                    "nocheckcertificate": True,
                    "quiet": True,
                    "no_warnings": True,
                }
                def _dl():
                    with yt_dlp.YoutubeDL(opts) as y:
                        y.download([bf["url"]])
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, _dl)
            return filename, True

        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "-g", "-f", "bestaudio/best", target,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        url = stdout.decode().split("\n")[0].strip() if stdout else ""
        if url:
            return url, False

        err = (stderr or b"unknown error").decode()
        raise RuntimeError(f"Failed to resolve audio: {err}")

    async def extract_title(self, query_or_url: str) -> str:
        opts = {"quiet": True, "skip_download": True}
        with yt_dlp.YoutubeDL(opts) as y:
            info = y.extract_info(await self._search_to_url(query_or_url), download=False)
            if isinstance(info, dict) and "entries" in info:
                info = info["entries"][0]
            return info.get("title") or "Unknown Title"

# ─────────────────────────────────────────────────────────────
# VC Manager
# ─────────────────────────────────────────────────────────────

class VCManager:
    def __init__(self, client):
        if PyTgCalls is None:
            raise RuntimeError("pytgcalls is not installed. Run: pip install pytgcalls")
        if Client is None:
            raise RuntimeError("pyrogram is not installed. Run: pip install pyrogram") # 🔑 Pengecekan Pyrogram

        self.client = client # Klien Telethon Ultroid
        self.pyro_client = None # Klien Pyrogram untuk PyTgCalls
        self.tgcalls = None
        self.states: Dict[int, VCState] = {}
        self.started = False
        self.resolver = YouTubeResolver()

        asyncio.create_task(self._on_client_ready())

    async def _on_client_ready(self):
        # 1. Pastikan klien Telethon Ultroid terhubung penuh
        max_retries = 10
        for i in range(max_retries):
            try:
                await self.client.get_me() 
                break
            except Exception:
                await asyncio.sleep(3) 
        else:
            print("Failed to ensure Telethon client readiness. Cannot proceed.")
            return

        if not self.started:
            try:
                # 2. 🔑 PERBAIKAN: Buat Klien Pyrogram terpisah menggunakan file sesi Pyrogram.
                # String sesi Telethon TIDAK kompatibel.
                
                # Dapatkan kredensial dari klien Telethon yang sudah login
                api_id = self.client.api_id
                api_hash = self.client.api_hash
                
                # Inisialisasi Klien Pyrogram baru. 
                # Pyrogram akan membuat/menggunakan file sesi lokal bernama 'ultroid_vc_music.session'.
                self.pyro_client = Client(
                    "ultroid_vc_music", # Nama sesi Pyrogram (argumen posisional pertama)
                    api_id=api_id,
                    api_hash=api_hash,
                    # session_string dan in_memory dihilangkan
                )
                
                # Koneksikan klien Pyrogram secara eksplisit (Ini akan melakukan login/load sesi)
                await self.pyro_client.start()

                # 3. Meneruskan klien Pyrogram ke PyTgCalls
                self.tgcalls = PyTgCalls(self.pyro_client) 
                
                # Daftarkan handler on_stream_end
                @self.tgcalls.on_stream_end()
                async def on_end(_, update):
                    chat_id = update.chat_id
                    await self._on_track_end(chat_id)
                
                await self.tgcalls.start()
                self.started = True
                print("PyTgCalls successfully started using Pyrogram client.")
                
            except Exception as e:
                # Jika masih gagal, mungkin ada masalah dengan sesi atau versi library
                print(f"Failed to start PyTgCalls (using Pyrogram): {e}")
                self.tgcalls = None

    def state(self, chat_id: int) -> VCState:
        if chat_id not in self.states:
            self.states[chat_id] = VCState()
        return self.states[chat_id]

    async def leave(self, chat_id: int):
        if self.tgcalls is None: return
        try:
            await self.tgcalls.leave_group_call(chat_id)
        except NoActiveGroupCall: 
            pass
        except Exception:
            pass
        self.states.pop(chat_id, None)

    async def play(self, chat_id: int, track: Track):
        if self.tgcalls is None: raise RuntimeError("VC Manager is not initialized. Try .vcjoin again.")
        st = self.state(chat_id)
        async with st.lock:
            if st.now_playing is None:
                await self._start_stream(chat_id, track)
            else:
                st.queue.push(track)

    def _build_stream(self, src: str, vol_percent: int, is_local: bool) -> MediaStream:
        gain_db = 6.0 * (vol_percent / 100.0 - 1.0)
        
        return MediaStream(
            src,
            audio_parameters=["-af", f"volume={gain_db}dB"],
        )

    async def _start_stream(self, chat_id: int, track: Track):
        st = self.state(chat_id)
        st.now_playing = track
        is_local = os.path.exists(track.source)
        stream = self._build_stream(track.source, st.volume, is_local)
        try:
            await self.tgcalls.join_group_call(chat_id, stream)
        except Exception:
            await self.tgcalls.change_stream(chat_id, stream)

    async def _on_track_end(self, chat_id: int):
        if self.tgcalls is None: return
        st = self.state(chat_id)
        async with st.lock:
            nxt = st.queue.pop()
            if nxt:
                await self._start_stream(chat_id, nxt)
            else:
                st.now_playing = None
                try:
                    await self.tgcalls.leave_group_call(chat_id)
                except NoActiveGroupCall: 
                    pass
                except Exception:
                    pass

    async def pause(self, chat_id: int):
        if self.tgcalls is None: return
        await self.tgcalls.pause_stream(chat_id)

    async def resume(self, chat_id: int):
        if self.tgcalls is None: return
        await self.tgcalls.resume_stream(chat_id)

    async def stop(self, chat_id: int):
        if self.tgcalls is None: return
        st = self.state(chat_id)
        st.queue.clear()
        st.now_playing = None
        try:
            await self.tgcalls.leave_group_call(chat_id)
        except NoActiveGroupCall: 
            pass
        except Exception:
            pass

# Singleton manager
_vc: Optional[VCManager] = None


def _manager(e) -> VCManager:
    global _vc
    if _vc is None:
        _vc = VCManager(e.client) 
    return _vc

# ─────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────


def _cid(e: Message) -> int:
    return e.chat_id


@ultroid_cmd(pattern="vcjoin$", groups_only=True)
async def vc_join(e: Message):
    mgr = _manager(e)
    # Pemeriksaan untuk memastikan PyTgCalls sudah diinisialisasi
    if mgr.tgcalls is None:
        return await e.eor("VC Manager sedang inisialisasi. Tunggu sebentar atau pastikan klien Ultroid Anda sudah *login* dan siap.")
        
    await e.eor("VC ready. Gunakan `.vcplay <query|url>` atau *reply* ke media.")


@ultroid_cmd(pattern="vcleave$", groups_only=True)
async def vc_leave(e: Message):
    try:
        await _manager(e).leave(_cid(e))
        await e.eor("Left VC.")
    except Exception as ex:
        await e.eor(f"`{ex}`")


@ultroid_cmd(pattern=r"vcplay(?:\s+(.+))?$", groups_only=True)
async def vc_play(e: Message):
    chat_id = _cid(e)
    arg = (e.pattern_match.group(1) or "").strip()

    mgr = _manager(e)
    if mgr.tgcalls is None:
        return await e.eor("VC Manager belum siap. Coba lagi atau pastikan klien sudah *login*.")

    # If reply to media: download and play that file directly
    if e.is_reply and not arg:
        r = await e.get_reply_message()
        if r and (r.audio or r.voice or r.video or r.document):
            msg = await e.eor("Downloading replied media…")
            path = await e.client.download_media(r, file=DOWNLOAD_DIR)
            await mgr.play(chat_id, Track(title=os.path.basename(path), source=path, requested_by=str(e.sender_id)))
            return await msg.edit("Queued replied media.")

    if not arg:
        return await e.eor("Usage: `.vcplay <url|query>` or reply to media.")

    msg = await e.eor("Resolving & downloading…")
    
    try:
        # Resolve and prefer local audio path
        src, is_local = await mgr.resolver.download_audio_to_path(arg)
        title = await mgr.resolver.extract_title(arg)
        await mgr.play(chat_id, Track(title=title, source=src, requested_by=str(e.sender_id)))
        await msg.edit(f"Queued: **{title}** {'(local)' if is_local else '(stream)'}")
    except Exception as ex:
        await msg.edit(f"`{ex}`")


@ultroid_cmd(pattern="vcpause$", groups_only=True)
async def vc_pause(e: Message):
    try:
        await _manager(e).pause(_cid(e))
        await e.eor("Paused.")
    except Exception as ex:
        await e.eor(f"`{ex}`")


@ultroid_cmd(pattern="vcresume$", groups_only=True)
async def vc_resume(e: Message):
    try:
        await _manager(e).resume(_cid(e))
        await e.eor("Resumed.")
    except Exception as ex:
        await e.eor(f"`{ex}`")


@ultroid_cmd(pattern="vcskip$", groups_only=True)
async def vc_skip(e: Message):
    try:
        await _manager(e)._on_track_end(_cid(e))
        await e.eor("Skipped.")
    except Exception as ex:
        await e.eor(f"`{ex}`")


@ultroid_cmd(pattern="vcstop$", groups_only=True)
async def vc_stop(e: Message):
    try:
        await _manager(e).stop(_cid(e))
        await e.eor("Stopped and cleared queue.")
    except Exception as ex:
        await e.eor(f"`{ex}`")


@ultroid_cmd(pattern="vcnp$", groups_only=True)
async def vc_now_playing(e: Message):
    st = _manager(e).state(_cid(e))
    if st.now_playing:
        await e.eor(f"Now playing: **{st.now_playing.title}**")
    else:
        await e.eor("Nothing is playing.")


@ultroid_cmd(pattern="vcqueue$", groups_only=True)
async def vc_queue(e: Message):
    st = _manager(e).state(_cid(e))
    if not len(st.queue):
        return await e.eor("Queue is empty.")
    lines = [f"{i+1}. {t.title}" for i, t in enumerate(st.queue.as_list())]
    await e.eor("Upcoming:\n" + "\n".join(lines))


@ultroid_cmd(pattern=r"vcvol(?:\s+(\d{1,3}))?$", groups_only=True)
async def vc_volume(e: Message):
    arg = e.pattern_match.group(1)
    if arg is None:
        v = _manager(e).state(_cid(e)).volume
        return await e.eor(f"Current volume: **{v}%** (applies to next track)")
    try:
        v = min(200, max(0, int(arg)))
    except ValueError:
        return await e.eor("Give a number 0-200.")
    _manager(e).state(_cid(e)).volume = v
    await e.eor(f"Volume set to **{v}%** for next track.")
    
