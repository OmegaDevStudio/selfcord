from __future__ import annotations
from typing import Self


class Asset:
    def __init__(self, id: str, hash: str) -> None:
        self.url: str = ""
        self.update(id, hash)

    def update(self, id: str, hash: str):
        self.id: str = id
        self.hash: str = hash

    def __str__(self) -> str:
        return self.url

    def from_avatar(self):
        self.url = (
            f"https://cdn.discordapp.com/avatars/{self.id}/{self.hash}.png?size=4096"
        )
        if self.hash.startswith("a_"):
            self.url = f"https://cdn.discordapp.com/avatars/{self.id}/{self.hash}.gif?size=4096"
        return self

    def from_icon(self) -> Self:
        self.url = (
            f"https://cdn.discordapp.com/icons/{self.id}/{self.hash}.png?size=4096"
        )
        if self.hash.startswith("a_"):
            self.url = (
                f"https://cdn.discordapp.com/icons/{self.id}/{self.hash}.gif?size=4096"
            )
        return self

    @property
    def is_animated(self):
        if self.hash.startswith("a_"):
            return True
        return False
