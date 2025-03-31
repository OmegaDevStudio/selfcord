from __future__ import annotations

import asyncio
import datetime
import os
import random
import time
from io import BytesIO
from typing import TYPE_CHECKING, Literal, Optional

import aiofiles
import aiohttp
import ujson

from .assets import Asset
from .message import Message
from .permissions import Permission
from .webhooks import Webhook

if TYPE_CHECKING:
    from ..api import HttpClient
    from ..bot import Bot
    from .users import User


class PermissionOverwrite:
    def __init__(self, payload: dict, bot: Bot):
        self.bot: Bot = bot
        self.http = bot.http
        self.update(payload)

    def update(self, payload: dict):
        self.id: str = payload["id"]
        self.type: int = payload["type"]
        self.allow: Permission = Permission(payload["allow"], self.bot)
        self.deny: Permission = Permission(payload["deny"], self.bot)


class SlashCommand:
    def __init__(self, payload: dict, bot: Bot) -> None:
        self.bot = bot
        self.http = bot.http
        self.update(payload)

    def update(self, payload):

        self.id = payload.get("id")
        self.type = payload.get("type")
        self.application_id = payload.get("application_id")
        self.guild_id = payload.get("guild_id")
        self.version = payload.get("version")
        self.name = payload.get("name")
        self.description = payload.get("description")
        self.description_default = payload.get("description_default")
        self.options = [
            SubCommandOption(option, self) for option in payload.get("options", [])
        ]
        self.my_options = []
        self.integration_types = payload.get("integration_types")
        self.raw_data = payload
        self.required = payload.get("required", False)

    def add_value(self, name: str, value):
        new = {}

        if type(value) == list:
            for option in self.options:
                if option.name == name:
                    new["name"] = name
                    new["type"] = option.type
                    new["options"] = value
            return self.my_options.append(new)

        for option in self.options:
            if option.name == name:
                new["name"] = name
                new["value"] = value
                new["type"] = option.type
        return self.my_options.append(new)

    def get_option(self, name: str) -> Optional[SubCommandOption]:
        for option in self.options:
            if option.name == name:
                return option


class SubCommandOption(SlashCommand):
    def __init__(self, payload: dict, main: SlashCommand) -> None:
        self.cmd = main
        self.update(payload)

    def update(self, payload):
        self.opt_options = payload.get("options", [])
        self.name = payload.get("name")
        self.description = payload.get("description")
        self.required = payload.get("required", False)
        self.type = payload.get("type")
        self.my_options = []

    def add_value(self, name: str, value):
        new = {}
        for option in self.opt_options:
            if option.get("name", "") == name:
                new["name"] = name
                new["value"] = value
                new["type"] = option["type"]
        self.my_options.append(new)

    def reconstruct(self):
        self.cmd.add_value(self.name, self.my_options)


class Channel:
    def __init__(self, payload: dict, bot: Bot):
        self.bot: Bot = bot
        self.http: HttpClient = bot.http
        self.update(payload)

    def update(self, payload):
        self.id = payload["id"]
        self.type = payload["type"]
        self.flags = payload.get("flags")
        self.last_message_id = payload.get("last_message_id")
        self.guild_id = payload.get("guild_id")

    @property
    def guild(self):
        return self.bot.fetch_guild(self.guild_id)

    async def delete(self):
        await self.http.request("delete", "/channels/" + self.id, json={})


class Callable(Channel):
    def __init__(self, payload: dict, bot: Bot):
        self.bot: Bot = bot
        self.http: HttpClient = bot.http
        super().__init__(payload, self.bot)
        super().update(payload)
        self.update(payload)

    def update(self, payload):
        pass

    async def call(self):
        if self.type in (1, 3):
            await self.bot.gateway.call(self.id, None)
        else:
            await self.bot.gateway.call(self.id, self.guild_id)
        if self.guild_id is None:
            await self.ring()

        await asyncio.sleep(1.5)
        if self.bot.gateway.voice:
            self.bot.gateway.voice.channel = self.id
            asyncio.create_task(self.bot.gateway.voice.start())

    async def video_call(self):
        if self.type in (1, 3):
            await self.bot.gateway.video_call(self.id, None)
        else:
            await self.bot.gateway.video_call(self.id, self.guild_id)
        if self.guild_id is None:
            await self.ring()

        await asyncio.sleep(1.5)
        if self.bot.gateway.voice:
            self.bot.gateway.voice.channel = self.id
            asyncio.create_task(self.bot.gateway.voice.start())

    async def ring(self):
        await self.http.request(
            "POST", f"/channels/{self.id}/call/ring", json={"recipients": None}
        )

    async def leave_call(self):
        await self.bot.gateway.leave_call()
        if self.bot.gateway.voice:
            self.bot.gateway.voice.channel = None
            await self.bot.gateway.voice.close()


class Messageable(Channel):
    def __init__(self, payload: dict, bot: Bot):
        self.bot: Bot = bot
        self.http: HttpClient = bot.http
        super().__init__(payload, self.bot)
        super().update(payload)
        self.update(payload)

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id}>"

    def __str__(self):
        if hasattr(self, "name"):
            return self.name
        else:
            return self.recipient.username

    def update(self, payload):
        self.id: str = payload["id"]
        self.type: int = int(payload["type"])
        self.flags = payload.get("flags")
        self.last_message_id: Optional[str] = payload.get("last_message_id")

    def calc_nonce(self, date="now"):
        if date == "now":
            unixts = time.time()
        else:
            unixts = time.mktime(date.timetuple())
        return (int(unixts) * 1000 - 1420070400000) * 4194304

    @property
    def nonce(self) -> int:
        return self.calc_nonce()

    async def delayed_delete(self, message, time):
        await asyncio.sleep(time)
        await message.delete()

    async def get_slash_commands(
        self, name: Optional[str] = None
    ) -> Optional[SlashCommand] | Optional[list[SlashCommand]]:
        if self.guild_id is not None:
            json = await self.http.request(
                "GET", f"/guilds/{self.guild_id}/application-command-index"
            )
            if json is not None:
                cmds = []
                for cmd in json["application_commands"]:
                    if name is not None:
                        if cmd["name"] != name:
                            continue

                    if cmd.get("guild_id") is None:
                        cmd.update({"guild_id": self.guild_id})
                    cmds.append(SlashCommand(cmd, self.bot))

                if len(cmds) == 1:
                    return cmds[0]
                else:
                    return cmds

    async def trigger_slash(self, cmd: SlashCommand):
        if self.guild_id is not None:
            # print(cmd.my_options)

            json = {
                "type": 2,
                "application_id": cmd.application_id,
                "guild_id": self.guild_id,
                "channel_id": self.id,
                "session_id": self.bot.session_id,
                "data": {
                    "version": cmd.version,  # version not appending
                    "id": cmd.id,
                    "name": cmd.name,
                    "type": cmd.type,
                    "options": cmd.my_options,
                    "application_command": cmd.raw_data,
                },
            }
            json = ujson.dumps(json)
            boundary = f"----WebkitFormBoundaryAbCdEfGhIjKlmNoP"
            data = f'--{boundary}\r\nContent-Disposition: form-data; name="payload_json"\r\n\r\n{json}\r\n--{boundary}--'

            json = await self.http.request(
                "POST",
                "/interactions",
                headers={"content-type": f"multipart/form-data; boundary={boundary}"},
                data=data,
            )

    async def create_webhook(self, name: str):
        json = await self.http.request(
            "POST", f"/channels/{self.id}/webhooks", json={"name": name}
        )
        if json is not None:
            return Webhook(json, self.bot)

    async def typing(self):
        await self.http.request("POST", f"/channels/{self.id}/typing")

    async def upload_image(self, paths: list) -> list[dict[str, int | str]]:
        files = []
        id = 0
        for path in paths:
            if isinstance(path, (bytearray, bytes)):
                files.append(
                    {
                        "file_size": len(path),
                        "filename": f"{random.randint(1, 25555)}.png",
                        "id": id,
                    }
                )
            elif isinstance(path, BytesIO):
                files.append(
                    {
                        "file_size": path.getbuffer().nbytes,
                        "filename": f"{random.randint(1, 25555)}.png",
                        "id": id,
                    }
                )
            else:
                async with aiofiles.open(path, "rb") as f:
                    file = await f.read()
                    size = len(file)
                    name = os.path.basename(path)
                files.append({"file_size": size, "filename": f"{name}", "id": id})
            id += 1

        json = await self.http.request(
            "post", f"/channels/{self.id}/attachments", json={"files": files}
        )

        items = []
        for key, atch in enumerate(json["attachments"]):
            upload_url = atch["upload_url"]
            id = atch["id"]
            upload_filename = atch["upload_filename"]
            async with aiohttp.ClientSession() as session:
                if isinstance(paths[key], BytesIO):
                    file = paths[key].getvalue()
                elif isinstance(paths[key], (bytes, bytearray)):
                    file = paths[key]
                else:
                    async with aiofiles.open(paths[key], "rb") as f:
                        file = await f.read()
                async with session.put(upload_url, data=file):
                    pass
            items.append(
                {
                    "uploaded_filename": upload_filename,
                    "filename": os.path.basename(upload_filename),
                    "id": id,
                }
            )
        return items

    async def send(
        self,
        content: str = "",
        files: Optional[list[str]] = None,
        delete_after: Optional[int] = None,
        tts: bool = False,
    ) -> Optional[Message]:
        data = {"content": content, "tts": tts, "nonce": self.nonce}

        if files is not None and len(files) > 0:

            uploaded_files = await self.upload_image(files)
            data.update({"attachments": uploaded_files})

        if self.type in (1, 3):
            headers = {"referer": f"https://canary.discord.com/channels/@me/{self.id}"}
        else:
            headers = {
                "referer": f"https://canary.discord.com/channels/{self.guild_id}/{self.id}"
            }
        json = await self.http.request(
            "POST", f"/channels/{self.id}/messages", headers=headers, json=data
        )

        if json is not None:
            if delete_after != None:
                msg = Message(json, self.bot)
                await asyncio.create_task(self.delayed_delete(msg, delete_after))
                return msg

            return Message(json, self.bot)

    async def delete(self) -> Optional[Messageable]:
        if self.type in (1, 3):
            json = await self.http.request(
                "DELETE",
                f"/channels/{self.id}?silent=false",
                headers={
                    "referer": f"https://canary.discord.com/channels/@me/{self.id}"
                },
            )
        else:
            json = await self.http.request(
                "DELETE",
                f"/channels/{self.id}",
                headers={
                    "referer": f"https://canary.discord.com/channels/{self.guild_id}/{self.id}"
                },
            )

    async def history(self, limit: int = 50, bot_user_only: bool = False):
        n = 0
        if self.type in (1, 3):
            headers = {"referer": f"https://canary.discord.com/channels/@me/{self.id}"}
        else:
            headers = {
                "referer": f"https://canary.discord.com/channels/{self.guild_id}/{self.id}"
            }
        json = await self.http.request(
            "GET", f"/channels/{self.id}/messages?limit=50", headers=headers
        )
        msgs = []
        if json is None:
            return msgs

        for message in json:
            message.update({"guild_id": self.guild_id})
            msg = Message(message, self.bot)

            if bot_user_only:
                if msg.author.id == self.bot.user.id:
                    msgs.append(msg)
            else:
                msgs.append(msg)
            self.bot.cached_messages[msg.id] = msg
            n += 1

        if len(json) == 0:
            return msgs

        while n < limit:
            if json is None:
                return msgs

            if len(json) == 0:
                return msgs
            last = msgs[-1]
            json = await self.http.request(
                "GET",
                f"/channels/{self.id}/messages?before={last.id}&limit=50",
                headers=headers,
            )

            for message in json:
                message.update({"guild_id": self.guild_id})
                msg = Message(message, self.bot)
                if bot_user_only:
                    if msg.author.id == self.bot.user.id:
                        msgs.append(msg)
                else:
                    msgs.append(msg)
                self.bot.cached_messages[msg.id] = msg
                n += 1

        return msgs[:limit]

    async def search_base(
        self,
        content: Optional[str] = None,
        has: Optional[
            Literal["link", "embed", "file", "video", "image", "sound"]
        ] = None,
        from_: Optional[str] = None,
        mentions: Optional[str] = None,
        max: Optional[int] = None,
        min: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Optional[list[Message]]:
        params = {
            "content": content,
            "has": has,
            "from": from_,
            "mentions": mentions,
            "max": max,
            "min": min,
            "offset": offset,
        }
        params = {k: v for k, v in params.items() if v is not None}
        json = await self.http.request(
            "GET", f"/guilds/{self.id}/messages/search", params=params
        )

        if json is not None:
            for messages in json["messages"]:
                for message in messages:
                    message.update({"guild_id": self.guild_id})
                    msg = Message(message, self.bot)

                    self.bot.cached_messages[message.id] = msg
            return [
                Message(message, self.bot)
                for messages in json["messages"]
                for message in messages
            ]

    async def search(
        self,
        content: Optional[str] = None,
        has: Optional[
            Literal["link", "embed", "file", "video", "image", "sound"]
        ] = None,
        from_: Optional[str] = None,
        mentions: Optional[str] = None,
        max: Optional[int] = None,
        min: Optional[int] = None,
        amount: int = 25,
    ) -> list[Message]:
        n = 0
        msgs = []
        while n < amount:
            msg = await self.search_base(
                content=content,
                has=has,
                from_=from_,
                mentions=mentions,
                max=max,
                min=min,
                offset=n,
            )
            if msg is not None:
                if len(msg) == 0:
                    break
                n += len(msg)
                msgs.extend(msg)
        return msgs

    async def get_webhooks(self) -> Optional[list[Webhook]]:
        json = await self.http.request("GET", f"/channels/{self.id}/webhooks")
        if json is not None:
            return [Webhook(webhook, self.bot) for webhook in json]

    async def purge(self, amount: int):
        msgs = await self.history(amount, bot_user_only=True)
        for i in range(0, len(msgs), 2):
            await asyncio.gather(*(msg.delete() for msg in msgs[i : i + 2]))


class DMChannel(Messageable, Callable):
    def __init__(self, payload: dict, bot: Bot):

        super().__init__(payload, bot)

        super().update(payload)

        self.bot = bot
        self.http = bot.http

        self.update(payload)

    @property
    def recipient(self):
        return self.bot.fetch_user(self.recipient_id)

    def update(self, payload: dict):

        for recipien in payload.get("recipients", payload.get("recipient_ids", [])):
            if isinstance(recipien, str):
                self.recipient_id = recipien
            else:
                self.recipient_id = recipien["id"]

        self.is_spam: Optional[bool] = payload.get("is_spam")

    def get_user(self):
        self.recipient = self.bot.fetch_user(self.recipient_id)


class GroupChannel(Messageable, Callable):
    def __init__(self, payload: dict, bot: Bot):
        super().update(payload)
        super().__init__(payload, bot)
        self.bot = bot
        self.http = bot.http
        self.update(payload)

    def update(self, payload: dict):
        self.recipient: list[Optional[User]] = (
            [self.bot.fetch_user(user) for user in payload["recipient_ids"]]
            if payload.get("recipient_ids") is not None
            else []
        )
        self.is_spam: Optional[bool] = payload.get("is_spam")
        self.icon: Optional[Asset] = (
            Asset(self.id, payload["icon"]).from_icon()
            if payload.get("icon") is not None
            else None
        )
        self.name: Optional[str] = payload.get("name")
        self.last_pin_timestamp: Optional[int] = payload.get("last_pin_timestamp")

    async def leave(self):
        await self.http.request("DELETE", "/channels/" + self.id)

    async def edit(self, name: str, icon_url: Optional[str] = None):
        payload = {"name": name}
        if icon_url is not None:
            payload["icon"] = await self.http.encode_image(icon_url)

        await self.http.request("PATCH", "/channels/" + self.id, json=payload)


class TextChannel(Messageable):
    """
    This class is used to represent a text channel in Discord.
    """

    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(payload)
        super().update(payload)
        super().__init__(payload, bot)

    def update(self, payload):
        self.nsfw = payload.get("nsfw")
        self.guild_id = payload.get("guild_id")
        self.category_id = payload.get("parent_id")
        self.position = payload.get("position")
        self.rate_limit_per_user = payload.get("rate_limit_per_user")
        self.name = payload.get("name")
        self.last_pin_timestamp = payload.get("last_pin_timestamp")

        self.permission_overwrites = [PermissionOverwrite(overwrite, self.bot) for overwrite in payload.get("permission_overwrites", [])]  # type: ignore

    async def edit(
        self, name: str = "", topic: str = "", nsfw: bool = False, timeout: int = 0
    ):
        self.name = name
        self.nsfw = nsfw
        self.rate_limit_per_user = timeout

        await self.http.request(
            "patch",
            "/channels/" + self.id,
            json={
                "name": name,
                "type": 0,
                "topic": topic,
                "bitrate": 64000,
                "user_limit": 0,
                "nsfw": nsfw,
                "flags": 0,
                "rate_limit_per_user": timeout,
            },
        )


class VoiceChannel(Messageable, Callable):
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(payload)
        super().update(payload)
        super().__init__(payload, bot)

    def update(self, payload):
        self.guild_id = payload.get("guild_id")
        self.category_id = payload.get("parent_id")
        self.position = payload.get("position")
        self.permission_overwrites = [PermissionOverwrite(overwrite, self.bot) for overwrite in payload.get("permission_overwrites", [])]  # type: ignore
        self.user_limit = payload.get("user_limit")
        self.topic = payload.get("topic")
        self.rtc_region = payload.get("rtc_region")
        self.slowdown = payload.get("rate_limit_per_user")
        self.nsfw = payload.get("nsfw")
        self.name = payload.get("name")
        self.icon_emoji = payload.get("icon_emoji")
        self.bitrate = payload.get("bitrate")


class Category(Messageable):
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(payload)
        super().update(payload)
        super().__init__(payload, bot)

    def update(self, payload):
        self.name = payload.get("name")
        self.guild_id = payload.get("guild_id")
        self.position = payload.get("position")
        self.permission_overwrites = [PermissionOverwrite(overwrite, self.bot) for overwrite in payload.get("permission_overwrites", [])]  # type: ignore


class Announcement(Messageable):
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(payload)
        super().update(payload)
        super().__init__(payload, bot)

    def update(self, payload):
        self.name = payload.get("name")
        self.guild_id = payload.get("guild_id")
        self.position = payload.get("position")
        self.permission_overwrites = [PermissionOverwrite(overwrite, self.bot) for overwrite in payload.get("permission_overwrites", [])]  # type: ignore


class AnnouncementThread(Messageable):
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(payload)
        super().update(payload)
        super().__init__(payload, bot)

    def update(self, payload):
        self.name = payload.get("name")
        self.guild_id = payload.get("guild_id")
        self.position = payload.get("position")
        self.permission_overwrites = [PermissionOverwrite(overwrite, self.bot) for overwrite in payload.get("permission_overwrites", [])]  # type: ignore


class PublicThread(Messageable):
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(payload)
        super().update(payload)
        super().__init__(payload, bot)

    def update(self, payload):
        self.name = payload.get("name")
        self.guild_id = payload.get("guild_id")
        self.position = payload.get("position")
        self.permission_overwrites = [PermissionOverwrite(overwrite, self.bot) for overwrite in payload.get("permission_overwrites", [])]  # type: ignore


class PrivateThread(Messageable):
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(payload)
        super().update(payload)
        super().__init__(payload, bot)

    def update(self, payload):
        self.name = payload.get("name")
        self.guild_id = payload.get("guild_id")
        self.position = payload.get("position")
        self.permission_overwrites = [PermissionOverwrite(overwrite, self.bot) for overwrite in payload.get("permission_overwrites", [])]  # type: ignore


class StageChannel(Messageable):
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(payload)
        super().update(payload)
        super().__init__(payload, bot)

    def update(self, payload):
        self.last_message_id: Optional[str] = payload.get("last_message_id")
        self.name = payload.get("name")
        self.guild_id = payload.get("guild_id")
        self.position = payload.get("position")
        self.permission_overwrites = [PermissionOverwrite(overwrite, self.bot) for overwrite in payload.get("permission_overwrites", [])]  # type: ignore


class Directory(Messageable):
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(payload)
        super().update(payload)
        super().__init__(payload, bot)

    def update(self, payload):
        self.name = payload.get("name")
        self.guild_id = payload.get("guild_id")
        self.position = payload.get("position")
        self.permission_overwrites = [PermissionOverwrite(overwrite, self.bot) for overwrite in payload.get("permission_overwrites", [])]  # type: ignore


class ForumChannel(Messageable):
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(payload)
        super().update(payload)
        super().__init__(payload, bot)

    def update(self, payload):
        self.name = payload.get("name")
        self.guild_id = payload.get("guild_id")
        self.position = payload.get("position")
        self.topic = payload.get("topic")
        self.template = payload.get("template")
        self.slowdown = payload.get("rate_limit_per_user")
        self.category_id = payload.get("category_id")
        self.nsfw = payload.get("nsfw")
        self.default_thread_rate_limit_per_user = payload.get(
            "default_thread_rate_limit_per_user"
        )
        self.default_sort_order = payload.get("default_sort_order")
        self.default_reaction_emoji = payload.get("default_reaction_emoji")
        self.default_forum_layout = payload.get("default_forum_layout")
        self.available_tags = payload.get("available_tags")

        self.permission_overwrites = [PermissionOverwrite(overwrite, self.bot) for overwrite in payload.get("permission_overwrites", [])]  # type: ignore


class MediaChannel(Messageable):
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(payload)
        super().update(payload)
        super().__init__(payload, bot)

    def update(self, payload):
        self.name = payload.get("name")
        self.guild_id = payload.get("guild_id")
        self.position = payload.get("position")
        self.permission_overwrites = [PermissionOverwrite(overwrite, self.bot) for overwrite in payload.get("permission_overwrites", [])]  # type: ignore


class Convert(Messageable):
    def __new__(cls, payload: dict, bot: Bot) -> Messageable:

        tpe = payload["type"]

        if tpe == 0:
            return TextChannel(payload, bot)
        if tpe == 1:
            return DMChannel(payload, bot)
        if tpe == 2:
            return VoiceChannel(payload, bot)
        if tpe == 3:
            return GroupChannel(payload, bot)
        if tpe == 4:
            return Category(payload, bot)
        if tpe == 5:
            return Announcement(payload, bot)
        if tpe == 10:
            return AnnouncementThread(payload, bot)
        if tpe == 11:
            return PublicThread(payload, bot)
        if tpe == 12:
            return PrivateThread(payload, bot)
        if tpe == 13:
            return StageChannel(payload, bot)
        if tpe == 14:
            return Directory(payload, bot)
        if tpe == 15:
            return ForumChannel(payload, bot)
        if tpe == 16:
            return MediaChannel(payload, bot)
        return TextChannel(payload, bot)
