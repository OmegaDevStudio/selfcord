from __future__ import annotations

from typing import Optional



class Activity:
    def __init__(self, payload: dict, bot) -> None:
        self.bot = bot
        self.http = bot.http

        self.update(payload)

    def update(self, payload: dict):
        self.application_id = payload.get("application_id")