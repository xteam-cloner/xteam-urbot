# vc_music.py - Plugin Musik VC untuk Ultroid

from __future__ import annotations

import asyncio
import re
import os
import contextlib 
import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union, Any

import httpx
# Pastikan impor umum paket xteam dan telethon sudah benar
from . import * from telethon import events, TelegramClient 
from telethon.tl.types import Message
from xteam.configs import Var 
from xteam import vc_call # 🌟 PERUBAHAN KRITIS: IMPOR KLIEN PYTGCALLS GLOBAL DENGAN NAMA vc_call
from xteam import ultroid_bot # IMPOR KLIEN TELETHON UTAMA UNTUK MENGIRIM PESAN (jika diperlukan)

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
BITFLOW_API = "https://bitflow.in/api/youtube"
BITFLOW_API_KEY = getattr(Var, 'BITFLOW_API_KEY', "youtube321bot") 

DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
YOUTUBE_REGEX = r"(?:youtube\.com|youtu\.be)"

if not os.path.isdir(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
logger = logging.getLogger(__name__)

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
    def pop(self, index: int = 0) -> Optional[Track]:
        return self._q.pop(index) if self._q else None
    def as_list(self):
        return list(self._q)
    def clear(self):
        self._q.clear()

class VCState:
    def __init__(self):
        self.queue = Queue()
        self.now_playing: Optional[Track] = None
        self.lock = asyncio.Lock()
        self.volume = 100 

# ─────────────────────────────────────────────────────────────
# YouTube Resolver
# ─────────────────────────────────────────────────────────────

class YouTubeResolver:
    def __init__(self):
        if yt_dlp is None:
            raise RuntimeError("yt-dlp is required. Install with: pip install yt-dlp")

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
    # Menerima PyTgCalls Client (yang sekarang bernama vc_call)
    def __init__(self, client: TelegramClient, tgcalls_client: PyTgCalls):
        if PyTgCalls is None:
            raise RuntimeError("pytgcalls is not installed. Run: pip install pytgcalls")
        self.client = client
        self.tgcalls = tgcalls_client # 👈 self.tgcalls adalah vc_call global
        self.states: Dict[int, VCState] = {}
        self.resolver = YouTubeResolver()

        @self.tgcalls.on_stream_end()
        async def on_end(_, update: StreamEnded):
            chat_id = update.chat_id
            await self._on_track_end(chat_id)

    def state(self, chat_id: int) -> VCState:
        if chat_id not in self.states:
            self.states[chat_id] = VCState()
        return self.states[chat_id]

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

    def _build_stream(self, src: str, vol_percent: int, is_local: bool) -> MediaStream:
        gain_db = 6.0 * (min(vol_percent, 200) / 100.0 - 1.0)
        ffmpeg_params = ["-af", f"volume={gain_db}dB"]
        
        if is_local:
            return MediaStream.telegram(
                file=src, 
                additional_ffmpeg_parameters=ffmpeg_params,
            )
        else:
            return MediaStream.url(
                url=src, 
                additional_ffmpeg_parameters=ffmpeg_params,
            )


    async def _start_stream(self, chat_id: int, track: Track):
        st = self.state(chat_id)
        st.now_playing = track
        is_local = os.path.exists(track.source)
        stream = self._build_stream(track.source, st.volume, is_local)
        
        try:
            await self.tgcalls.join_group_call(chat_id, stream)
        except NoActiveGroupCall:
            logger.warning(f"No active VC in chat {chat_id}. Cannot start stream.")
            await ultroid_bot.send_message(chat_id, "`❌ Tidak ada Obrolan Suara aktif.`")
        except Exception as e:
            logger.error(f"Error starting stream: {e}")
            await ultroid_bot.send_message(chat_id, f"❌ Error saat memulai stream: `{e}`")
            await self._on_track_end(chat_id)


    async def _on_track_end(self, chat_id: int):
        st = self.state(chat_id)
        async with st.lock:
            if st.now_playing and os.path.exists(st.now_playing.source):
                with contextlib.suppress(Exception):
                    os.remove(st.now_playing.source)
            
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
        if st.now_playing and os.path.exists(st.now_playing.source):
            with contextlib.suppress(Exception):
                os.remove(st.now_playing.source)

        st.queue.clear()
        st.now_playing = None
        with contextlib.suppress(Exception):
            await self.tgcalls.leave_group_call(chat_id)


# --- SINGLETON MANAGER & HELPER ---
_vc: Dict[int, VCManager] = {} 

def _manager(e) -> VCManager:
    """
    Mengambil klien PyTgCalls global (vc_call) dan membuat VCManager per ID klien.
    """
    global vc_call # 🌟 PERUBAHAN: Merujuk ke variabel global vc_call

    if not isinstance(vc_call, PyTgCalls):
        # 🌟 PERUBAHAN: Cek tipe vc_call
        raise RuntimeError(
            "VC Client (PyTgCalls) belum siap atau `VCBOT` dinonaktifkan."
        )

    client_id = id(e.client)
    global _vc
    if client_id not in _vc:
        # 🌟 PERUBAHAN: Teruskan vc_call ke VCManager
        _vc[client_id] = VCManager(e.client, vc_call) 
    return _vc[client_id]

def _cid(e: Message) -> int:
    return e.chat_id

# ─────────────────────────────────────────────────────────────
# Commands (Ultroid Integration)
# ─────────────────────────────────────────────────────────────

@ultroid_cmd(pattern="vcjoin$", groups_only=True)
async def vc_join(e: Message):
    """Perintah: .vcjoin - Menginisialisasi manager."""
    try:
        _ = _manager(e) 
        await e.eor("`VC Manager siap. Gunakan .vcplay <query|url>`")
    except RuntimeError as ex:
        await e.eor(f"**❌ Error:** `{ex}`\nPastikan `VCBOT` aktif dan Anda menunggu startup selesai.")
    except Exception as ex:
        await e.eor(f"**❌ Error Inisialisasi:** `{type(ex).__name__}: {ex}`")


@ultroid_cmd(pattern="vcleave$", groups_only=True)
async def vc_leave(e: Message):
    """Perintah: .vcleave - Meninggalkan VC."""
    try:
        await _manager(e).leave(_cid(e))
        await e.eor("`👋 Berhasil meninggalkan VC.`")
    except Exception as ex:
        await e.eor(f"**❌ Gagal!** `{type(ex).__name__}: {ex}`")


@ultroid_cmd(pattern=r"vcplay(?:\s+(.+))?$", groups_only=True)
async def vc_play(e: Message):
    """Perintah: .vcplay - Memutar atau mengantrekan lagu."""
    chat_id = _cid(e)
    arg = (e.pattern_match.group(1) or "").strip()

    if e.is_reply and not arg:
        r = await e.get_reply_message()
        if r and (r.audio or r.voice or r.video or r.document):
            msg = await e.eor("`📥 Mengunduh media yang dibalas...`")
            path = await e.client.download_media(r, file=DOWNLOAD_DIR) 
            title = os.path.basename(path)
            
            await _manager(e).play(
                chat_id, 
                Track(
                    title=title, 
                    source=path, 
                    requested_by=str(e.sender_id)
                )
            )
            return await msg.edit(f"`✅ Media yang dibalas diantrekan: **{title}**`")

    if not arg:
        return await e.eor("`Penggunaan: .vcplay <url|query>` atau balas ke media.")

    msg = await e.eor("`🌐 Mencari & mengunduh...`")
    mgr = _manager(e)
    try:
        src, is_local, title = await mgr.resolver.download_audio_to_path(arg)
        
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
        await msg.eor(f"**❌ Gagal Memutar!** `{type(ex).__name__}: {ex}`")


@ultroid_cmd(pattern="vcpause$", groups_only=True)
async def vc_pause(e: Message):
    try:
        await _manager(e).pause(_cid(e))
        await e.eor("`⏸ Dijeda.`")
    except Exception as ex:
        await e.eor(f"**❌ Gagal!** `{type(ex).__name__}: {ex}`")


@ultroid_cmd(pattern="vcresume$", groups_only=True)
async def vc_resume(e: Message):
    try:
        await _manager(e).resume(_cid(e))
        await e.eor("`▶ Dilanjutkan.`")
    except Exception as ex:
        await e.eor(f"**❌ Gagal!** `{type(ex).__name__}: {ex}`")


@ultroid_cmd(pattern="vcskip$", groups_only=True)
async def vc_skip(e: Message):
    try:
        await _manager(e)._on_track_end(_cid(e)) 
        await e.eor("`⏩ Dilewati.`")
    except Exception as ex:
        await e.eor(f"**❌ Gagal!** `{type(ex).__name__}: {ex}`")


@ultroid_cmd(pattern="vcstop$", groups_only=True)
async def vc_stop(e: Message):
    try:
        await _manager(e).stop(_cid(e))
        await e.eor("`⏹ Dihentikan dan antrean dibersihkan.`")
    except Exception as ex:
        await e.eor(f"**❌ Gagal!** `{type(ex).__name__}: {ex}`")


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
    if not st.queue.as_list():
        return await e.eor("`Antrean kosong.`")
    
    lines = [f"**{i+1}.** {t.title}" for i, t in enumerate(st.queue.as_list())]
    np_title = st.now_playing.title if st.now_playing else "Tidak ada"
    
    response = (
        f"**🎶 Sedang Diputar:** {np_title}\n"
        f"--- Antrean ({len(st.queue.as_list())} Lagu) ---\n"
        + "\n".join(lines)
    )
    await e.eor(response)


@ultroid_cmd(pattern=r"vcvol(?:\s+(\d{1,3}))?$", groups_only=True)
async def vc_volume(e: Message):
    arg = e.pattern_match.group(1)
    st = _manager(e).state(_cid(e))
    
    if arg is None:
        return await e.eor(f"Volume saat ini: **{st.volume}%** (berlaku untuk lagu berikutnya)")
    
    try:
        v = min(200, max(0, int(arg)))
    except ValueError:
        return await e.eor("`Masukkan angka antara 0-200.`")
        
    st.volume = v
    await e.eor(f"Volume diatur ke **{v}%** untuk lagu berikutnya. (Akan diterapkan pada pemutaran stream/file berikutnya)")
