from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from .assets import Asset
from .message import Message

if TYPE_CHECKING:
    from ..bot import Bot
    from .channels import Channel
    from .guild import Guild


# TODO: Implement webhooks


class Webhook:
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(payload)

    @property
    def url(self) -> str:
        return f"https://discord.com/api/webhooks/{self.id}/{self.token}"
    
    @property
    def avatar(self) -> Asset:
        return Asset(self.id, self.avatar_hash)
    
    @property
    def channel(self) -> Optional[Channel]:
        return self.bot.get_channel(self.channel_id)
    
    @property
    def guild(self) -> Optional[Guild]:
        return self.bot.fetch_guild(self.guild_id)
    


    def update(self, payload: dict):
        self.id = payload.get("id")
        self.type = payload.get("type")
        self.guild_id = payload.get("guild_id")
        self.channel_id = payload.get("channel_id")
        self.user = payload.get("user")
        self.name = payload.get("name")
        self.avatar_hash = payload.get("avatar", "")

        self.token = payload.get("token")
        self.application_id = payload.get("application_id")
        self.source_guild = payload.get("source_guild")
        self.source_channel = payload.get("source_channel")

    async def delete(self):
        await self.http.request(
            "DELETE",
            f"/webhooks/{self.id}/{self.token}"
        )

    async def send(self, content: Optional[str] = None):
        json = await self.http.request(
            "POST",
            f"/webhooks/{self.id}/{self.token}",
            json={
                "content": content,
            
            }
        )
        if json is not None:
            return Message(json, self.bot)
    
