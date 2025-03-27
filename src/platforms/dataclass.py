from pydantic import BaseModel


class CachedTrack(BaseModel):
    name: str
    artist: str
    loop: int
    user: str
    file_path: str
    thumbnail: str
    track_id: str
    duration: int = 0
    platform: str


class TrackInfo(BaseModel):
    cdnurl: str
    key: str
    name: str
    artist: str
    album: str
    tc: str
    cover: str
    lyrics: str
    duration: int
    year: int


class MusicTrack(BaseModel):
    name: str
    artist: str
    id: str
    year: int
    cover: str
    duration: int
    platform: str = "spotify"


class PlatformTracks(BaseModel):
    tracks: list[MusicTrack]
