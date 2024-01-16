from __future__ import annotations

from typing import Optional
from .users import User, Status
from .guild import Emoji

class PresenceUpdate:
    def __init__(self, payload: dict, bot) -> None:
        self.bot = bot
        self.http = bot.http
        self.update(payload)

    def update(self, payload: dict):
        self.user = payload.get("user")
        if self.user is not None:
            if self.user.get("username") is not None:
                self.user = User(self.user, self.bot)
            else:
                self.user = self.bot.fetch_user(self.user['id']) if self.bot.fetch_user(self.user['id']) is not None else self.user['id']
        self.status = payload.get("status")
        self.client_status = Status(payload['client_status']) if payload.get("client_status") is not None else payload.get("client_status")
        self.activities = payload.get("activities")
        self.broadcast = payload.get("broadcast")

                

class MessageAddReaction:
    def __init__(self, payload: dict, bot) -> None:
        self.bot = bot
        self.http = bot.http
        self.update(payload)

    def update(self, payload):
        self.burst = payload.get("burst", False)
        self.message_id = payload.get("message_id")
        self.channel_id = payload.get("channel_id")
        self.channel = self.bot.fetch_channel(self.channel_id)
        self.message = self.bot.fetch_message(self.message_id)
        self.message_author_id = payload.get("message_author_id")
        self.message_author = self.bot.fetch_user(self.message_author_id)
        self.user_id = payload.get("user_id")
        self.user = self.bot.fetch_user(self.user_id)
        self.type = payload.get("type")
        self.emoji = Emoji(payload['emoji'], self.bot) if payload.get("emoji") is not None else None

    