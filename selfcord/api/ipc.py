import asyncio
import sys
import os
import tempfile
import json
import struct
from typing import Optional
import time


# Thanks to these people
# Pretty much took most of their code
# https://github.com/qwertyquerty/pypresence

class DiscordIPC:
    def __init__(self, application_id: str, pid: int = os.getpid()) -> None:
        self.application_id = application_id
        self.pid = pid

    @property
    def path(self):
        ipc = 'discord-ipc-'
        

        if sys.platform in ('linux', 'darwin'):
            tempdir = (os.environ.get('XDG_RUNTIME_DIR') or tempfile.gettempdir())
            paths = ['.', 'snap.discord', 'app/com.discordapp.Discord', 'app/com.discordapp.DiscordCanary']
        elif sys.platform == 'win32':
            tempdir = r'\\?\pipe'
            paths = ['.']
        else:
            return
        
        for path in paths:
            full_path = os.path.abspath(os.path.join(tempdir, path))
            if sys.platform == 'win32' or os.path.isdir(full_path):
                for entry in os.scandir(full_path):
                    if entry.name.startswith(ipc) and os.path.exists(entry):
                        return entry.path
                    
    async def read_output(self):
        try:
            msg = await asyncio.wait_for(self.read.read(8), 20)
            status_code, length = struct.unpack('<II', msg[:8])
            data = await asyncio.wait_for(self.read.read(length), 20)
        except (BrokenPipeError, struct.error):
            raise BrokenPipeError
        except asyncio.TimeoutError:
            return
        payload = json.loads(data.decode('utf-8'))
        if payload["evt"] == "ERROR":
            raise RuntimeError(payload["data"]["message"])
        return payload


    def send(self, op: int, payload: dict):
        payload = json.dumps(payload)

        
        self.write.write(
            struct.pack(
                '<II',
                op,
                len(payload)
            ) + payload.encode('utf-8')
        )


    async def connect(self):
        self.read, self.write = await asyncio.open_unix_connection(self.path)

        self.send(0, {'v': 1, 'client_id': self.application_id})
        msg = await self.read.read(8)
        code, length = struct.unpack('<ii', msg)
        msg = json.loads((await self.read.read(length)))
        if "code" in msg:
            if msg['message'] == "Invalid Client Id":
                raise RuntimeError("You failed, wrong ID")
            
        asyncio.create_task(self.loop())

    def close(self):
        self.send(2, {'v': 1, 'client_id': self.application_id})
        self.write.close()
        self.loop.close()
            
    async def loop(self):
        while True:
            await self.read_output()

    
    async def update_presence(
        self,
        state: Optional[str] = None,
        details: Optional[str] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        large_image: Optional[str] = None,
        large_text: Optional[str] = None,
        small_image: Optional[str] = None,
        small_text: Optional[str] = None,
        party_id: Optional[str] = None,
        party_size: Optional[list] = None,
        join: Optional[str] = None,
        match: Optional[str] = None,
        spectate: Optional[str] = None,
        buttons: Optional[list] = None,
        instance: bool = True, payload_override: Optional[dict] = None
    ):
        if payload_override:
            payload = payload_override
        else:
            if start:
                start = int(start)
            if end:
                end = int(end)

            activity = {
                "state": state,
                "details": details,
                "timestampts": {
                    "start": start,
                    "end": end
                },
                "assets": {
                    "large_image": large_image,
                    "large_text": large_text,
                    "small_image": small_image,
                    "small_text": small_text,
                },
                "party": {
                    "party_id": party_id,
                    "size": party_size
                },
                "secrets": {
                    "join": join,
                    "spectate": spectate,
                    "match": match
                },
                "buttons": buttons,
                "instance": instance
            }
            payload = {
                "cmd": "SET_ACTIVITY",
                "args": {
                    "pid": self.pid,
                    "activity": activity
                },
                "nonce": f"{time.time():.20f}",
            }
        self.send(1, payload)

