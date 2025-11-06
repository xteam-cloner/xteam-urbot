# (Kode header, impor, Queue/State, dan Resolver tetap sama seperti sebelumnya)

from __future__ import annotations

import asyncio
import os
import re
import tempfile
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import httpx

from telethon import events
from telethon.tl.types import Message

# ⚠️ BLOCK IMPOR PYTGCALLS YANG DIPERBARUI ⚠️
try:
    from pytgcalls import PyTgCalls
    from pytgcalls import filters as fl
    from ntgcalls import TelegramServerError
    from pytgcalls.exceptions import NoActiveGroupCall # Exception baru
    from pytgcalls.types import (
        ChatUpdate,
        MediaStream, # Menggantikan AudioPiped
        StreamEnded,
        GroupCallConfig,
        GroupCallParticipant,
        UpdatedGroupCallParticipant,
        AudioQuality,
        VideoQuality,
    )
except Exception as e:
    PyTgCalls = None  # type: ignore
    MediaStream = None # type: ignore
    NoActiveGroupCall = Exception # Fallback untuk tipe Exception
    class TelegramServerError(Exception): pass
# ⚠️ END BLOCK IMPOR PYTGCALLS YANG DIPERBARUI ⚠️

try:
    import yt_dlp
except Exception:
    yt_dlp = None  # type: ignore

try:
    from youtubesearchpython.__future__ import VideosSearch
except Exception:
    VideosSearch = None  # type: ignore

from . import ultroid_cmd

YOUTUBE_REGEX = r"(?:youtube\.com|youtu\.be)"
BITFLOW_API = "https://bitflow.in/api/youtube"
BITFLOW_API_KEY = "youtube321bot"  # provided test key from your snippet
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")

# ─────────────────────────────────────────────────────────────
# Queue/State
# ─────────────────────────────────────────────────────────────

@dataclass
class Track:
    title: str
    source: str  # local file path or direct stream URL
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
        self.volume = 100  # % applied to *next* track via ffmpeg filter

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
        self.client = client
        self.tgcalls = None  # Tunda inisialisasi PyTgCalls
        self.states: Dict[int, VCState] = {}
        self.started = False
        self.resolver = YouTubeResolver()

        # Gunakan asyncio.create_task untuk menjalankan _on_client_ready secara asinkron
        asyncio.create_task(self._on_client_ready())

    async def _on_client_ready(self):
        # 🔑 PERUBAHAN BARU: Memastikan koneksi Telethon secara eksplisit
        if not self.client.is_connected():
            print("Telethon client not yet connected. Attempting to connect...")
            try:
                # Coba start ulang klien (Ultroid seharusnya sudah melakukannya)
                await self.client.start()
            except Exception as e:
                print(f"Failed to explicitly start client: {e}")
                return

        # Loop pengecekan koneksi yang lebih andal
        max_retries = 10
        for i in range(max_retries):
            try:
                # Cek koneksi dengan get_me()
                await self.client.get_me() 
                break # Keluar dari loop jika berhasil mendapatkan info klien
            except Exception as e:
                print(f"Telethon client not fully ready (Attempt {i+1}/{max_retries}). Waiting...")
                await asyncio.sleep(3) # Tunggu lebih lama: 3 detik
        else:
            print("Failed to ensure Telethon client readiness after multiple attempts.")
            return

        if not self.started:
            try:
                # Inisialisasi PyTgCalls ketika klien sudah siap
                self.tgcalls = PyTgCalls(self.client) 
                
                # Daftarkan handler on_stream_end setelah tgcalls dibuat
                @self.tgcalls.on_stream_end()
                async def on_end(_, update):
                    chat_id = update.chat_id
                    await self._on_track_end(chat_id)
                
                await self.tgcalls.start()
                self.started = True
                print("PyTgCalls successfully started.")
            except Exception as e:
                print(f"Failed to start PyTgCalls: {e}")
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
            
