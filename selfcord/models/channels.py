from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from .assets import Asset
import random
import asyncio

if TYPE_CHECKING:
    from .users import User
    from ..bot import Bot
    from ..api import DiscordHttp


BASE = "https://discord.com/api/v9"


class Messageable:
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.guild_id: str
        self.id: str
        self.type: int

    def update(self, payload):
        print("this is ran")
        self.id: str = payload["id"]
        self.type: int = int(payload["type"])
        self.flags = payload.get("flags")
        self.last_message_id: Optional[str] = payload.get("last_message_id")

    @property
    def nonce(self) -> int:
        return random.randint(100000, 99999999)

    async def send(
        self, content: str, files: Optional[list[str]] = None, delete_after: Optional[int] = None, tts: bool = False
    ):
        if self.type in (1, 3):
            headers = {"referer": f"https://canary.discord.com/channels/@me/{self.id}"}
        else:
            headers = {
                "referer": f"https://canary.discord.com/channels/{self.guild_id}/{self.id}"
            }
        await self.http.request(
            "POST",
            f"/channels/{self.id}/messages",
            headers=headers,
            json={"content": content, "flags": 0, "tts": tts, "nonce": self.nonce},
        )


class DMChannel(Messageable):
    def __init__(self, payload: dict, bot: Bot):
        super().__init__(payload, bot)
        super().update(payload)
        self.bot = bot
        self.http = bot.http
        self.update(payload)

    def update(self, payload: dict):
        self.recipient: Optional[User] = self.bot.fetch_user(
            payload["recipients"][0] if payload.get("recipients") is not None else ""
        )
        self.is_spam: Optional[bool] = payload.get("is_spam")

    async def delete(self):
        await self.http.request(
            "delete", BASE + "/channels/" + self.id + "?silent=false"
        )



class GroupChannel(Messageable):
    def __init__(self, payload: dict, bot: Bot):
        super().__init__(payload, bot)
        super().update(payload)
        self.bot = bot
        self.http = bot.http
        self.update(payload)

        print("in group channel")

    def update(self, payload: dict):
        self.recipient: list[Optional[User]] = (
            [self.bot.fetch_user(user) for user in payload["recipients"]]
            if payload.get("recipients") is not None
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


class TextChannel(Messageable):
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
        self.rate_limit_per_user = payload.get("rate_limit_per_user")
        self.name = payload.get("name")
        self.last_pin_timestamp = payload.get("last_pin_timestamp")

        self.permission_overwrites = payload.get("permission_overwrites")


class VoiceChannel(Messageable):
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
        self.permission_overwrites = payload.get("permission_overwrites")
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
        self.permission_overwrites = payload.get("permission_overwrites")


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
        self.permission_overwrites = payload.get("permission_overwrites")


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
        self.permission_overwrites = payload.get("permission_overwrites")


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
        self.permission_overwrites = payload.get("permission_overwrites")


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
        self.permission_overwrites = payload.get("permission_overwrites")


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
        self.permission_overwrites = payload.get("permission_overwrites")


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
        self.permission_overwrites = payload.get("permission_overwrites")


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

        self.permission_overwrites = payload.get("permission_overwrites")


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
        self.permission_overwrites = payload.get("permission_overwrites")


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
