# vctools.py - Plugin Musik VC Ultroid (Versi Final yang Diperbaiki)

from __future__ import annotations

import asyncio
import os
import re
import contextlib 
import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any

import httpx
# Impor umum:
from . import * 
from telethon import events, TelegramClient 
from telethon.tl.types import Message
from xteam.configs import Var 
from xteam import vc_call # 🌟 HARUS DIIMPOR DARI xteam (Ini adalah PyTgCalls Client)
from xteam import ultroid_bot 

# Impor Dependensi Kritis (Biarkan Python yang memberikan ImportError jika gagal)
# Jika ini gagal, berarti instalasi pytgcalls GAGAL, yang merupakan masalah di luar kode ini.
from pytgcalls import PyTgCalls
#from pytgcalls.types import AudioPiped, StreamType
#from pytgcalls import PyTgCalls, filters
from pytgcalls.types import Update, MediaStream

import yt_dlp
from youtubesearchpython.__future__ import VideosSearch

from . import ultroid_cmd
logger = logging.getLogger(__name__)

# --- KONSTANTA & KONFIGURASI ---
BITFLOW_API = "https://bitflow.in/api/youtube"
BITFLOW_API_KEY = getattr(Var, 'BITFLOW_API_KEY', "youtube321bot") 
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")

if not os.path.isdir(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# Queue/State Models
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
    def as_list(self):
        return list(self._q)
    def clear(self):
        self._q.clear()
    def __len__(self):
        return len(self._q)

class VCState:
    def __init__(self):
        self.queue = Queue()
        self.now_playing: Optional[Track] = None
        self.lock = asyncio.Lock()
        self.volume = 100

# ─────────────────────────────────────────────────────────────
# YouTube Resolver (Asumsi fungsi ini diisi dengan benar)
# ─────────────────────────────────────────────────────────────

class YouTubeResolver:
    def __init__(self):
        if yt_dlp is None:
            raise RuntimeError("yt-dlp is required. Install with: pip install yt-dlp")
        if not os.path.isdir(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # (Lanjutan fungsi resolver...)
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

    async def download_audio_to_path(self, query_or_url: str) -> Tuple[str, bool, str]:
        target = await self._search_to_url(query_or_url)
        title = await self.extract_title(target)
        bf = await self._bitflow(target, want_video=False)
        if bf and bf.get("url") and bf.get("videoid"):
            filename = os.path.join(DOWNLOAD_DIR, f"{bf['videoid']}.{bf.get('ext','m4a')}")
            if not os.path.exists(filename):
                opts = {
                    "format": "bestaudio/best", "outtmpl": filename, "geo_bypass": True, 
                    "nocheckcertificate": True, "quiet": True, "no_warnings": True,
                }
                def _dl():
                    with yt_dlp.YoutubeDL(opts) as y: y.download([bf["url"]]) 
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, _dl)
            return filename, True, title 

        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "-g", "-f", "bestaudio/best", target,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        url = stdout.decode().split("\n")[0].strip() if stdout else ""
        if url:
            return url, False, title 

        err = (stderr or b"unknown error").decode()
        raise RuntimeError(f"Failed to resolve audio: {err}")

    async def extract_title(self, query_or_url: str) -> str:
        opts = {"quiet": True, "skip_download": True}
        try:
            with yt_dlp.YoutubeDL(opts) as y:
                info = y.extract_info(query_or_url, download=False)
                if isinstance(info, dict) and "entries" in info:
                    info = info["entries"][0] 
                return info.get("title") or "Unknown Title"
        except Exception:
            return "Unknown Title"


# ─────────────────────────────────────────────────────────────
# VC Manager
# ─────────────────────────────────────────────────────────────

class VCManager:
    # 🌟 PERUBAHAN KRITIS: Menerima PyTgCalls Client yang sudah distart
    def __init__(self, tgcalls_client: PyTgCalls):
        self.tgcalls = tgcalls_client # 👈 Gunakan klien yang ada!
        self.states: Dict[int, VCState] = {}
        self.resolver = YouTubeResolver()

        @self.tgcalls.on_stream_end()
        async def on_end(_, update):
            chat_id = update.chat_id
            await self._on_track_end(chat_id)

    def state(self, chat_id: int) -> VCState:
        if chat_id not in self.states:
            self.states[chat_id] = VCState()
        return self.states[chat_id]

    # ... (leave, play, _build_stream, _start_stream, _on_track_end, pause, resume, stop methods sama seperti sebelumnya)
    async def leave(self, chat_id: int):
        try:
            await self.tgcalls.leave_group_call(chat_id)
        except Exception:
            pass
        self.states.pop(chat_id, None)

    async def play(self, chat_id: int, track: Track):
        st = self.state(chat_id)
        async with st.lock:
            if st.now_playing is None:
                await self._start_stream(chat_id, track)
            else:
                st.queue.push(track)

    def _build_stream(self, src: str, vol_percent: int, is_local: bool) -> AudioPiped:
        gain_db = 6.0 * (vol_percent / 100.0 - 1.0)
        return AudioPiped(
            src,
            stream_type=StreamType().local_stream if is_local else StreamType().pulse_stream,
            additional_ffmpeg_parameters=["-af", f"volume={gain_db}dB"],
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
        st = self.state(chat_id)
        async with st.lock:
            nxt = st.queue.pop()
            if nxt:
                await self._start_stream(chat_id, nxt)
            else:
                st.now_playing = None
                with contextlib.suppress(Exception):
                    await self.tgcalls.leave_group_call(chat_id)

    async def pause(self, chat_id: int):
        await self.tgcalls.pause_stream(chat_id)

    async def resume(self, chat_id: int):
        await self.tgcalls.resume_stream(chat_id)

    async def stop(self, chat_id: int):
        st = self.state(chat_id)
        st.queue.clear()
        st.now_playing = None
        with contextlib.suppress(Exception):
            await self.tgcalls.leave_group_call(chat_id)


# Singleton manager
_vc: Optional[VCManager] = None


def _manager(e) -> VCManager:
    global vc_call
    
    # Pengecekan Kritis: Pastikan vc_call adalah PyTgCalls
    if not isinstance(vc_call, PyTgCalls):
        # Ini akan terpicu jika VCBOT dinonaktifkan atau vc_connection mengembalikan TelethonClient
        raise RuntimeError("VC Client (PyTgCalls) belum siap atau VCBOT dinonaktifkan.")
        
    if _vc is None:
        # Buat VCManager dengan PyTgCalls Client yang sudah ada
        _vc = VCManager(vc_call)
    return _vc

# ─────────────────────────────────────────────────────────────
# Commands (Sama seperti sebelumnya)
# ─────────────────────────────────────────────────────────────

def _cid(e: Message) -> int:
    return e.chat_id


@ultroid_cmd(pattern="vcjoin$", groups_only=True)
async def vc_join(e: Message):
    try:
        _ = _manager(e)
        await e.eor("VC ready. Use `.vcplay <query|url>` or reply to media.")
    except RuntimeError as ex:
        # Error ini muncul jika vc_call BUKAN PyTgCalls (yaitu None atau TelethonClient)
        await e.eor(f"**❌ Error:** `{ex}`\nPastikan VCBOT aktif dan PyTgCalls terinstal.")


@ultroid_cmd(pattern="vcleave$", groups_only=True)
async def vc_leave(e: Message):
    try:
        await _manager(e).leave(_cid(e))
        await e.eor("Left VC.")
    except Exception as ex:
        await e.eor(f"`{type(ex).__name__}: {ex}`")


@ultroid_cmd(pattern=r"vcplay(?:\s+(.+))?$", groups_only=True)
async def vc_play(e: Message):
    chat_id = _cid(e)
    arg = (e.pattern_match.group(1) or "").strip()

    if e.is_reply and not arg:
        r = await e.get_reply_message()
        if r and (r.audio or r.voice or r.video or r.document):
            msg = await e.eor("Downloading replied media…")
            path = await e.client.download_media(r, file=DOWNLOAD_DIR)
            title = os.path.basename(path)
            await _manager(e).play(chat_id, Track(title=title, source=path, requested_by=str(e.sender_id)))
            return await msg.edit(f"Queued replied media: **{title}**")

    if not arg:
        return await e.eor("Usage: `.vcplay <url|query>` or reply to media.")

    msg = await e.eor("Resolving & downloading…")
    mgr = _manager(e)
    try:
        src, is_local, title = await mgr.resolver.download_audio_to_path(arg)
        await mgr.play(chat_id, Track(title=title, source=src, requested_by=str(e.sender_id)))
        await msg.edit(f"Queued: **{title}** {'(local)' if is_local else '(stream)'}")
    except RuntimeError as ex:
        await msg.edit(f"**❌ Gagal Resolusi!** `{ex}`")
    except Exception as ex:
        await msg.edit(f"❌ Error: `{type(ex).__name__}: {ex}`")


@ultroid_cmd(pattern="vcpause$", groups_only=True)
async def vc_pause(e: Message):
    try:
        await _manager(e).pause(_cid(e))
        await e.eor("Paused.")
    except Exception as ex:
        await e.eor(f"`{type(ex).__name__}: {ex}`")


@ultroid_cmd(pattern="vcresume$", groups_only=True)
async def vc_resume(e: Message):
    try:
        await _manager(e).resume(_cid(e))
        await e.eor("Resumed.")
    except Exception as ex:
        await e.eor(f"`{type(ex).__name__}: {ex}`")


@ultroid_cmd(pattern="vcskip$", groups_only=True)
async def vc_skip(e: Message):
    try:
        await _manager(e)._on_track_end(_cid(e))
        await e.eor("Skipped.")
    except Exception as ex:
        await e.eor(f"`{type(ex).__name__}: {ex}`")


@ultroid_cmd(pattern="vcstop$", groups_only=True)
async def vc_stop(e: Message):
    try:
        await _manager(e).stop(_cid(e))
        await e.eor("Stopped and cleared queue.")
    except Exception as ex:
        await e.eor(f"`{type(ex).__name__}: {ex}`")


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
    lines = [f"**{i+1}.** {t.title}" for i, t in enumerate(st.queue.as_list())]
    np_title = st.now_playing.title if st.now_playing else "None"
    response = (
        f"🎶 Sedang Diputar: **{np_title}**\n"
        f"--- Antrean ({len(st.queue.as_list())} Lagu) ---\n"
        + "\n".join(lines)
    )
    await e.eor(response)


@ultroid_cmd(pattern=r"vcvol(?:\s+(\d{1,3}))?$", groups_only=True)
async def vc_volume(e: Message):
    arg = e.pattern_match.group(1)
    st = _manager(e).state(_cid(e))
    
    if arg is None:
        return await e.eor(f"Current volume: **{st.volume}%** (applies to next track)")
    
    try:
        v = min(200, max(0, int(arg)))
    except ValueError:
        return await e.eor("`Give a number 0-200.`")
        
    st.volume = v
    await e.eor(f"Volume set to **{v}%** for next track.")
    
