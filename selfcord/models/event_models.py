from __future__ import annotations

from typing import Optional
from .users import User, Status

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

                
