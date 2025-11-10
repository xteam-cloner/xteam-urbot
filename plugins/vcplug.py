from __future__ import annotations

import asyncio
import os
import re
import tempfile
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import httpx
# Pastikan semua impor Ultroid ini ada di dalam file vc_music.py Anda
from . import *
from telethon import events
from telethon.tl.types import Message
# Tambahkan impor vcClient dari pyUltroid sesuai struktur yang Anda berikan
try:
    from xteam import vcClient
except ImportError:
    # Fallback jika struktur import Ultroid berbeda (sangat penting)
    vcClient = None
    pass 

from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream 
from pytgcalls import filters as fl
from ntgcalls import TelegramServerError
from pytgcalls.exceptions import NoActiveGroupCall, InvalidMTProtoClient 
from pytgcalls.types import (
    ChatUpdate,
    StreamEnded,
    GroupCallConfig,
    GroupCallParticipant,
    UpdatedGroupCallParticipant,
    AudioQuality,
    VideoQuality,
)
import yt_dlp
from youtubesearchpython.__future__ import VideosSearch

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
        """Return (path_or_url, is_local)"""
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
# VC Manager (Perbaikan Inisialisasi menggunakan vcClient)
# ─────────────────────────────────────────────────────────────

class VCManager:
    # Menerima main_client (untuk pesan) dan vc_client (untuk voice chat)
    def __init__(self, main_client, vc_client):
        self.client = main_client
        self.vc_client = vc_client # <-- Klien khusus PyTgCalls
        self.tgcalls: Optional[PyTgCalls] = None 
        self.states: Dict[int, VCState] = {}
        self.started = False
        self.resolver = YouTubeResolver()

    async def ensure_initialized(self):
        """Metode aman untuk inisialisasi PyTgCalls dengan vcClient."""
        if self.tgcalls is None:
            if not self.vc_client:
                raise RuntimeError("vcClient tidak tersedia. Pastikan impor 'from pyUltroid import vcClient' berhasil.")

            # Pastikan vcClient sudah terhubung
            if not self.vc_client.is_connected():
                await self.vc_client.start()
                
            # Inisialisasi PyTgCalls DENGAN vcClient
            try:
                self.tgcalls = PyTgCalls(self.vc_client) 
            except InvalidMTProtoClient as e:
                raise RuntimeError(f"Gagal inisialisasi PyTgCalls: Klien VC tidak valid. Coba perbarui pytgcalls/telethon/Ultroid.") from e

            @self.tgcalls.on_stream_end()
            async def on_end(_, update):
                chat_id = update.chat_id
                await self._on_track_end(chat_id)

            await self.tgcalls.start()
            self.started = True
            
        return self

    def state(self, chat_id: int) -> VCState:
        if chat_id not in self.states:
            self.states[chat_id] = VCState()
        return self.states[chat_id]

    async def leave(self, chat_id: int):
        if not self.tgcalls: return
        try:
            await self.tgcalls.leave_group_call(chat_id)
        except Exception:
            pass
        self.states.pop(chat_id, None)

    def _build_stream(self, src: str, vol_percent: int, is_local: bool) -> MediaStream:
        """Membangun objek MediaStream."""
        gain_db = 6.0 * (vol_percent / 100.0 - 1.0)
        
        if is_local:
            stream = MediaStream.file(src) 
        else:
            stream = MediaStream.url(src)

        if hasattr(stream, 'additional_ffmpeg_parameters'):
            stream.additional_ffmpeg_parameters = ["-af", f"volume={gain_db}dB"]
        
        return stream

    async def _start_stream(self, chat_id: int, track: Track):
        st = self.state(chat_id)
        st.now_playing = track
        if not self.tgcalls:
            raise RuntimeError("VCManager belum diinisialisasi. Coba jalankan .vcjoin terlebih dahulu.")
            
        is_local = os.path.exists(track.source)
        stream = self._build_stream(track.source, st.volume, is_local)
        
        try:
            await self.tgcalls.join_group_call(chat_id, stream)
        except Exception:
            await self.tgcalls.change_stream(chat_id, stream)

    async def play(self, chat_id: int, track: Track):
        st = self.state(chat_id)
        async with st.lock:
            if st.now_playing is None:
                await self._start_stream(chat_id, track)
            else:
                st.queue.push(track)
                
    async def _on_track_end(self, chat_id: int):
        st = self.state(chat_id)
        async with st.lock:
            nxt = st.queue.pop()
            if nxt:
                await self._start_stream(chat_id, nxt)
            else:
                st.now_playing = None
                if self.tgcalls:
                    try:
                        await self.tgcalls.leave_group_call(chat_id)
                    except Exception:
                        pass

    async def pause(self, chat_id: int):
        if not self.tgcalls: return
        await self.tgcalls.pause_stream(chat_id)

    async def resume(self, chat_id: int):
        if not self.tgcalls: return
        await self.tgcalls.resume_stream(chat_id)

    async def stop(self, chat_id: int):
        st = self.state(chat_id)
        st.queue.clear()
        st.now_playing = None
        if self.tgcalls:
            try:
                await self.tgcalls.leave_group_call(chat_id)
            except Exception:
                pass

# Singleton manager
_vc: Optional[VCManager] = None


def _cid(e: Message) -> int:
    return e.chat_id

# Fungsi _manager diubah menjadi async dan meneruskan vcClient
async def _manager(e) -> VCManager:
    global _vc
    if _vc is None:
        # PENTING: Meneruskan klien Ultroid dan klien VC yang diimpor
        _vc = VCManager(e.client, vcClient) 
    return await _vc.ensure_initialized() 

# ─────────────────────────────────────────────────────────────
# Commands (Semua memanggil _manager(e) dengan await)
# ─────────────────────────────────────────────────────────────


@ultroid_cmd(pattern="vcjoin$", groups_only=True)
async def vc_join(e: Message):
    try:
        _ = await _manager(e) 
        await e.eor("VC ready. Use `.vcplay <query|url>` or reply to media.")
    except Exception as ex:
        await e.eor(f"Error: `{ex}`")


@ultroid_cmd(pattern="vcleave$", groups_only=True)
async def vc_leave(e: Message):
    try:
        mgr = await _manager(e)
        await mgr.leave(_cid(e))
        await e.eor("Left VC.")
    except Exception as ex:
        await e.eor(f"`{ex}`")


@ultroid_cmd(pattern=r"vcplay(?:\s+(.+))?$", groups_only=True)
async def vc_play(e: Message):
    chat_id = _cid(e)
    arg = (e.pattern_match.group(1) or "").strip()

    msg = await e.eor("Resolving & downloading…")
    
    try:
        mgr = await _manager(e)
        
        if e.is_reply and not arg:
            r = await e.get_reply_message()
            if r and (r.audio or r.voice or r.video or r.document):
                path = await e.client.download_media(r, file=DOWNLOAD_DIR)
                await mgr.play(chat_id, Track(title=os.path.basename(path), source=path, requested_by=str(e.sender_id)))
                return await msg.edit("Queued replied media.")
            else:
                 return await msg.edit("Usage: `.vcplay <url|query>` or reply to media (audio/video/document).")


        if not arg:
            return await msg.edit("Usage: `.vcplay <url|query>` or reply to media.")

        src, is_local = await mgr.resolver.download_audio_to_path(arg)
        title = await mgr.resolver.extract_title(arg)
        await mgr.play(chat_id, Track(title=title, source=src, requested_by=str(e.sender_id)))
        await msg.edit(f"Queued: **{title}** {'(local)' if is_local else '(stream)'}")
    except Exception as ex:
        await msg.edit(f"`{ex}`")


@ultroid_cmd(pattern="vcpause$", groups_only=True)
async def vc_pause(e: Message):
    try:
        await (await _manager(e)).pause(_cid(e)) 
        await e.eor("Paused.")
    except Exception as ex:
        await e.eor(f"`{ex}`")


@ultroid_cmd(pattern="vcresume$", groups_only=True)
async def vc_resume(e: Message):
    try:
        await (await _manager(e)).resume(_cid(e))
        await e.eor("Resumed.")
    except Exception as ex:
        await e.eor(f"`{ex}`")


@ultroid_cmd(pattern="vcskip$", groups_only=True)
async def vc_skip(e: Message):
    try:
        await (await _manager(e))._on_track_end(_cid(e))
        await e.eor("Skipped.")
    except Exception as ex:
        await e.eor(f"`{ex}`")


@ultroid_cmd(pattern="vcstop$", groups_only=True)
async def vc_stop(e: Message):
    try:
        await (await _manager(e)).stop(_cid(e))
        await e.eor("Stopped and cleared queue.")
    except Exception as ex:
        await e.eor(f"`{ex}`")


@ultroid_cmd(pattern="vcnp$", groups_only=True)
async def vc_now_playing(e: Message):
    st = (await _manager(e)).state(_cid(e))
    if st.now_playing:
        await e.eor(f"Now playing: **{st.now_playing.title}**")
    else:
        await e.eor("Nothing is playing.")


@ultroid_cmd(pattern="vcqueue$", groups_only=True)
async def vc_queue(e: Message):
    st = (await _manager(e)).state(_cid(e))
    if not len(st.queue):
        return await e.eor("Queue is empty.")
    lines = [f"{i+1}. {t.title}" for i, t in enumerate(st.queue.as_list())]
    await e.eor("Upcoming:\n" + "\n".join(lines))


@ultroid_cmd(pattern=r"vcvol(?:\s+(\d{1,3}))?$", groups_only=True)
async def vc_volume(e: Message):
    arg = e.pattern_match.group(1)
    mgr = await _manager(e)
    
    if arg is None:
        v = mgr.state(_cid(e)).volume
        return await e.eor(f"Current volume: **{v}%** (applies to next track)")
    try:
        v = min(200, max(0, int(arg)))
    except ValueError:
        return await e.eor("Give a number 0-200.")
        
    mgr.state(_cid(e)).volume = v
    await e.eor(f"Volume set to **{v}%** for next track.")

@ultroid_cmd(pattern=r"play(?:\s+(.+))?$", groups_only=True)
async def vc_play_alias(e: Message):
    chat_id = _cid(e)
    arg = (e.pattern_match.group(1) or "").strip()
    
    msg = await e.eor("Resolving & downloading…")
    
    try:
        mgr = await _manager(e)
        
        if e.is_reply and not arg:
            r = await e.get_reply_message()
            if r and (r.audio or r.voice or r.video or r.document):
                path = await e.client.download_media(r, file=DOWNLOAD_DIR)
                await mgr.play(chat_id, Track(title=os.path.basename(path), source=path, requested_by=str(e.sender_id)))
                return await msg.edit("Queued replied media.")
            else:
                 return await msg.edit("Usage: `.play <url|query>` or reply to media (audio/video/document).")
                 
        if not arg:
            return await msg.edit("Usage: `.play <url|query>` or reply to media.")
    
        src, is_local = await mgr.resolver.download_audio_to_path(arg)
        title = await mgr.resolver.extract_title(arg)
        await mgr.play(chat_id, Track(title=title, source=src, requested_by=str(e.sender_id)))
        await msg.edit(f"Queued: **{title}** {'(local)' if is_local else '(stream)'}")
    except Exception as ex:
        await msg.edit(f"`{ex}`")
    
