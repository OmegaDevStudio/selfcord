from __future__ import annotations
import itertools

from typing import Optional
from .users import User, Status, Member
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
        self.channel = self.bot.get_channel(self.channel_id)
        self.message = self.bot.fetch_message(self.message_id)
        self.message_author_id = payload.get("message_author_id")
        self.message_author = self.bot.fetch_user(self.message_author_id)
        self.user_id = payload.get("user_id")
        self.user = self.bot.fetch_user(self.user_id)
        self.type = payload.get("type")
        self.emoji = Emoji(payload['emoji'], self.bot) if payload.get("emoji") is not None else None

class MemberListUpdate:
    def __init__(self, payload: dict, bot) -> None:
        self.bot = bot
        self.http = bot.http
        self.update(payload)

    def update(self, payload):
        self.member_count = payload.get("member_count")
        self.id = payload.get("id")
        self.guild_id = payload.get("guild_id")

        self.groups = []
        self.ops = []
        for group, op in itertools.zip_longest(payload.get("groups", []), payload.get("ops", [])):
            if group is not None:
                group.update({"guild_id": self.guild_id})
                self.groups.append(group)

            if op is not None:
                op.update({"guild_id": self.guild_id})
                self.ops.append(op)

class MemberOp():
    def __init__(self, payload: dict, bot) -> None:
        self.bot = bot
        self.http = bot.http
        self.update(payload)

    def update(self, payload):
        self.op = payload.get("op")
        self.range = payload.get("range")
        self.items = payload.get("items", [])
        self.index = payload.get("index")
        self.guild_id = payload.get("guild_id")
        for item in self.items:
            member = item.get("member")
            if member is not None:
                guild = self.bot.fetch_guild(self.guild_id)
                member = Member(member, self.bot)
                guild.members.append(member)


class Group:
    def __init__(self, payload: dict, bot) -> None:
        self.bot = bot
        self.http = bot.http
        self.update(payload)

    def update(self, payload):
        self.group_id = payload.get("id")
        self.count = payload.get("count")

class CallCreate:
    def __init__(self, payload: dict, bot) -> None:
        self.bot = bot
        self.http = bot.http
        self.update(payload)

    @property
    def channel(self):
        return self.bot.get_channel(self.channel_id)
    
    def update(self, payload):
        self.voice_states = []
        for user in payload.get("voice_states", []):
            
            check_user = self.bot.fetch_user(user['user_id'])
            if check_user is None:
                self.voice_states.append(User(user, self.bot))
            else:
                check_user.partial_update(user)
                self.voice_states.append(check_user)
        self.ringing = payload.get("ringing", [])
        self.region = payload.get("region")
        self.channel_id = payload.get("channel_id")

