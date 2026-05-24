import asyncio
import os
import re
from typing import Union

import aiohttp
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython import VideosSearch, Playlist

API_URL = os.environ.get("SHRUTI_API_URL", "https://api.shrutibots.site")
API_KEY = os.environ.get("SHRUTI_API_KEY", "YOUR_API_KEY")

DOWNLOAD_DIR = "downloads"


def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


async def download_song(link: str) -> str:
    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link

    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}/download",
                params={
                    "url": video_id,
                    "type": "audio",
                    "api_key": API_KEY,
                },
                timeout=aiohttp.ClientTimeout(total=300),
            ) as resp:

                if resp.status != 200:
                    return None

                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(131072):
                        f.write(chunk)

        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path

        return None

    except Exception as e:
        print(f"DOWNLOAD SONG ERROR: {e}")

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

        return None


async def download_video(link: str) -> str:
    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link

    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}/download",
                params={
                    "url": video_id,
                    "type": "video",
                    "api_key": API_KEY,
                },
                timeout=aiohttp.ClientTimeout(total=600),
            ) as resp:

                if resp.status != 200:
                    return None

                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(131072):
                        f.write(chunk)

        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path

        return None

    except Exception as e:
        print(f"DOWNLOAD VIDEO ERROR: {e}")

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

        return None


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
                        return text[entity.offset : entity.offset + entity.length]

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

            results = VideosSearch(link, limit=1)
            data = await results.next()

            if not data.get("result"):
                return None

            result = data["result"][0]

            title = result.get("title", "Unknown")
            duration_min = result.get("duration", "0:00")
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result.get("id")

            duration_sec = (
                int(time_to_seconds(duration_min))
                if duration_min
                else 0
            )

            return (
                title,
                duration_min,
                duration_sec,
                thumbnail,
                vidid,
            )

        except Exception as e:
            print(f"DETAILS ERROR: {e}")
            return None

    async def title(self, link: str, videoid: Union[bool, str] = None):
        try:
            if videoid:
                link = self.base + link

            if "&" in link:
                link = link.split("&")[0]

            results = VideosSearch(link, limit=1)
            data = await results.next()

            if not data.get("result"):
                return None

            return data["result"][0].get("title")

        except Exception as e:
            print(f"TITLE ERROR: {e}")
            return None

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        try:
            if videoid:
                link = self.base + link

            if "&" in link:
                link = link.split("&")[0]

            results = VideosSearch(link, limit=1)
            data = await results.next()

            if not data.get("result"):
                return None

            return data["result"][0].get("duration")

        except Exception as e:
            print(f"DURATION ERROR: {e}")
            return None

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        try:
            if videoid:
                link = self.base + link

            if "&" in link:
                link = link.split("&")[0]

            results = VideosSearch(link, limit=1)
            data = await results.next()

            if not data.get("result"):
                return None

            return data["result"][0]["thumbnails"][0]["url"].split("?")[0]

        except Exception as e:
            print(f"THUMBNAIL ERROR: {e}")
            return None

    async def video(self, link: str, videoid: Union[bool, str] = None):
        try:
            if videoid:
                link = self.base + link

            if "&" in link:
                link = link.split("&")[0]

            downloaded_file = await download_video(link)

            if downloaded_file:
                return 1, downloaded_file

            return 0, "Video download failed"

        except Exception as e:
            return 0, f"Video download error: {e}"

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

            plist = await Playlist.get(link)

            videos = plist.get("videos") or []

            ids = []

            for data in videos[:limit]:
                if not data:
                    continue

                vid = data.get("id")

                if not vid:
                    continue

                ids.append(vid)

            return ids

        except Exception as e:
            print(f"PLAYLIST ERROR: {e}")
            return []

    async def track(self, link: str, videoid: Union[bool, str] = None):
        try:
            if videoid:
                link = self.base + link

            if "&" in link:
                link = link.split("&")[0]

            results = VideosSearch(link, limit=1)
            data = await results.next()

            if not data.get("result"):
                return None, None

            result = data["result"][0]

            title = result.get("title", "Unknown")
            duration_min = result.get("duration", "0:00")
            vidid = result.get("id")
            yturl = result.get("link")
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]

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

    async def formats(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ):
        try:
            if videoid:
                link = self.base + link

            if "&" in link:
                link = link.split("&")[0]

            ytdl_opts = {"quiet": True}

            ydl = yt_dlp.YoutubeDL(ytdl_opts)

            with ydl:
                formats_available = []

                r = ydl.extract_info(link, download=False)

                for format in r["formats"]:
                    try:
                        if "dash" not in str(format["format"]).lower():
                            formats_available.append(
                                {
                                    "format": format["format"],
                                    "filesize": format.get("filesize"),
                                    "format_id": format["format_id"],
                                    "ext": format["ext"],
                                    "format_note": format["format_note"],
                                    "yturl": link,
                                }
                            )

                    except Exception:
                        continue

            return formats_available, link

        except Exception as e:
            print(f"FORMAT ERROR: {e}")
            return [], link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
        try:
            if videoid:
                link = self.base + link

            if "&" in link:
                link = link.split("&")[0]

            a = VideosSearch(link, limit=10)

            data = await a.next()

            result = data.get("result")

            if not result:
                return None

            title = result[query_type]["title"]
            duration_min = result[query_type]["duration"]
            vidid = result[query_type]["id"]
            thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]

            return title, duration_min, thumbnail, vidid

        except Exception as e:
            print(f"SLIDER ERROR: {e}")
            return None

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
    ) -> str:

        try:
            if videoid:
                link = self.base + link

            if video:
                downloaded_file = await download_video(link)
            else:
                downloaded_file = await download_song(link)

            if downloaded_file:
                return downloaded_file, True

            return None, False

        except Exception as e:
            print(f"DOWNLOAD ERROR: {e}")
            return None, False


YouTube = YouTubeAPI()
