import asyncio
import os
import re
from typing import Union

import aiohttp
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from yt_dlp import YoutubeDL

DOWNLOAD_DIR = "downloads"


def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link

        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]

        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)

        for message in messages:

            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[
                            entity.offset : entity.offset + entity.length
                        ]

            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url

        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        try:
            if videoid:
                link = self.base + link

            if "&" in link:
                link = link.split("&")[0]

            loop = asyncio.get_event_loop()

            def extract():
                ydl_opts = {
                    "quiet": True,
                    "noplaylist": True,
                    "nocheckcertificate": True,
                    "ignoreerrors": True,
                }

                with YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(link, download=False)

            data = await loop.run_in_executor(None, extract)

            if not data:
                return None

            title = data.get("title", "Unknown")
            duration = data.get("duration", 0)
            thumbnail = data.get("thumbnail")
            vidid = data.get("id")

            minutes = duration // 60
            seconds = duration % 60

            duration_min = f"{minutes}:{seconds:02d}"

            return (
                title,
                duration_min,
                duration,
                thumbnail,
                vidid,
            )

        except Exception as e:
            print(f"DETAILS ERROR: {e}")
            return None

    async def title(self, link: str, videoid: Union[bool, str] = None):
        try:
            data, _ = await self.track(link, videoid)

            if not data:
                return None

            return data["title"]

        except Exception as e:
            print(f"TITLE ERROR: {e}")
            return None

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        try:
            data, _ = await self.track(link, videoid)

            if not data:
                return None

            return data["duration_min"]

        except Exception as e:
            print(f"DURATION ERROR: {e}")
            return None

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        try:
            data, _ = await self.track(link, videoid)

            if not data:
                return None

            return data["thumb"]

        except Exception as e:
            print(f"THUMBNAIL ERROR: {e}")
            return None

    async def track(self, link: str, videoid: Union[bool, str] = None):
        try:
            if videoid:
                link = self.base + link

            if "&" in link:
                link = link.split("&")[0]

            loop = asyncio.get_event_loop()

            def extract():
                ydl_opts = {
                    "quiet": True,
                    "noplaylist": True,
                    "nocheckcertificate": True,
                    "ignoreerrors": True,
                }

                with YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(link, download=False)

            data = await loop.run_in_executor(None, extract)

            if not data:
                return None, None

            title = data.get("title", "Unknown")
            duration = data.get("duration", 0)
            vidid = data.get("id")
            thumbnail = data.get("thumbnail")
            yturl = data.get("webpage_url")

            if not vidid:
                return None, None

            minutes = duration // 60
            seconds = duration % 60

            duration_min = f"{minutes}:{seconds:02d}"

            track_details = {
                "title": title,
                "link": yturl,
                "vidid": vidid,
                "duration_min": duration_min,
                "thumb": thumbnail,
            }

            return track_details, vidid

        except Exception as e:
            print(f"TRACK ERROR: {e}")
            return None, None

    async def playlist(
        self,
        link,
        limit,
        user_id,
        videoid: Union[bool, str] = None,
    ):
        try:
            if videoid:
                link = self.listbase + link

            if "&" in link:
                link = link.split("&")[0]

            ydl_opts = {
                "quiet": True,
                "extract_flat": True,
                "skip_download": True,
            }

            loop = asyncio.get_event_loop()

            def extract():
                with YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(link, download=False)

            data = await loop.run_in_executor(None, extract)

            entries = data.get("entries", [])

            ids = []

            for video in entries[:limit]:
                if not video:
                    continue

                vid = video.get("id")

                if vid:
                    ids.append(vid)

            return ids

        except Exception as e:
            print(f"PLAYLIST ERROR: {e}")
            return []

    async def video(self, link: str, videoid: Union[bool, str] = None):
        try:
            if videoid:
                link = self.base + link

            os.makedirs(DOWNLOAD_DIR, exist_ok=True)

            ydl_opts = {
                "format": "bestvideo+bestaudio/best",
                "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
                "quiet": True,
                "merge_output_format": "mp4",
            }

            loop = asyncio.get_event_loop()

            def download():
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(link, download=True)
                    return ydl.prepare_filename(info)

            file_path = await loop.run_in_executor(None, download)

            return 1, file_path

        except Exception as e:
            return 0, f"Video download error: {e}"

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ):

        try:
            if videoid:
                link = self.base + link

            os.makedirs(DOWNLOAD_DIR, exist_ok=True)

            if video:
                ydl_opts = {
                    "format": "bestvideo+bestaudio/best",
                    "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
                    "quiet": True,
                    "merge_output_format": "mp4",
                }
            else:
                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
                    "quiet": True,
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ],
                }

            loop = asyncio.get_event_loop()

            def extract():
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(link, download=True)
                    return ydl.prepare_filename(info)

            file_path = await loop.run_in_executor(None, extract)

            return file_path, True

        except Exception as e:
            print(f"DOWNLOAD ERROR: {e}")
            return None, False


YouTube = YouTubeAPI()
