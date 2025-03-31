from __future__ import annotations
from typing import Optional, TYPE_CHECKING, Literal
from .assets import Asset
from .permissions import Permission

if TYPE_CHECKING:
    from ..bot import Bot
    from .guild import Guild, Role
    from .channels import Convert, Messageable, DMChannel


# Realise this might be fucked because my subclassism didn't work with channels
# So basically guys my epic OOP magic didn't work this is indeed fucked
# Time to copy and paste everything! Actually methods should be fine, attrs for some reason don't wanna work

class Status:
    def __init__(self, payload: dict):
        self.update(payload)

    def __str__(self):
        return f"{self.platforms} // {self.status}"

    def update(self, payload: dict):
        self.platforms = [k for k in payload.keys()]
        self.status = [v for v in payload.values()]


class Profile():
    def __init__(self, id: str, payload: dict):
        self.id = id
        self.update(payload)

    def update(self, payload: dict):
        profile = payload["user_profile"]
        self.bio: Optional[str] = profile.get("bio")
        self.accent_color: Optional[str] = profile.get("accent_color")
        self.pronouns: Optional[str] = profile.get("pronouns")
        self.profile_effect: Optional[str] = profile.get("profile_effect")
        self.banner: Optional[Asset] = (
            Asset(self.id, payload["banner"]).from_avatar()
            if payload.get("banner") is not None and self.id is not None
            else None
        )
        self.theme_colors: Optional[list[int]] = payload.get("theme_colors")
        self.popout_animation_particle_type: Optional[str] = payload.get("popout_animation_particle_type")
        self.emoji: Optional[str] = payload.get("emoji")
        self.mutual_guilds = payload.get("mutual_guilds", [])
        


class User:
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(payload)


    def __str__(self):
        return f"{self.username}#{self.discriminator} ({self.id})"

    def __repr__(self):
        return f"<User id={self.id} name={self.display_name} discriminator={self.discriminator}>"


    def _remove_null(self, payload: dict):
        return {key: value for key, value in payload.items() if value is not None}
    

    
    async def profile(self) -> Optional[Profile]:
        resp = await self.http.request("GET", f"/users/{self.id}/profile?with_mutual_guilds=True")
        if resp is not None:
            return Profile(resp['user']['id'], resp)
        else:
            resp = await self.http.request("GET", f"/users/{self.id}/profile?with_mutual_guilds=False")
            if resp is not None:
                return Profile(resp['user']['id'], resp)


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
        self.id: Optional[str] = payload.get("id") or payload.get("user_id")

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
        self.global_name: Optional[str] = payload.get("global_name")
        self.flags: int = payload.get("flags", 0)
        self.avatar_decoration: Optional[str] = payload.get("avatar_decoration")
        self.is_bot = payload.get("bot", False)
        self.premium_since = payload.get("premium_since")

        self.session_id = payload.get("session_id")
        self.self_video = payload.get("self_video")
        self.suppress = payload.get("suppress")
        self.self_mute = payload.get("self_mute")
        self.self_deaf = payload.get("self_deaf")
        self.request_to_speak_timestamp = payload.get("request_to_speak_timestamp")
        self.mute = payload.get("mute")
        self.deaf = payload.get("deaf")
        

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
            "post", "/users/@me/channels", json={"recipients": [self.id if self.id is not None else ""]}
        )
        # print(json)

        return Convert(json, self.bot)


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

    

    async def add_friend(self, username: str, discriminator: Optional[str] = None):
        json = await self.http.request(
            "post", "/users/@me/relationships", json={"username": username, "discriminator": discriminator}
        )
        if json is not None:
            return User(json, self.bot)
        

    async def add_friend_id(self, id: str):
        json = await self.http.request(
            "PUT", "/users/@me/relationships/" + id, json={}

        )
        if json is not None:
            return User(json, self.bot)


    async def create_group(self, recipients: list[str], name: str):
        json = await self.http.request(
            "post", "/users/@me/channels", json={"recipients": recipients, "name": name}
        )
        if json is not None:
            return Convert(json, self.bot)


    async def edit_display_name(self, global_name: str):
        await self.http.request(
            "PATCH", "/users/@me",
            json={"global_nane": global_name}
        )

    async def edit_pfp(self, avatar_url: str, animated: bool = False):
        await self.http.request(
            "PATCH", "/users/@me",
            json={"avatar": (await self.http.encode_image(avatar_url, animated))}
        )

    async def edit_banner(self, banner_url: str, animated: bool = False):
        await self.http.request(
            "PATCH", "/users/@me/profile",
            json={"avatar": (await self.http.encode_image(banner_url, animated))}
        )

    async def edit_bio(self, bio: str):
        await self.http.request(
            "PATCH", "/users/@me/profile",
            json={"bio": bio}
        )
    

    async def redeem_nitro(self, code: str):
        json = await self.http.request(
            "post", f"/entitlements/gift-codes/{code}/redeem" + code, json={}
        )
        return json
    
    async def edit_hypesquad(self, house: int | Literal["bravery", "brilliance", "balance"]):
        match house:
            case "bravery":
                house = 1
            case "brilliance":
                house = 2
            case "balance":
                house = 3
            case _:
                raise ValueError("Invalid house")
            
        await self.http.request(
            "post", "/hypesquad/online", json={"house_id": house}
        )
                                               
                                               
    

class Member(User):
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        super().__init__(payload, bot)
        super().update(payload)
        self.update(payload)

    @property
    def guild(self):
        return self.bot.fetch_guild(self.guild_id)


    def update(self, payload: dict):
        self.roles: list[Role] = []
        self.permissions = None
        for role in payload.get("roles", []):
            role = self.bot.fetch_role(role)
            if role is not None:
                self.roles.append(role)
        
        self.guild_id: Optional[str] = payload.get("guild_id")
        self.joined_at: Optional[str] = payload.get("joined_at")
        self.premium_since: Optional[str] = payload.get("premium_since")
        self.deaf: bool = payload.get("deaf", False)
        self.mute: bool = payload.get("mute", False)
        self.pending: Optional[bool] = payload.get("pending")
        self.nick: Optional[str] = payload.get("nick")
        self.communication_disabled_until: Optional[str] = payload.get("communication_disabled_until")
        
        
    def partial_update(self, payload: dict):
        payload = self._remove_null(payload)
        super().partial_update(payload)
        for key, value in payload.items():
            if hasattr(self, key):
                if key == "roles":
                    self.roles = []
                    for role in value:
                        role = self.bot.fetch_role(role)
                        if role is not None:
                            self.roles.append(role)
                else:
                    setattr(self, key, value)


    async def kick(self, reason: str = ""):
        await self.http.request(
            "DELETE", f"/guilds/{self.guild_id}/members/{self.id}",
            headers={"X-Audit-Log-Reason": reason}
        )

    async def ban(self, reason: str = "", delete_message_seconds: int = 0):
        await self.http.request(
            "PUT", f"/guilds/{self.guild_id}/bans/{self.id}",
            json={"delete_message_seconds": delete_message_seconds},
            headers={"X-Audit-Log-Reason": reason}
        )

    async def unban(self):
        await self.http.request(
            "DELETE",
            f"/guilds/{self.guild_id}/bans/{self.id}",
        )
    



