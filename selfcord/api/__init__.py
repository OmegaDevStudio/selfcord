"""Where Selfcord interacts with discords API directly, using discord gateway (websockets) and http requests. This is also where events are located."""
from .gateway import Gateway
from .http import HttpClient
from .voice import *
from .errors import *
from .ipc import DiscordIPC
from .activity import Activity