from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from .assets import Asset

if TYPE_CHECKING:
    from ..bot import Bot
    from .guild import Guild, Role
    from .channels import DMChannel, Messageable


# Realise this might be fucked because my subclassism didn't work with channels
# So basically guys my epic OOP magic didn't work this is indeed fucked
# Time to copy and paste everything! Actually methods should be fine, attrs for some reason don't wanna work

class Status:
    def __init__(self, payload: dict):
        self.update(payload)

    def update(self, payload: dict):
        self.platforms = payload.keys()
        self.status = payload.values()


class User:
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(payload)

    def _remove_null(self, payload: dict):
        return {key: value for key, value in payload.items() if value is not None}

    def update(self, payload: dict):
        self.username: Optional[str] = payload.get("username")
        self.status: Optional[str] = payload.get("status")
        self.client_status: Optional[Status] = (
            Status(payload['client_status']) 
            if payload.get("client_status") is not None
            else None
        )
        self.broadcast = payload.get("broadcast")
        self.activities = payload.get("activities")
        self.id: Optional[str] = payload.get("id")  or payload.get("user_id")
        self.discriminator: Optional[str] = payload.get("discriminator")
        self.global_name: Optional[str] = payload.get("global_name")
        self.avatar: Optional[Asset] = (
            Asset(self.id, payload["avatar"]).from_avatar()
            if payload.get("avatar") is not None and self.id is not None
            else None
        )
        self.banner: Optional[Asset] = (
            Asset(self.id, payload["banner"]).from_avatar()
            if payload.get("banner") is not None and self.id is not None
            else None
        )
        self.banner_color: Optional[str] = payload.get("banner_color")
        self.accent_color: Optional[str] = payload.get("accent_color")
        self.display_name: Optional[str] = payload.get("global_name")
        self.flags: int = payload.get("flags", 0)
        self.avatar_decoration: Optional[str] = payload.get("avatar_decoration")
        self.is_bot = payload.get("bot", False)
        self.premium_since = payload.get("premium_since")

    def partial_update(self, payload: dict):
        for key, value in payload.items():
            if hasattr(self, key):
                if key == "banner":
                    setattr(self, key, (
                        Asset(self.id, payload["banner"]).from_avatar()
                        if payload.get("banner") is not None and self.id is not None
                        else None
                    ))
                elif key == "avatar":
                    setattr(self, key, (
                        Asset(self.id, payload["banner"]).from_avatar()
                        if payload.get("banner") is not None and self.id is not None
                        else None
                    ))
                elif key == "client_status":
                    setattr(self, key, (
                        Status(payload['client_status']) 
                        if payload.get("client_status") is not None
                        else None
                    ))
                elif key == "bot":
                    setattr(self, "is_bot", value)

                else:
                    setattr(self, key, value)


    async def friend(self):
        json = await self.http.request(
            "put", "/users/@me/relationships/" + self.id if self.id is not None else "", json={}
        )
        return User(json, self.bot)
    
    async def block(self):
        await self.http.request(
            "put", "/users/@me/relationships/" + self.id if self.id is not None else "", json={"type": 2}
        )

    async def reset_relationship(self):
        await self.http.request(
            "delete", "/users/@me/relationships/" + self.id if self.id is not None else "", json={}
        )

    async def create_dm(self) -> Optional[DMChannel]:
        json = await self.http.request(
            "post", "/channels", json={"recipients": [self.id if self.id is not None else ""]}
        )

        return DMChannel(json, self.bot) or None


class Client(User):
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.guilds: list[Guild] = []
        self.friends: list[User] = []
        self.blocked: list[User] = []
        self.private_channels: list[Messageable] = []

        super().__init__(payload, bot) 
        super().update(payload)
        self.update(payload) 

    def update(self, payload: dict):
        self.verified = payload.get("verified")
        self.purchased_flags = payload.get("purchased_flags")
        self.pronouns = payload.get("pronouns")
        self.premium_type = payload.get("premium_type")
        self.phone = payload.get("phone")
        self.nsfw = payload.get("nsfw_allowed")
        self.mobile = payload.get("mobile")
        self.desktop = payload.get("desktop")
        self.mfa = payload.get("mfa_enabled")

    def partial_update(self, payload: dict):
        payload = self._remove_null(payload)
        super().partial_update(payload)
        for key, value in payload.items():
            if hasattr(self, key):
                setattr(self, key, value)

class Member(User):
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        super().__init__(payload, bot)
        super().update(payload)

    def update(self, payload: dict):
        self.roles: list[Role] = []
        self.permissions = 0  # TODO: Create Permission class

    def partial_update(self, payload: dict):
        payload = self._remove_null(payload)
        super().partial_update(payload)
        for key, value in payload.items():
            if hasattr(self, key):
                setattr(self, key, value)



