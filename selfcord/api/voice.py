from websockets.client import connect
import ujson
from aioconsole import aprint
from typing import Optional
import time
import asyncio
import socket
import io
import struct
import ctypes
import array

try:
    import opuslib
    import nacl.secret
    import nacl.utils
except ImportError:
    pass



SAMPLING_RATE = 48000
CHANNELS = 2
FRAME_LENGTH = 20  # in milliseconds
SAMPLE_SIZE = struct.calcsize("h") * CHANNELS
SAMPLES_PER_FRAME = int(SAMPLING_RATE / 1000 * FRAME_LENGTH)
FRAME_SIZE = SAMPLES_PER_FRAME * SAMPLE_SIZE



class Source(io.BufferedIOBase):
    def __init__(self, source: bytes) -> None:
        self.source: io.BufferedIOBase = io.BytesIO(source)

    def read(self):
        data = self.source.read(FRAME_SIZE)
        if len(data) != FRAME_SIZE:
            return b''
        return data
    
    def __len__(self):
        return self.source.getbuffer().nbytes - self.source.tell()
    


    







class Voice:
    IDENTIFY = 0
    UDP_SELECT = 1
    READY = 2
    HEARTBEAT = 3
    SESSION_DESCRIPTION = 4
    HEARTBEAT_ACK = 6
    HELLO = 8


    def __init__(
        self,
        bot,
        voice_token: str,
        endpoint: str,
        server_id: str
    ) -> None:
        self.bot = bot
        self.voice_token = voice_token
        self.session_id = bot.session_id
        self.endpoint = endpoint
        self.server_id = server_id
        self.alive = False
        self.channel = None
        self.ws = None
        self.mode = "xsalsa20_poly1305_lite"
        self._lite_nonce = 0
        self.sequence = 0
        self.timestamp = 0
        try:
            self.encoder = opuslib.Encoder(SAMPLING_RATE, CHANNELS, application=2049) 
        except:
            pass
        self.socket: Optional[socket.socket] = None


    async def send(self, payload: dict):
        if self.ws:
            await self.ws.send(ujson.dumps(payload))

    async def recv(self):
        if self.ws:
            item = await self.ws.recv()
            json = ujson.loads(item)
      
            op = json['op']
            data = json['d']

            if op == self.HELLO:
                interval = data['heartbeat_interval'] / 1000.0
                await self.identify()
                asyncio.create_task(
                    self.heartbeat(interval)
                )
            
            if op == self.HEARTBEAT_ACK:
                pass


            if op == self.SESSION_DESCRIPTION:
                await self.handle_session_description(data)


            if op == self.READY:
                await self.handle_ready(data)

    async def handle_session_description(self, data: dict):
        self.secret_key = data['secret_key']
        self.audio_codec = data['audio_codec']
        self.media_session_id = data['media_session_id']

    

    async def handle_ready(self, data: dict):
        self.ssrc = data['ssrc']
        self.ip = data['ip']
        self.port = data['port']
        self.modes = data['modes']
        heartbeat_interval = data['heartbeat_interval']
        await self.ip_discovery()
        await self.udp_select()

    async def connect(self):
        self.ws = await connect(f"wss://{self.endpoint}", origin="https://discord.com")
        self.alive = True
    
    async def start(self):
        await self.connect()
        while self.alive:
            await self.recv()


        
    def encrypt_xsalsa20_poly1305_lite(self, header: bytes, data) -> bytes:
        box = nacl.secret.SecretBox(bytes(self.secret_key))
        nonce = bytearray(24)

        nonce[:4] = struct.pack('>I', self._lite_nonce)
        self.checked_add('_lite_nonce', 1, 4294967295)

        return header + box.encrypt(bytes(data), bytes(nonce)).ciphertext + nonce[:4]
    

    
    def encode(self, pcm_data: bytes):
        c_int16_ptr = ctypes.POINTER(ctypes.c_int16)
        max_len = len(pcm_data)
        pcm_ptr = ctypes.cast(pcm_data, c_int16_ptr) # type: ignore
        data = (ctypes.c_char * max_len)() # type: ignore

        ret = self.encoder.encode(pcm_data, FRAME_SIZE)
        return array.array('b', data[:len(ret)]).tobytes()

    
    async def send_audio_data(self, source: bytes):
        self.checked_add("sequence", 1, 65535)
        self.source = Source(source)
        start = time.perf_counter()
        loops = 0
        while len(self.source) != 0:
            
            data = self.source.read()
            loops += 1

            encoded = self.encode(data)
            packet = self.get_voice_packet(encoded)

            await self.speaking(speak=True)
            if self.socket:
                # await aprint("sending", len(data), f"LEFT: {len(self.source)}")
                self.socket.sendto(packet, (self.ip, self.port))

            next_time = start + (FRAME_LENGTH / 1000) * loops
            delay = max(0, (FRAME_LENGTH / 1000) +  (next_time - time.perf_counter()))
            await aprint(delay)
            await asyncio.sleep(delay)
            self.checked_add('timestamp', SAMPLES_PER_FRAME, 4294967295)
           
    
    def get_voice_packet(self, data):
        header = bytearray(12)

        # Formulate rtp header
        header[0] = 0x80
        header[1] = 0x78
        struct.pack_into('>H', header, 2, self.sequence)
        struct.pack_into('>I', header, 4, self.timestamp)
        struct.pack_into('>I', header, 8, self.ssrc)


        return self.encrypt_xsalsa20_poly1305_lite(header, data)


    
    def checked_add(self, attr: str, value: int, limit: int) -> None:
        val = getattr(self, attr)
        if val + value > limit:
            setattr(self, attr, 0)
        else:
            setattr(self, attr, val + value)


    async def speaking(self, speak: bool = False, priority = False):
        val = 0
        if speak:
            val += 1
        if priority:
            val += 4
        payload = {
            "op": 5,
            "d": {
               "speaking": int(val),
               "delay": 0,
               "ssrc": self.ssrc 
            }
        }
    
        await self.send(payload)

    async def identify(self):
        payload = {
            "op": self.IDENTIFY,
            "d": {
                "server_id": self.server_id,
                "user_id": self.bot.user.id,
                "session_id": self.session_id,
                "token": self.voice_token
            }
        }
        await self.send(payload)


    async def heartbeat(self, interval: int):
        while self.alive:
            await asyncio.sleep(interval)
            payload = {
                "op": self.HEARTBEAT, "d": int(time.time())
            }
            await self.send(payload)

    async def close(self):
        if self.ws:
            self.alive = False
            await self.ws.close()
            
    async def udp_select(self):
      
        payload = {
            "op": 1,
            "d": {
                "protocol": "udp",

                "data": {"address": self.my_ip, "port": self.my_port, "mode": self.mode},
            },
        }
        await self.send(payload)


    async def ip_discovery(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.socket.setblocking(False)

        packet = bytearray(74)
        struct.pack_into(">H", packet, 0, 1)
        struct.pack_into(">H", packet, 2, 70)
        struct.pack_into(">I", packet, 4, self.ssrc)
        self.socket.sendto(packet, (self.ip, self.port))

        while True:
            try:
                data = self.socket.recv(74)
                break
            except:
                continue
        ip_start = 8
        ip_end = data.index(0, ip_start)
        self.my_ip = data[ip_start:ip_end].decode("ascii")
        self.my_port = struct.unpack_from(">H", data, len(data) - 2)[0]
        print(self.my_ip, self.my_port)
    
    