from typing import Union, Optional

from pytdbot import types


class Telegram:
    """A helper class to process Telegram messages containing playable media (audio/video)."""

    def __init__(self, reply: Optional[types.Message]):
        """Initialize with a Telegram message object."""
        self.msg = reply

    def is_valid(self) -> bool:
        """Checks if the message contains a playable media file (audio or video)."""
        if not self.msg or isinstance(self.msg, types.Error):
            return False

        return isinstance(self.msg.content, (types.MessageVideo, types.MessageAudio))

    def get_file_name(self) -> str:
        """Retrieves the file name from the media message."""
        if not self.is_valid():
            return "Unknown Media"

        content = self.msg.content
        if isinstance(content, types.MessageVideo):
            return getattr(content.video, "file_name", "Video.mp4")
        if isinstance(content, types.MessageAudio):
            return getattr(content.audio, "file_name", "Audio.mp3")

        return "Unknown Media"

    async def dl(self) -> Union[types.Error, types.LocalFile]:
        """Downloads the media file asynchronously."""
        if not self.is_valid():
            return types.Error(message="Invalid file for download or play.")

        return await self.msg.download()
