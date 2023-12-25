from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from .users import User, Member
from .channels import Messageable
from .guild import Guild

if TYPE_CHECKING:
    from ..bot import Bot

class Message:
    def __init__(self, data: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(data)

    def update(self, payload: dict):
        self.id: Optional[str] = payload.get("id")
        self.content: Optional[str] = payload.get("content")
        self.type: int = payload.get("type", 0)
        self.tts: bool = payload.get("tts", False)
        self.timestamp: Optional[int] = payload.get("timestamp")
        self.replied_message: Optional[Message] = payload.get("referenced_message")
        self.pinned: Optional[bool] = payload.get("pinned")
        self.nonce: Optional[int] = payload.get("nonce")
        self.mentions: Optional[dict] = payload.get("mentions")
        self.channel_id: str = payload.get("channel_id", "")
        self.channel: Optional[Messageable] = self.bot.fetch_channel(self.channel_id)
        self.guild_id: str = payload.get("guild_id", "")
        self.guild: Optional[Guild] = self.bot.fetch_guild(self.guild_id)
        self.author: Optional[User] = (
            User(payload['author'], self.bot)
            if payload.get("author") is not None
            else None
        )
        # we will fix later 
        # self.member = Member(payload.get("member"), self.bot)
        self.flags: int = payload.get("flags", 0)
        # Create associated classes with these
        self.embeds = payload.get("embeds")
        self.components = payload.get("components")
        self.attachments = payload.get("attachments")
