import random
import string

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InputMediaPhoto, Message
from pytgcalls.exceptions import NoActiveGroupCall

import config
from MoonXMusic import Apple, Resso, SoundCloud, Spotify, Telegram, YouTube, app
from MoonXMusic.core.call import Moony
from MoonXMusic.utils import seconds_to_min, time_to_seconds
from MoonXMusic.utils.channelplay import get_channeplayCB
from MoonXMusic.utils.decorators.language import languageCB
from MoonXMusic.utils.decorators.play import PlayWrapper
from MoonXMusic.utils.formatters import formats
from MoonXMusic.utils.inline import (
    botplaylist_markup,
    livestream_markup,
    playlist_markup,
    slider_markup,
    track_markup,
)
from MoonXMusic.utils.logger import play_logs
from MoonXMusic.utils.stream.stream import stream
from config import BANNED_USERS, lyrical


@app.on_message(
    filters.command(
        [
            "play",
            "vplay",
            "cplay",
            "cvplay",
            "playforce",
            "vplayforce",
            "cplayforce",
            "cvplayforce",
        ]
    )
    & filters.group
    & ~BANNED_USERS
)
@PlayWrapper
async def play_commnd(
    client,
    message: Message,
    _,
    chat_id,
    video,
    channel,
    playmode,
    url,
    fplay,
):
    mystic = await message.reply_text(
        _["play_2"].format(channel) if channel else _["play_1"]
    )

    plist_id = None
    slider = None
    plist_type = None
    spotify = None

    user_id = message.from_user.id
    user_name = message.from_user.first_name

    audio_telegram = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )

    video_telegram = (
        (message.reply_to_message.video or message.reply_to_message.document)
        if message.reply_to_message
        else None
    )

    if audio_telegram:
        if audio_telegram.file_size > 104857600:
            return await mystic.edit_text(_["play_5"])

        duration_min = seconds_to_min(audio_telegram.duration)

        if (audio_telegram.duration) > config.DURATION_LIMIT:
            return await mystic.edit_text(
                _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
            )

        file_path = await Telegram.get_filepath(audio=audio_telegram)

        if await Telegram.download(_, message, mystic, file_path):
            message_link = await Telegram.get_link(message)
            file_name = await Telegram.get_filename(audio_telegram, audio=True)
            dur = await Telegram.get_duration(audio_telegram, file_path)

            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur,
            }

            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                err = (
                    e
                    if ex_type == "AssistantErr"
                    else _["general_2"].format(ex_type)
                )
                return await mystic.edit_text(err)

            return await mystic.delete()

        return

    elif video_telegram:

        if message.reply_to_message.document:
            try:
                ext = video_telegram.file_name.split(".")[-1]

                if ext.lower() not in formats:
                    return await mystic.edit_text(
                        _["play_7"].format(f"{' | '.join(formats)}")
                    )

            except:
                return await mystic.edit_text(
                    _["play_7"].format(f"{' | '.join(formats)}")
                )

        if video_telegram.file_size > config.TG_VIDEO_FILESIZE_LIMIT:
            return await mystic.edit_text(_["play_8"])

        file_path = await Telegram.get_filepath(video=video_telegram)

        if await Telegram.download(_, message, mystic, file_path):

            message_link = await Telegram.get_link(message)
            file_name = await Telegram.get_filename(video_telegram)
            dur = await Telegram.get_duration(video_telegram, file_path)

            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur,
            }

            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    video=True,
                    streamtype="telegram",
                    forceplay=fplay,
                )

            except Exception as e:
                ex_type = type(e).__name__
                err = (
                    e
                    if ex_type == "AssistantErr"
                    else _["general_2"].format(ex_type)
                )
                return await mystic.edit_text(err)

            return await mystic.delete()

        return

    elif url:

        if await YouTube.exists(url):

            if "playlist" in url:

                try:
                    details = await YouTube.playlist(
                        url,
                        config.PLAYLIST_FETCH_LIMIT,
                        message.from_user.id,
                    )

                except:
                    return await mystic.edit_text(_["play_3"])

                streamtype = "playlist"
                plist_type = "yt"

                if "&" in url:
                    plist_id = (url.split("=")[1]).split("&")[0]
                else:
                    plist_id = url.split("=")[1]

                img = config.PLAYLIST_IMG_URL
                cap = _["play_9"]

            else:

                try:
                    details, track_id = await YouTube.track(url)

                    if not details:
                        return await mystic.edit_text(
                            "❌ Failed to fetch track details."
                        )

                except:
                    return await mystic.edit_text(_["play_3"])

                streamtype = "youtube"
                img = details.get("thumb")
                cap = _["play_10"].format(
                    details.get("title", "Unknown"),
                    details.get("duration_min", "Live"),
                )

        else:
            return await mystic.edit_text("❌ Invalid URL")

    else:

        if len(message.command) < 2:
            buttons = botplaylist_markup(_)

            return await mystic.edit_text(
                _["play_18"],
                reply_markup=InlineKeyboardMarkup(buttons),
            )

        slider = True

        query = message.text.split(None, 1)[1]

        if "-v" in query:
            query = query.replace("-v", "")

        try:
            details, track_id = await YouTube.track(query)

            if not details:
                return await mystic.edit_text(
                    "❌ No track details found."
                )

        except Exception as ex:
            print(ex)
            return await mystic.edit_text(_["play_3"])

        streamtype = "youtube"

    if str(playmode) == "Direct":

        if not plist_type:

            if not details:
                return await mystic.edit_text(
                    "❌ Failed to fetch song details."
                )

            if details.get("duration_min"):

                duration_sec = time_to_seconds(
                    details["duration_min"]
                )

                if duration_sec > config.DURATION_LIMIT:
                    return await mystic.edit_text(
                        _["play_6"].format(
                            config.DURATION_LIMIT_MIN,
                            app.mention,
                        )
                    )

            else:

                buttons = livestream_markup(
                    _,
                    track_id,
                    user_id,
                    "v" if video else "a",
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )

                return await mystic.edit_text(
                    _["play_13"],
                    reply_markup=InlineKeyboardMarkup(buttons),
                )

        try:
            await stream(
                _,
                mystic,
                user_id,
                details,
                chat_id,
                user_name,
                message.chat.id,
                video=video,
                streamtype=streamtype,
                spotify=spotify,
                forceplay=fplay,
            )

        except Exception as e:
            ex_type = type(e).__name__

            err = (
                e
                if ex_type == "AssistantErr"
                else _["general_2"].format(ex_type)
            )

            return await mystic.edit_text(err)

        await mystic.delete()

        return await play_logs(message, streamtype=streamtype)
