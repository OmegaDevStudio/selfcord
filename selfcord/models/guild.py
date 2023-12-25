from __future__ import annotations
import itertools
from typing import TYPE_CHECKING, Optional
from .assets import Asset
from .channels import Convert
if TYPE_CHECKING:
    from ..bot import Bot


class Guild:
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(payload)

    def update(self, payload: dict):
        self.channels: list[Channel] = []
        self.emojis: list[Emoji] = []
        self.stickers: list[Sticker] = []
        self.roles: list[Role] = []
        # MUH OPTIMISATIONS: Zip Longest very cool bro
        for emoji, sticker, role, channel in itertools.zip_longest(
            payload["emojis"] if payload.get("emojis") is not None else [],
            payload["stickers"] if payload.get("stickers") is not None else [],
            payload["roles"] if payload.get("roles") is not None else [],
            payload["channels"] if payload.get("channels") is not None else [],
        ):
            if emoji is not None:
                self.emojis.append(Emoji(emoji, self.bot))

            if sticker is not None:
                self.stickers.append(Sticker(sticker, self.bot))

            if role is not None:
                self.roles.append(Role(role, self.bot))

            if channel is not None:
                chan = Convert(channel, self.bot)
                self.channels.append(chan)
                if self.bot.user:
                    self.bot.cached_channels[chan.id] = chan

        self.member_count = payload.get("member_count")
        self.lazy = payload.get("lazy")
        self.large = payload.get("large")
        self.joined_at = payload.get("joined_at")
        properties: Optional[dict] = payload.get("properties")
        if properties:
            self.id: str = properties["id"]
            self.owner_id: Optional[str] = (
                properties["owner_id"]
                if properties.get("owner_id") is not None
                else None
            )
            self.premium_tier: Optional[int] = properties.get("premium_tier")
            self.splash: Optional[Asset] = (
                Asset(self.id, properties["splash"])
                if properties.get("splash") is not None
                else None
            )
            self.nsfw_level: Optional[str] = (
                properties["nsfw_level"]
                if properties.get("nsfw_level") is not None
                else None
            )
            self.application_id: Optional[str] = (
                properties["application_id"]
                if properties.get("application_id") is not None
                else None
            )
            self.system_channel_flags: Optional[int] = properties.get(
                "system_channel_flags"
            )
            self.inventory_settings: Optional[str] = properties.get(
                "inventory_settings"
            )
            self.default_message_notifications: Optional[int] = properties.get(
                "default_message_notifications"
            )
            self.hub_type: Optional[int] = properties.get("hub_type")
            self.afk_channel: Optional[str] = properties.get("afk_channel")
            self.incidents_data: Optional[int] = properties.get(
                "incidents_data")
            self.discovery_splash: Optional[Asset] = (
                Asset(self.id, properties["discovery_splash"])
                if properties.get("discovery_splash") is not None
                else None
            )
            self.preferred_locale: Optional[str] = properties.get(
                "preferred_locale")
            self.icon: Optional[Asset] = (
                Asset(self.id, properties["icon"]).from_icon()
                if properties.get("discovery_splash") is not None
                else None
            )
            self.latest_onboarding_question_id: Optional[str] = properties.get(
                "latest_onboarding_question_id"
            )
            self.explicit_content_filter: Optional[int] = properties.get(
                "explicit_content_filter"
            )
            self.description: Optional[str] = properties.get("description")
            self.afk_timeout: Optional[int] = properties.get("afk_timeout")
            self.max_video_channel_users: Optional[int] = properties.get(
                "max_video_channel_users"
            )
            self.nsfw: Optional[bool] = properties.get("nsfw")
            self.system_channel_id: Optional[str] = properties.get(
                "system_channel_id")
            self.rules_channel_id: Optional[str] = properties.get(
                "rules_channel_id")
            self.max_stage_video_channel_users: Optional[int] = properties.get(
                "max_stage_video_channel_users"
            )
            self.banner: Optional[Asset] = (
                Asset(self.id, properties["banner"])
                if properties.get("banner") is not None
                else None
            )
            self.public_updates_channel_id: Optional[int] = properties.get(
                "public_updates_channel_id"
            )
            self.mfa_level: Optional[int] = properties.get("mfa_level")
            self.features: Optional[list[str]] = properties.get("features")
            self.max_members: Optional[int] = properties.get("max_members")
            self.name: Optional[str] = properties.get("name")
            self.safety_alerts_channel_id: Optional[int] = properties.get(
                "safety_alerts_channel_id"
            )
            self.premium_progress_bar_enabled: Optional[bool] = properties.get(
                "premium_progress_bar_enabled"
            )
            self.verification_level: Optional[int] = properties.get(
                "verification_level"
            )
            self.home_header: Optional[str] = properties.get("home_header")
            self.vanity_url_code: Optional[str] = properties.get(
                "vanity_url_code")


class Emoji:
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(payload)

    def update(self, payload: dict):
        self.roles = payload.get("roles")
        self.name = payload.get("name")
        self.require_colons = payload.get("require_colons")
        self.managed = payload.get("managed")
        self.id = payload["id"]
        self.available = payload.get("available")
        self.animated = payload.get("animated")


class Role:
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(payload)

    def update(self, payload: dict):
        self.unicode_emoji = payload.get("unicode_emoji")
        self.position = payload.get("position")
        self.permissions = payload.get("permissions")
        self.name = payload.get("name")
        self.mentionable = payload.get("mentionable")
        self.managed = payload.get("managed")
        self.id = payload["id"]
        self.icon = payload.get("icon")
        self.hoist = payload.get("hoist")
        self.flags = payload.get("flags")
        self.color = payload.get("color")


class Sticker:
    def __init__(self, payload: dict, bot: Bot):
        self.bot = bot
        self.http = bot.http
        self.update(payload)

    def update(self, payload: dict):
        self.type = payload.get("type")
        self.tags = payload.get("tags")
        self.name = payload.get("name")
        self.id = payload.get("id")
        self.guild_id = payload.get("guild_id")
        self.format_type = payload.get("format_type")
        self.description = payload.get("description")
        self.available = payload.get("available")
        self.asset = payload.get("asset")
