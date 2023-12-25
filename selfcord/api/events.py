import itertools
from aioconsole import aprint
from ..models import Guild, Convert, User, Message


class Handler:
    def __init__(self, bot) -> None:
        self.bot = bot

    async def handle_ready(self, data: dict):
        guilds = data.get("guilds", [])
        private_channels = data.get("private_channels", [])
        users = data.get("users", [])
        relationships = data.get("relationship", [])
        merged_members = data.get("merged_members", [])
        # LOOK AT ALL THIS OPTIMISATION
        for guild, channel, user, relation in itertools.zip_longest(
            guilds,
            private_channels,
            users,
            relationships,
        ):
            if guild is not None:
                self.bot.user.guilds.append(Guild(guild, self.bot))
            if channel is not None:
                chan = Convert(channel, self.bot)
                self.bot.user.private_channels.append(chan)
                self.bot.cached_channels[chan.id] = chan
            if user is not None:
                check_user = self.bot.fetch_user(user["id"])
                if check_user is None:
                    user = User(user, self.bot)
                    self.bot.cached_users[user.id] = user
                else:
                    check_user.partial_update(user)
            if relation is not None:
                check_user = self.bot.fetch_user(relation["id"])
                if check_user is None:
                    user = User(relation, self.bot)
                    self.bot.cached_users[user.id] = user
                    if relation["type"] == 1:
                        self.bot.user.friends.append(user)
                    if relation["type"] == 2:
                        self.bot.user.blocked.append(user)
                else:
                    check_user.partial_update(user)
        await self.bot.emit("ready")


    async def handle_ready_supplemental(self, data: dict):
        for guild in data['guilds']:
            for user in guild:
                check_user = self.bot.fetch_user(user['id'])
                if check_user is None:
                    user = User(user, self.bot)
                    self.bot.cached_users[user.id] = user
                else:
                    check_user.partial_update(user)
        for friend in data['friends']:
            check_user = self.bot.fetch_user(friend['id'])
            if check_user is None:
                user = User(friend, self.bot)
                self.bot.cached_users[user.id] = user
            else:
                check_user.partial_update(friend)
        for guild in data['merged_members']:
            for member in guild:
                check_user = self.bot.fetch_user(member['id'])
                if check_user is None:
                    user = User(member, self.bot)
                    self.bot.cached_users[user.id] = user
                    
        pass

    async def handle_message_create(self, data: dict):
        message = Message(data, self.bot)
        self.bot.cached_messages[message.id] = message
        await self.bot.process_commands(message)

    async def handle_message_delete(self, data: dict):
        pass


    async def handle_channel_delete(self, data: dict):
        pass

    async def handle_thread_create(self, data: dict):
        pass
        # cache[data['id']] = PublicThread(data)

    async def handle_thread_delete(self, data: dict):
        pass

    async def handle_server_create(self, data: dict):
        pass
        # we gotta do some research on this one
        # No literally just do print(data) and run the event loop it will show you the data

    async def handle_server_delete(self, data: dict):
        pass

    # do you think we should do something with presences too?
    # yesser, somehow we will connect User/Member with status/presence
    async def hand_channel_create(self, data: dict):
        self.bot.cached_channels[data["id"]] = Convert(data, self.bot)

    async def handle_guild_member_list_update(self, data: dict):
        print(data, "guild_member_list")

    async def handle_thread_list_sync(self, data: dict):
        print(data, "thread_list_sync")

    async def handle_guild_member_chunk(self, data: dict):
        print(data, "guild_member_chunk")
