from __future__ import annotations

import asyncio
import socket
import struct
import time

import ujson
import websockets
from aioconsole import aprint

try:
    import nacl.secret
    import nacl.utils
    import opuslib
except:
    pass
import io
import os
from traceback import format_exception
from typing import TYPE_CHECKING, Any

import aiofiles

# import ffmpeg
from ...utils import logging

if TYPE_CHECKING:
    from ...api import http
    from ...bot import Bot


log = logging.getLogger(__name__)


class Voice:
    """Voice class used to interact with voice websockets and send data"""

    SAMPLING_RATE = 48000
    CHANNELS = 2
    FRAME_LENGTH = 20  # in milliseconds
    SAMPLE_SIZE = struct.calcsize("h") * CHANNELS
    SAMPLES_PER_FRAME = int(SAMPLING_RATE / 1000 * FRAME_LENGTH)
    FRAME_SIZE = SAMPLES_PER_FRAME * SAMPLE_SIZE

    """Op codes"""
    READY = 2
    SESSION_DESCRIPTION = 4
    HEARTBEAT_ACK = 6
    HEARTBEAT = 8

    def __init__(
        self,
        session_id: str,
        token: str,
        endpoint: str,
        server_id: str,
        bot: Bot,
    ) -> None:
        self.session_id: str = session_id
        self.token: str = token
        self.endpoint: str = endpoint
        self.server_id: str = server_id
        self.bot: Bot = bot
        self.alive = False
        self.mode = "xsalsa20_poly1305"
        self.sequence = 0
        self.timestamp = 0

    async def connect(self):
        """Connect to discord voice ws"""
        self.ws = await websockets.connect(
            f"wss://{self.endpoint}", origin="https://discord.com"
        )
        self.alive = True

    async def recv_msg(self):
        """
        Receives Message from websocket, encodes as json and runs tasks
        """
        item = ujson.loads(await self.ws.recv())
        op = item.get("op")  # Op code
        data = item.get("d")  # Data
        if op == self.READY:
            await self.handle_ready(data)

        elif op == self.HEARTBEAT:
            asyncio.create_task(self.heartbeat(data))

        elif op == self.SESSION_DESCRIPTION:
            await self.handle_description(data)

    async def handle_description(self, data: dict):
        self.secret_key: list[Any] = data.get("secret_key")

    # def pcm_encode(self, file: str):
    #     out, err = (
    #         ffmpeg
    #         .input(file)
    #         .output('-', format='s16le', acodec='pcm_s16le', ac=2, ar='48k')
    #         .overwrite_output()
    #         .run(capture_stdout=True, capture_stderr=True)
    #     )
    #     return out

    def encode_data(self, data: bytes):
        self.encoder = opuslib.Encoder(
            self.SAMPLING_RATE, self.CHANNELS, opuslib.APPLICATION_AUDIO
        )
        return self.encoder.encode(data, self.SAMPLES_PER_FRAME)

    def get_voice_packet(self, encoded: bytes):
        header = bytearray(12)

        header[0] = 0x80
        header[1] = 0x78
        struct.pack_into(">H", header, 2, self.sequence)
        struct.pack_into(">I", header, 4, self.timestamp)
        struct.pack_into(">I", header, 8, self.SSRC)
        return self.encrypt_xsalsa20_poly1305(header, encoded)

    def encrypt_xsalsa20_poly1305(self, header: bytes, data) -> bytes:
        box = nacl.secret.SecretBox(bytes(self.secret_key))
        nonce = bytearray(24)
        nonce[:12] = header
        return header + box.encrypt(bytes(data), bytes(nonce)).ciphertext

    def checked_add(self, attr: str, value: int, limit: int):
        val = getattr(self, attr)
        if val + value > limit:
            setattr(self, attr, 0)
        else:
            setattr(self, attr, val + value)

    async def send_encode_audio_data(self, data: bytes):
        self.checked_add("sequence", 1, 65535)
        buffer = io.BytesIO(data)
        while True:
            data = buffer.read(self.FRAME_SIZE)
            if len(data) == 0:
                break
            encoded = self.encode_data(data)
            packet = self.get_voice_packet(encoded)
            await self.speak(True)
            self.socket.sendto(packet, (self.endpoint_IP, self.voice_port))

            await asyncio.sleep(self.FRAME_LENGTH / 1000)
        await self.speak(False)
        self.checked_add("timestamp", self.SAMPLES_PER_FRAME, 4294967295)

    async def send_audio_data(self, data: bytes):
        self.checked_add("sequence", 1, 65535)
        buffer = io.BytesIO(data)
        while True:
            data = buffer.read(self.FRAME_SIZE)
            if len(data) == 0:
                break
            packet = self.get_voice_packet(data)
            await self.speak(True)
            self.socket.sendto(packet, (self.endpoint_IP, self.voice_port))
            await asyncio.sleep(self.FRAME_LENGTH / 1000)
        await self.speak(False)
        self.checked_add("timestamp", self.SAMPLES_PER_FRAME, 4294967295)

    async def play(self, path):
        await self.speak(False)
        if os.path.exists(path):
            if os.path.isfile(path):
                async with aiofiles.open(path, mode="rb") as f:
                    data = await f.read()
                # data = self.pcm_encode(path)
                if path.endswith(".opus"):
                    await self.send_audio_data(data)
                else:
                    await self.send_encode_audio_data(data)
            else:
                RuntimeError("Path is not a file")
        else:
            RuntimeError("Path does not exist")

    async def speak(self, state):
        payload = {
            "op": 5,
            "d": {
                "speaking": int(state),
                "ssrc": self.SSRC,
                "delay": 0,
            },
        }
        await self.send_json(payload)

    async def send_json(self, payload: dict):
        """Send json to the websocket
        Args:
            payload (dict): Valid payload to send to the gateway
        """
        await self.ws.send(ujson.dumps(payload))

    async def close(self):
        """Close the connection to websocket"""
        self.alive = False
        await self.ws.close()

    async def identify(self):
        payload = {
            "op": 0,
            "d": {
                "server_id": self.server_id,
                "token": self.token,
                "session_id": self.session_id,
                "user_id": self.bot.user.id,
                "streams": [
                    {"type": "video", "rid": "100", "quality": 100},
                    {"type": "video", "rid": "50", "quality": 50},
                ],
                "video": True,
            },
        }
        await self.send_json(payload)

    async def start(self):
        await self.connect()
        await self.identify()
        while self.alive:
            try:
                await self.recv_msg()
            except KeyboardInterrupt:
                log.error("Shutting down")
                await self.close()
            except Exception as e:
                log.error(f"Websocket Unexpectedly closed {e}")
                await self.close()

    async def handle_ready(self, data: dict):
        self.SSRC = data.get("ssrc")
        self.endpoint_IP = data.get("ip")
        self.voice_port = data.get("port")
        await self.ip_discovery()

    async def heartbeat(self, data: dict):
        interval = data.get("heartbeat_interval") / 1000.0
        while self.alive:
            await asyncio.sleep(interval)
            payload = {"op": 3, "d": time.time()}
            await self.send_json(payload)

    async def udp_select(self):
        payload = {
            "op": 1,
            "d": {
                "protocol": "udp",
                "codecs": [
                    {
                        "name": "opus",
                        "type": "audio",
                        "priority": 1000,
                        "payload_type": 120,
                    }
                ],
                "data": {"address": self.IP, "port": self.port, "mode": self.mode},
            },
        }
        await self.send_json(payload)

    async def ip_discovery(self):
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(False)
        packet = bytearray(74)
        struct.pack_into(">H", packet, 0, 1)
        struct.pack_into(">H", packet, 2, 70)
        struct.pack_into(">I", packet, 4, self.SSRC)
        self.socket.sendto(packet, (self.endpoint_IP, self.voice_port))

        while True:
            try:
                data = self.socket.recv(74)
                break
            except:
                continue
        ip_start = 8
        ip_end = data.index(0, ip_start)
        self.IP = data[ip_start:ip_end].decode("ascii")
        self.port = struct.unpack_from(">H", data, len(data) - 2)[0]
        await self.udp_select()
