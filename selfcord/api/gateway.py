from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from zlib import decompressobj
import time
import asyncio
from .events import Handler
import websockets
from aioconsole import aprint
import ujson
from websockets.client import connect, ClientConnection
from .errors import ReconnectWebsocket
from websockets.exceptions import ConnectionClosed, ConnectionClosedError, ConnectionClosedOK
if TYPE_CHECKING:
    from ..bot import Bot
    from websockets import connection
    from ..models import Capabilities, Guild, Messageable
    from .voice import Voice


class Gateway:

    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    PRESENCE = 3
    VOICE_STATE = 4
    VOICE_PING = 5
    RESUME = 6
    RECONNECT = 7
    REQUEST_MEMBERS = 8
    INVALIDATE_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11
    GUILD_SYNC = 12

    def __init__(self, bot: Bot, decompress: bool = True) -> None:
        self.decompress = decompress
        self.bot: Bot = bot
        self.capabilities: Capabilities = self.bot.capabilities
        self.handler: Handler = Handler(bot)
        self.token: Optional[str] = None
        self.zlib = decompressobj(15)
        self.zlib_suffix: bytes = b"\x00\x00\xff\xff"
        self.last_ack: float = 0
        self.last_send: float = 0
        self.latency: float = float("inf")
        self.ws = None
        self.alive = False
        self.URL = (
            "wss://gateway.discord.gg/?encoding=json&v=9&compress=zlib-stream"
            if self.decompress else 
            "wss://gateway.discord.gg/?encoding=json&v=9"
        )
        self.voice: Optional[Voice] = None
        self.subscriptions_data = {}

    async def linux_run(self, cmd):
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stout, stderr = await proc.communicate()




    async def send_json(self, payload: dict):
        if self.ws:
            try:
                await self.ws.send(ujson.dumps(payload))
            except ConnectionClosed as e:
                await self.handle_reconnect(e)
        

    async def load_async(self, item):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, ujson.loads, item)

    async def recv_json(self):
        if self.ws:
            
            item = await self.ws.recv()
    
            if self.decompress:
                buffer = bytearray()
                try:
                    buffer.extend(item)
                except:
                    buffer = item
                if len(item) < 4 or item[-4:] != self.zlib_suffix:
                    return
                n = len(item)
                
                
                item = self.zlib.decompress(item)
                self.zlib.flush(n)
                
                
            item = await self.load_async(item)

            # await asyncio.sleep(1)

            if item:
                self.op = item["op"]
                data = item["d"]
                event = item["t"]
                self.seq = item["s"]

                if self.op == self.HELLO:
                    interval = data["heartbeat_interval"] / 1000.0
                    await self.identify()
                    asyncio.create_task(self.heartbeat(interval))

                elif self.op == self.HEARTBEAT_ACK:
                    self.heartbeat_ack()

                elif self.op == self.INVALIDATE_SESSION:
                    if data == False:
                        await self.close()
                        raise ReconnectWebsocket("Invalidated Session", resume=False, op=self.op)
                    else:
                        await self.close()
                        await asyncio.sleep(2)
                        await self.connect(self.bot.resume_url)
                        await self.resume()
                    

                elif self.op == self.RECONNECT:
                    # await aprint(f"Attempting reconnect???? {self.bot.user.username}")
                    # await self.linux_run(f"notify-send 'RECONNECT HAPPENING NOW CHECK CONSOLE {data} {op}'")
                    await self.close()
                    await asyncio.sleep(2)
                    await self.connect(self.bot.resume_url)
                    await self.resume()
                    

                elif self.op == self.DISPATCH:
                    if hasattr(self.handler, f"handle_{event.lower()}"):
                        method = getattr(
                            self.handler, f"handle_{event.lower()}")
                        asyncio.create_task(method(data))

    async def connect(self, url: str):
        self.ws = await connect(
            url, origin="https://discord.com", max_size=None,
            extra_headers={"user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0"},
            read_limit=1000000, max_queue=100, write_limit=1000000,
        )
        self.alive = True
        self.zlib = decompressobj(15)

    async def handle_reconnect(self, e: ConnectionClosed):
        # await aprint(f"Closing because fail. Attempting reconnect {self.bot.user.username}\n{e}")
        if e.rcvd is not None:
            if e.rcvd.code in [1000, 1001, 1011, 4000, 4001, 4002, 4003, 4005, 4007, 4008, 4009]:
                # await aprint(f"RECEIVE: {e.rcvd.code}  --- {e.rcvd.reason}")
                await self.close()
                await asyncio.sleep(2)
                await self.connect(self.bot.resume_url)
                await self.resume()
                
        if e.sent is not None:
            if e.sent.code in [1000, 1001, 1011, 4000, 4001, 4002, 4003, 4005, 4007, 4008, 4009]:
                # await aprint(f"SENT: {e.sent.code} --- {e.sent.reason}")
                await self.close()
                await asyncio.sleep(2)
                await self.connect(self.bot.resume_url)
                await self.resume()

        
        # await aprint("Raising error")
        await self.close()
        raise ReconnectWebsocket("Unknown", resume=False, op=False)

    async def start(self, token: str, resume: bool = False):
        if not resume:
            await self.connect(self.URL)
            
            self.token = token
            while self.alive:
                try:

                    await self.recv_json()

                except ConnectionClosed as e:
                    await self.handle_reconnect(e)

                



    async def resume(self):
        # await aprint(self.seq, self.bot.session_id)
        await self.send_json({
            "op": self.RESUME,
            "d": {"token": self.token, "session_id": self.bot.session_id, "seq":self.seq},
        })
        
    async def cache_guild(self, guild: Guild, channel):
        payload = {
            "op": 14,
            "d": {
                "guild_id": guild.id,
                "typing": True,
                "threads": False,
                "activities": True,
                "members": [],
                "channels": {
                    str(channel.id): [
                        [
                            0,
                            99
                        ]
                    ]
                }
            }
        }
        await self.send_json(payload)

    async def close(self):
        """This function closes the websocket
        """
        self.alive = False
        await self.ws.close()

    async def identify(self):
        payload = {
            "op": 2,
            "d": {
                "capabilities": self.capabilities.value,
                "token": self.token,
                "client_state": {
                    "guild_versions": {},
                    "api_code_version": 0,
                    "highest_last_message_id": "0",
                    "initial_guild_id": None,
                    "private_channels_version": "0",
                    "read_state_version": 0,
                    "user_guild_settings_version": -1,
                    "user_settings_version": -1,
                },
                "compress": False,
                "presence": {
                    "activities": [],
                    "afk": False,
                    "since": 0,
                    "status": "online",
                },
                "properties": {
                    "os": "Linux",
                    "browser": "Chrome",
                    "device": "",
                    "system_locale": "en-GB",
                    "browser_user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
                    "browser_version": "118.0.0.0",
                    "os_version": "",
                    "referrer": "",
                    "referring_domain": "",
                    "referrer_current": "",
                    "referring_domain_current": "",
                    "release_channel": "canary",
                    "client_build_number": 259975,
                    "client_event_source": None
                },

            },
        }
        await self.send_json(payload)



    async def heartbeat(self, interval: int):
        heartbeat_json = {"op": 1, "d": time.time()}
        while True:
            await asyncio.sleep(interval)
            await self.send_json(heartbeat_json)
            self.last_send = time.perf_counter()

    def heartbeat_ack(self):
        self.last_ack = time.perf_counter()
        self.latency = self.last_ack - self.last_send

    def roundup(self, n):
        import math
        return int(math.ceil(n / 100.0)) * 100
    
    def chunks(self, lst, n):
        for i in range(0, len(lst), 1):
            if len(lst[: i + 1]) > 3:
                for i in range(i, len(lst), n):
                    yield lst[i : i + n]
                break
            yield lst[: i + 1]

    def correct_channels(self, guild: Guild):
        roles = guild.me.roles
        
        channels = []
        for channel in guild.channels:
            if len(channel.permission_overwrites) > 0:
                for overwrite in channel.permission_overwrites:
                    if (overwrite.id == guild.id) or (overwrite.id in [role.id for role in roles]):
                        for permission in overwrite.allow.permissions:
                            for name, value in permission.items():
                                if name == "VIEW_CHANNEL":
                                    if value:
                                        
                                        channels.append(channel)
                                        break
  
    
                    for permission in overwrite.deny.permissions:
                        for name, value in permission.items():
                            if name == "VIEW_CHANNEL":
                                break
                        else:
                            
                            channels.append(channel)
                            break

        return list(set(channels))
    
    def get_ranges(self, amount: int):
        ranges = []
        for i in range(0, amount, 100):
            ranges.append(
                [i, self.roundup(i + (amount - i)) - 1]
            ) if i + 99 > amount else ranges.append([i, i + 99])
        return ranges
    
    async def subscriptions(self, guild: Guild, channels: Optional[list[Messageable]] = None):
       # In Progres...
       # Basically discord no longer uses op 14, uses this now
        if guild.member_count is not None:
            ranges = self.get_ranges(guild.member_count)
        if channels is None:
            channels = self.correct_channels(guild)
        self.subscriptions_data[guild.id] = {"channels": {}}
        self.subscriptions_data[guild.id]["channels"].update({channels[0].id: [0, 99]})

        payload = {
            "op": 37, 
            "d": {
                "subscriptions": self.subscriptions_data
            }
        }
        await self.send_json(payload)


    async def chunk_members(self, guild: Guild):
        channels = self.correct_channels(guild)
        channels = channels[:5]
        ranges = []

        if guild.member_count is not None:
            for i in range(0, guild.member_count, 100):
                ranges.append(
                    [i, self.roundup(i + (guild.member_count - i)) - 1]
                ) if i + 99 > guild.member_count else ranges.append([i, i + 99])
  
            
        for item in self.chunks(ranges, 3):

            queries = {}
            payload = payload = {
                "op": 14,
                "d": {
                    "guild_id": guild.id,
                    "typing": True,
                    "threads": False,
                    "activities": True,
                }
            }
            data = payload['d']

            # For now
            for channel in channels:
                queries[channel.id] = item

            data['channel'] = queries
            
            await self.send_json(payload)
            # print(payload)
            await asyncio.sleep(2.0)
        

    async def call(self, channel: str, guild: Optional[str] = None):
        payload = {
            "op": 4,
            "d": {
                "guild_id": guild,
                "channel_id": channel,
       
                "self_mute": False,
                "self_deaf": False,
                "self_video": False,
            },
        }
        await self.send_json(payload)


    async def video_call(self, channel: str, guild: Optional[str] = None):
        payload = {
            "op": 4,
            "d": {
                "guild_id": guild,
                "channel_id": channel,
    
                "self_mute": False,
                "self_deaf": False,
                "self_video": True,
            },
        }
        await self.send_json(payload)

    async def leave_call(self):
        payload = {
            "op": 4,
            "d": {
                "guild_id": None,
                "channel_id": None,
                "self_mute": False,
                "self_deaf": False,
                "self_video": False,
            },
        }
        await self.send_json(payload)
