# vc_music.py - Ultroid VC Music Plugin menggunakan PyTgCalls terbaru
# Drop this file ke folder plugins Ultroid Anda.

from __future__ import annotations

import asyncio
import re
import os
import contextlib 
import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union, Any
from xteam import ultroid_bot as client
import httpx
from . import * 
from telethon import events, TelegramClient 
from telethon.tl.types import Message
# Menggunakan Var dari xteam.configs
from xteam.configs import Var 
from ntgcalls import TelegramServerError
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from pytgcalls.types import (
    StreamEnded,
)
from pytgcalls.exceptions import NoActiveGroupCall, InvalidMTProtoClient
import yt_dlp
from youtubesearchpython.__future__ import VideosSearch

from . import ultroid_cmd

# --- KONSTANTA & KONFIGURASI ---

# Ambil API KEY dari Var Ultroid jika tersedia, jika tidak gunakan hardcode lama
BITFLOW_API = "https://bitflow.in/api/youtube"
# Menggunakan getattr untuk kompatibilitas dengan Var, fallback ke key lama
BITFLOW_API_KEY = getattr(Var, 'BITFLOW_API_KEY', "youtube321bot") 

DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
YOUTUBE_REGEX = r"(?:youtube\.com|youtu\.be)"

# Buat folder download jika belum ada
if not os.path.isdir(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
# --- LOGGING ---
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Queue/State Models
# ─────────────────────────────────────────────────────────────

@dataclass
class Track:
    title: str
    source: str  # local file path or direct stream URL
    requested_by: str

class Queue:
    """Antrean lagu untuk setiap chat."""
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
    """Status Voice Chat per-chat_id."""
    def __init__(self):
        self.queue = Queue()
        self.now_playing: Optional[Track] = None
        self.lock = asyncio.Lock()
        self.volume = 100 

# ─────────────────────────────────────────────────────────────
# YouTube Resolver (yt-dlp + Bitflow)
# ─────────────────────────────────────────────────────────────

class YouTubeResolver:
    def __init__(self):
        if yt_dlp is None:
            # Karena ini Ultroid plugin, sebaiknya log/raise error jika yt-dlp tidak ada
            raise RuntimeError("yt-dlp is required. Install with: pip install yt-dlp")

    async def _bitflow(self, url: str, want_video: bool = False) -> Optional[dict]:
        """Mengambil metadata dari Bitflow API."""
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
        """Mengubah query menjadi URL streamable atau ytsearch1."""
        if re.search(r"^https?://", query):
            return query
        q = f"ytsearch1:{query.strip()}"
        return q

    async def download_audio_to_path(self, query_or_url: str) -> Tuple[str, bool]:
        """Return (path_or_url, is_local). Mengutamakan download lokal."""
        target = await self._search_to_url(query_or_url)

        # 1. Coba Bitflow untuk URL metadata
        bf = await self._bitflow(target, want_video=False)
        if bf and bf.get("url") and bf.get("videoid"):
            filename = os.path.join(DOWNLOAD_DIR, f"{bf['videoid']}.{bf.get('ext','m4a')}")
            
            # Download jika file belum ada
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
            return filename, True # Path lokal, berhasil

        # 2. Fallback: Resolusi URL stream langsung (tanpa download)
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "-g", "-f", "bestaudio/best", target,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        url = stdout.decode().split("\n")[0].strip() if stdout else ""
        if url:
            return url, False # URL stream, berhasil

        # 3. Gagal total
        err = (stderr or b"unknown error").decode()
        raise RuntimeError(f"Failed to resolve audio: {err}")

    async def extract_title(self, query_or_url: str) -> str:
        """Mengambil judul secara ringan (tanpa download)."""
        opts = {"quiet": True, "skip_download": True}
        with yt_dlp.YoutubeDL(opts) as y:
            info = y.extract_info(await self._search_to_url(query_or_url), download=False)
            if isinstance(info, dict) and "entries" in info:
                # Jika hasil pencarian, ambil entri pertama
                info = info["entries"][0] 
            return info.get("title") or "Unknown Title"

# ─────────────────────────────────────────────────────────────
# VC Manager (Jantung Keep-Alive)
# ─────────────────────────────────────────────────────────────

class VCManager:
    def __init__(self, client):
        if PyTgCalls is None:
            raise RuntimeError("pytgcalls is not installed. Run: pip install pytgcalls")
        self.client = client
        # Inisialisasi PyTgCalls dengan client yang sudah ada
        self.tgcalls = PyTgCalls(client) 
        self.states: Dict[int, VCState] = {}
        self.resolver = YouTubeResolver()

        @self.tgcalls.on_stream_end()
        async def on_end(_, update: StreamEnded):
            # Handler saat lagu selesai
            chat_id = update.chat_id
            await self._on_track_end(chat_id)

        # PyTgCalls harus dimulai
        self.client.loop.run_until_complete(self.tgcalls.start())

    def state(self, chat_id: int) -> VCState:
        if chat_id not in self.states:
            self.states[chat_id] = VCState()
        return self.states[chat_id]

    async def leave(self, chat_id: int):
        """Meninggalkan VC dan membersihkan state."""
        try:
            await self.tgcalls.leave_group_call(chat_id)
        except Exception:
            pass
        self.states.pop(chat_id, None)

    async def play(self, chat_id: int, track: Track):
        """Memutar atau mengantrekan lagu."""
        st = self.state(chat_id)
        async with st.lock:
            if st.now_playing is None:
                await self._start_stream(chat_id, track)
            else:
                st.queue.push(track)

    def _build_stream(self, src: str, vol_percent: int, is_local: bool) -> MediaStream:
        """Membuat objek MediaStream dengan filter volume FFmpeg."""
        # Volume filter: 100%→0 dB; 200%→+6 dB; 50%→-6 dB
        gain_db = 6.0 * (vol_percent / 100.0 - 1.0)
        
        # Parameter FFmpeg
        ffmpeg_params = ["-af", f"volume={gain_db}dB"]
        
        if is_local:
            # Untuk file lokal, gunakan MediaStream.telegram
            return MediaStream.telegram(
                file=src, 
                additional_ffmpeg_parameters=ffmpeg_params,
            )
        else:
            # Untuk URL stream, gunakan MediaStream.url
            return MediaStream.url(
                url=src, 
                additional_ffmpeg_parameters=ffmpeg_params,
            )


    async def _start_stream(self, chat_id: int, track: Track):
        """Memulai stream baru atau mengganti stream yang ada."""
        st = self.state(chat_id)
        st.now_playing = track
        is_local = os.path.exists(track.source)
        stream = self._build_stream(track.source, st.volume, is_local)
        
        try:
            # PyTgCalls mengirim JoinGroupCallRequest jika belum bergabung
            await self.tgcalls.join_group_call(chat_id, stream)
        except NoActiveGroupCall:
            logger.warning(f"No active VC in chat {chat_id}. Cannot start stream.")
        except Exception as e:
            logger.error(f"Error starting stream: {e}")
            # Coba skip jika error terjadi saat mencoba bergabung
            await self._on_track_end(chat_id)


    async def _on_track_end(self, chat_id: int):
        """Dipanggil saat lagu selesai, memicu lagu berikutnya."""
        st = self.state(chat_id)
        async with st.lock:
            nxt = st.queue.pop()
            if nxt:
                await self._start_stream(chat_id, nxt)
            else:
                st.now_playing = None
                # Jika antrean kosong, tinggalkan VC
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


# --- SINGLETON MANAGER & HELPER ---
_vc: Optional[VCManager] = None

def _manager(e) -> VCManager:
    """Menginisialisasi dan mengembalikan instance VCManager."""
    global _vc
    if _vc is None:
        _vc = VCManager(e.client)
    return _vc

def _cid(e: Message) -> int:
    return e.chat_id

# ─────────────────────────────────────────────────────────────
# Commands (Ultroid Integration)
# ─────────────────────────────────────────────────────────────

@ultroid_cmd(pattern="vcjoin$", groups_only=True)
async def vc_join(e: Message):
    """Perintah: .vcjoin - Inisialisasi manager."""
    _ = _manager(e)
    await e.eor("`VC Manager siap. Gunakan .vcplay <query|url>`")


@ultroid_cmd(pattern="vcleave$", groups_only=True)
async def vc_leave(e: Message):
    """Perintah: .vcleave - Meninggalkan VC."""
    try:
        await _manager(e).leave(_cid(e))
        await e.eor("`👋 Berhasil meninggalkan VC.`")
    except Exception as ex:
        await e.eor(f"**❌ Gagal!** `{ex}`")


@ultroid_cmd(pattern=r"vcplay(?:\s+(.+))?$", groups_only=True)
async def vc_play(e: Message):
    """Perintah: .vcplay - Memutar atau mengantrekan lagu."""
    chat_id = _cid(e)
    arg = (e.pattern_match.group(1) or "").strip()

    # Logika: Reply ke Media
    if e.is_reply and not arg:
        r = await e.get_reply_message()
        if r and (r.audio or r.voice or r.video or r.document):
            msg = await e.eor("`📥 Mengunduh media yang dibalas...`")
            path = await e.client.download_media(r, file=DOWNLOAD_DIR) 
            await _manager(e).play(
                chat_id, 
                Track(
                    title=os.path.basename(path), 
                    source=path, 
                    requested_by=str(e.sender_id)
                )
            )
            return await msg.edit("`✅ Media yang dibalas diantrekan.`")

    if not arg:
        return await e.eor("`Penggunaan: .vcplay <url|query>` atau balas ke media.")

    msg = await e.eor("`🌐 Mencari & mengunduh...`")
    mgr = _manager(e)
    try:
        src, is_local = await mgr.resolver.download_audio_to_path(arg)
        title = await mgr.resolver.extract_title(arg)
        
        await mgr.play(
            chat_id, 
            Track(
                title=title, 
                source=src, 
                requested_by=str(e.sender_id)
            )
        )
        await msg.edit(f"`✅ Diantrekan:` **{title}** `{'[Lokal]' if is_local else '[Stream]'}`")
    except RuntimeError as ex:
        await msg.edit(f"**❌ Gagal Resolusi!** `{ex}`")
    except Exception as ex:
        logger.error(f"Error in vcplay: {ex}")
        await msg.edit(f"**❌ Gagal Memutar!** `{type(ex).__name__}: {ex}`")


@ultroid_cmd(pattern="vcpause$", groups_only=True)
async def vc_pause(e: Message):
    try:
        await _manager(e).pause(_cid(e))
        await e.eor("`⏸ Dijeda.`")
    except Exception as ex:
        await e.eor(f"**❌ Gagal!** `{ex}`")


@ultroid_cmd(pattern="vcresume$", groups_only=True)
async def vc_resume(e: Message):
    try:
        await _manager(e).resume(_cid(e))
        await e.eor("`▶ Dilanjutkan.`")
    except Exception as ex:
        await e.eor(f"**❌ Gagal!** `{ex}`")


@ultroid_cmd(pattern="vcskip$", groups_only=True)
async def vc_skip(e: Message):
    try:
        await _manager(e)._on_track_end(_cid(e)) 
        await e.eor("`⏩ Dilewati.`")
    except Exception as ex:
        await e.eor(f"**❌ Gagal!** `{ex}`")


@ultroid_cmd(pattern="vcstop$", groups_only=True)
async def vc_stop(e: Message):
    try:
        await _manager(e).stop(_cid(e))
        await e.eor("`⏹ Dihentikan dan antrean dibersihkan.`")
    except Exception as ex:
        await e.eor(f"**❌ Gagal!** `{ex}`")


@ultroid_cmd(pattern="vcnp$", groups_only=True)
async def vc_now_playing(e: Message):
    st = _manager(e).state(_cid(e))
    if st.now_playing:
        await e.eor(f"🎶 Sedang diputar: **{st.now_playing.title}**")
    else:
        await e.eor("`Tidak ada yang diputar.`")


@ultroid_cmd(pattern="vcqueue$", groups_only=True)
async def vc_queue(e: Message):
    st = _manager(e).state(_cid(e))
    if not len(st.queue):
        return await e.eor("`Antrean kosong.`")
    
    lines = [f"**{i+1}.** {t.title}" for i, t in enumerate(st.queue.as_list())]
    np_title = st.now_playing.title if st.now_playing else "Tidak ada"
    
    response = (
        f"**🎶 Sedang Diputar:** {np_title}\n"
        f"--- Antrean ({len(st.queue)} Lagu) ---\n"
        + "\n".join(lines)
    )
    await e.eor(response)


@ultroid_cmd(pattern=r"vcvol(?:\s+(\d{1,3}))?$", groups_only=True)
async def vc_volume(e: Message):
    arg = e.pattern_match.group(1)
    st = _manager(e).state(_cid(e))
    
    if arg is None:
        return await e.eor(f"Current volume: **{st.volume}%** (berlaku untuk lagu berikutnya)")
    
    try:
        v = min(200, max(0, int(arg)))
    except ValueError:
        return await e.eor("`Masukkan angka antara 0-200.`")
        
    st.volume = v
    await e.eor(f"Volume diatur ke **{v}%** untuk lagu berikutnya.")
