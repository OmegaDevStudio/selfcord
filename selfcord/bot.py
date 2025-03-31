from __future__ import annotations

import ast
from time import perf_counter
import asyncio
import contextlib
import importlib
import inspect
import io
import os
import random
import sys
import time
import urllib

from collections import defaultdict
from traceback import format_exception
from typing import TYPE_CHECKING, Optional, Literal
from urllib.parse import urlparse

import aiofiles
import aiohttp
from aioconsole import aexec, aprint

from selfcord.models.sessions import Session

from .api import Gateway, HttpClient, ReconnectWebsocket
from .models import (
    Client, DMChannel, GroupChannel, Guild,
    Message, TextChannel, User, VoiceChannel,
    Capabilities, Convert, Messageable,
    Role, Callable
)

from .utils import (
    Command, CommandCollection, Context, Event, Extension,
    ExtensionCollection, logging
)
from .utils.logging import handler
import sys


if TYPE_CHECKING:
    from .api import Voice

if sys.platform == "linux":
    import uvloop
    uvloop.install()

if sys.platform.lower().startswith("win"):
    import winloop # type: ignore
    winloop.install()




class Bot:
    """Bot instance as entry point to interact with the bot

    Args:
        debug (bool): Whether to start the bot in debug mode, defaults to False.
        prefixes (list[str]): Prefixes for the bot, defaults to s!.
        inbuilt_help (bool): Whether the inbuilt help command should be enabled, defaults to True.
        userbot (bool): Whether the bot should be a userbot rather than selfbot, defaults to False.
        eval (bool): Whether to have the eval command as default, defaults to False.
    """

    def __init__(
        self,
        prefixes: list[str] = ["s!"],
        inbuilt_help: bool = True,
        userbot: bool = False,
        token_leader: Optional[str] = None,
        eval: bool = False,
        decompress: bool = True,
    	password: Optional[str] = None
    ) -> None:
        self.inbuilt_help: bool = inbuilt_help
        self.token: str
        self.http: HttpClient = HttpClient(self)
        self.t1: float = time.perf_counter()
        self.session_id: str
        self.resume_url: str
        self.capabilities: Capabilities = Capabilities.default()
        self._events = defaultdict(list)
        self.commands = CommandCollection()
        self.prefixes: list[str] = (
            prefixes if isinstance(prefixes, list) else [prefixes]
        )
        self.extensions = ExtensionCollection()
        self.user: Client
        self.eval: bool = eval
        self.token_leader = token_leader
        self.bots = []
        if self.token_leader is not None:
            self.userbot: bool = True
        else:
            self.userbot: bool = userbot
        self.password: str = password
        self.cached_users: dict[str, User] = {}
        self.cached_channels: dict[str, Messageable] = {}
        self.cached_messages: dict[str, Message] = {}
        self.gateway: Gateway = Gateway(self, decompress)
        self.startup = perf_counter()
        self.semaphore = asyncio.BoundedSemaphore(1)

    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


        
    async def runner(self, token: str, multi_token: bool = False):
        data = await self.http.static_login(token)
        self.token = token
        if data is not None:
            
            self.user = Client(data, self)
       
            while True:
                try:
                    await self.gateway.start(token)
                except ReconnectWebsocket as e:
                    await self.gateway.close()
  


                

    def run(self, token: str):
        """Used to start connection to gateway as well as gather user information

        Args:
            token (str): _description_
        """
        self.token = token

        try: 
            asyncio.run(self.runner(token))
        except Exception as e:
            self.gateway.alive = False
            raise e

    @property
    def latency(self):
        """Latency of heartbeat ack, gateway latency essentially"""
        return self.gateway.latency

    # For events
    async def inbuilt_commands(self):
        """
        I call this on bot initialisation, it's the inbuilt help command
        """
        if self.inbuilt_help:
            @self.cmd("The help command!", aliases=["test"])
            async def help(ctx, cat=None):
                """The help command, dedicated to viewing all commands, extensions and information regarding commands."""
                if cat is None:
                    msg = f"```ini\n"
                    msg += f"[ {self.user} ]\nType <prefix>help <ext_name> to view commands relating to a specific extension. Type <prefix>help <cmd_name> to view information regarding a command.\n[ .Prefixes ] : {self.prefixes}\n\n"
                    msg += f"[ .Commands ]\n"
                    for command in self.commands:
                        msg += f". {command.name}: {command.description}\n"
                    msg += "\n[ .Extensions ]\n"
                    for ext in self.extensions:
                        msg += f"[ {ext.name} ] : [ {ext.description} ]\n"

                    msg += "```"
                    return await ctx.reply(f"{msg}")

                else:
                    name = cat.lower()
                    for ext in self.extensions:
                        if name == ext.name.lower():
                            msg = f"```ini\n[ {self.user.username} Selfbot ]\n"
                            msg += f"[ {self.user} ]\n\nType <prefix>help <ext_name> to view commands relating to a specific extension. Type <prefix>help <cmd_name> to view information regarding a command.\n\n[ .Prefixes ] : {self.prefixes}\n\n"
                            msg += f"[ .Commands ]\n"
                            for command in ext.commands:
                                if command.ext == ext.ext:
                                    msg += f". {command.name}: {command.description}\n"

                            msg += "```"
                            return await ctx.reply(f"{msg}")
                    else:
                        for cmd in self.commands:
                            if name == cmd.name.lower():
                                msg = f"```ini\n[ {self.user.username} Selfbot ]\n"
                                msg += f"[ {self.user} ]\n\nType <prefix>help <ext_name> to view commands relating to a specific extension. Type <prefix>help <cmd_name> to view information regarding a command.\n\n[ .Prefixes ] : {self.prefixes}\n\n"
                                msg += f"[ .{cmd.name} ]\n"
                                msg += f"[ Description ] :  {cmd.description} \n"
                                msg += f"[ Long Description ] :\n{cmd.func.__doc__}\n"
                                msg += f"[ Aliases ] : {cmd.aliases} \n"
                                args = inspect.signature(cmd.func)
                                msg += f"\n[ Example Usage ] :\n[ {self.prefixes[0]}{cmd.aliases[0]}"
                                for arg in args.parameters.keys():
                                    if arg in ["self", "ctx"]:
                                        continue
                                    msg += f" <{arg}>"
                                msg += " ]"

                                msg += "```"
                                return await ctx.reply(f"{msg}")
                        for ext in self.extensions:
                            for cmd in ext.commands:
                                if name == cmd.name.lower():
                                    msg = f"```ini\n[ {self.user.username} Selfbot ]\n"
                                    msg += f"[ {self.user} ]\n\nType <prefix>help <ext_name> to view commands relating to a specific extension. Type <prefix>help <cmd_name> to view information regarding a command.\n\n[ .Prefixes ] : {self.prefixes}\n\n"
                                    msg += f"[ .{cmd.name} ]\n"
                                    msg += f"[ Description ] :  {cmd.description} \n"
                                    msg += (
                                        f"[ Long Description ] :\n{cmd.func.__doc__}\n"
                                    )
                                    msg += f"[ Aliases ] :  {cmd.aliases} \n"
                                    args = inspect.signature(cmd.func)
                                    msg += f"\n[ Example Usage ] :\n[ {self.prefixes[0]}{cmd.aliases[0]}"
                                    for arg in args.parameters.keys():
                                        if arg in ["self", "ctx"]:
                                            continue
                                        msg += f" <{arg}>"
                                    msg += " ]"

                                    msg += "```"
                                    return await ctx.reply(f"{msg}")

        if self.eval:
            # print("EVAL ACTIVATE???")
            def clean_code(content):
                if content.startswith("```") and content.endswith("```"):
                    return "\n".join(content.split("\n")[1:])[:-3]
                else:
                    return content



            @self.cmd(description="Executes and runs code", aliases=["exec"])
            async def eval(ctx, *, code):
                """Runs python code via exec, intended for experienced usage. This can be DANGEROUS if you do not know what you are doing, use with caution."""
                if code.startswith("```"):
                    code = clean_code(code)
                # print("EVAL ACTIVATE???")
                envs = {
                    "bot": self,
                    "ctx": ctx,
                    "selfcord": sys.modules[__name__],
                    "__import__": __import__
                }
                
                try:
                    with contextlib.redirect_stdout(io.StringIO()) as f:
                        await aexec(code, local=envs)
                        result = f"```{f.getvalue()}\n```"
                except Exception as e:
                    error = "".join(format_exception(e, e, e.__traceback__))
                    result = f"```\n{error}```"

                await ctx.reply(result)

    def on(self, event: str, mass_token: bool = False):
        """Decorator for events

        Args:
            event (str): The event to check for
        """

        def decorator(coro):
            if not inspect.iscoroutinefunction(coro):
    
                raise Exception("Not a coroutine")
            else:
                self._events[event].append(Event(name=event, coro=coro, ext=None, mass_token=mass_token))

                def wrapper(*args, **kwargs):
                    result = self._events[event].append(
                        Event(name=event, coro=coro, ext=None, mass_token=mass_token)
                    )

                    return result

                return wrapper

        return decorator

    async def emit(self, event, *args, **kwargs):
        """Used to essentially push values to the decorator when the event fires

        Args:
            event (str): The event name
        """
        on_event = f"on_{event}"

        # try:
        if hasattr(self, on_event):
            await getattr(self, on_event)(*args, **kwargs)
        
        if event in self._events.keys():
            
            for Event in self._events[event]:
                if len(Event.coro.__code__.co_varnames) == 0:
                    asyncio.create_task(Event.coro())
                elif Event.coro.__code__.co_varnames[0] == "self":
                    asyncio.create_task(Event.coro(Event.ext, *args, **kwargs))

                else:
                    asyncio.create_task(Event.coro(*args, **kwargs))

    def cmd(self, description="", aliases=[], mass_token: bool = False):
        """Decorator to add commands for the bot

        Args:
            description (str, optional): Description of command. Defaults to "".
            aliases (list, optional): Alternative names for command. Defaults to [].

        Raises:
            RuntimeWarning: If you suck and don't use a coroutine
        """
        if isinstance(aliases, str):
            aliases = [aliases]

        def decorator(coro):
            name = coro.__name__
            if not inspect.iscoroutinefunction(coro):
   
                raise Exception("Not a coroutine")
                return
            else:
                cmd = Command(
                    name=name, description=description, aliases=aliases, func=coro, mass_token=mass_token
                )
                self.commands.add(cmd)
            return cmd

        return decorator
    

    async def load_tokens(self, tokens: list, prefixes: list[str] = ["!"], eval: bool = False):
        rmv = []
        for token in tokens:

            mass_bot = self.__class__(prefixes=prefixes, token_leader=self.user.id, eval=eval, inbuilt_help=False, )

            @mass_bot.cmd()
            async def help(ctx):
                desc = "```\n"
                for cmd in mass_bot.commands:
                    desc += f"{cmd.name}  :  {cmd.description}\n"
                desc += "```"
                await ctx.reply(desc)

            for cmd in self.commands:
                if cmd.mass_token:
                    rmv.append(cmd)
                    mass_bot.commands.add(cmd)

            for ext in self.extensions:
                for name, value in ext._events.items():
                    for item in value:
                        if item.mass_token:
                            
                            mass_bot._events[name].append(item)

            for name, value in self._events.items():
                for item in value:
                    if item.mass_token:
                        
                        mass_bot._events[name].append(item)
            
            self.bots.append(mass_bot)

        for rm in rmv:
            try:
                self.commands.remove(rm)
            except:
                pass

        for token, bot in zip(tokens, self.bots):
            asyncio.create_task(bot.runner(token, True))

    def add_cmd(self, coro, description="", aliases=[]):
        """
        Function to add commands manually without decorator
        Args:
            coro (coroutine): The function to add
            description (str, optional): Description of command. Defaults to "".
            aliases (list, optional): Alternative names for command. Defaults to [].

        Raises:
            RuntimeWarning: If you suck and don't use a coroutine
        """
        if isinstance(aliases, str):
            aliases = [aliases]
        name = coro.__name__
        if not inspect.iscoroutinefunction(coro):

            raise Exception("Not a coroutine")
        else:
            cmd = Command(
                name=name, description=description, aliases=aliases, func=coro
            )
            self.commands.add(cmd)

    async def load_extension(self, name: Optional[str] = None, url: Optional[str] = None, dir: Optional[str] = None):
        """
        Load various extensions/plugins/cogs if any.

        Args:
            name (str): Name of the extension to load
            url (str): URL you want to load
            dir (str): Directory you want to load

        Raises:
            ModuleNotFoundError: If you suck and don't know the name of what you want to load
        """
        if name is None and url is None:
            return
        if url is not None:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    text = await resp.text()

            if dir is None:
                path = os.path.basename(urlparse(url).path)

                if path.endswith(".py"):
                    if os.path.exists(path):
          
                        return

                    lines = text.splitlines()
                    async with aiofiles.open(path, "a+") as f:
                        for line in lines:
                            await f.write(f"{line}\n")

                    name = f"{os.path.basename(urlparse(url).path)[:-3]}"

                else:
 
                    return

            else:
                path = f"{dir}/{os.path.basename(urlparse(url).path)}"
                
                if path.endswith(".py"):
                    if os.path.exists(path):
               
                        return
                    if not os.path.exists(dir):
                        os.makedirs(dir)
                    lines = text.splitlines()
                    async with aiofiles.open(path, "a+") as f:
                        for line in lines:
                            await f.write(f"{line}\n")

                    name = f"{dir}.{os.path.basename(urlparse(url).path)[:-3]}"

                else:
        
                    return

                
                
        try:
            name = importlib.util.resolve_name(name, None) # type: ignore
        except Exception as e:
            raise e

        spec = importlib.util.find_spec(name) # type: ignore

        lib = importlib.util.module_from_spec(spec) # type: ignore

        try:
            spec.loader.exec_module(lib)
        except Exception as e:

            return
        try:
            ext = getattr(lib, "Ext")
        except Exception as e:
            raise e

        # Creates an Extension - ext in this case refers to the Ext class used for initialisation
        ext = Extension(
            name=ext.name,
            description=ext.description,
            ext=ext(self),
            _events=ext._events,
        )
        self.extensions.add(ext)
        try:
            for name, event in ext._events.items():
                for ext_event in event:
                    self._events[name].append(
                        Event(name=name, coro=ext_event.coro, ext=ext.ext)
                    )
        except Exception as e:
            raise e

    async def logout(self):
        await self.gateway.close()

    async def change_presence(self, activity: list[dict], status: Literal["online", "idle", "dnd", "invisible"] = "online", afk: bool = False):
        d = {"op": 3, "d": {"activities": activity, "status": status, "afk": afk, "since": int(time.time())}}

        await self.gateway.send_json(d)


    async def process_commands(self, msg):
        """
        What is called in order to actually get command input and run commands

        Args:
            msg (str): The message containing command
        """
        context = Context(msg, self)

        asyncio.create_task(context.invoke())
    
    def fetch_message(self, message_id: str) -> Optional[Message]:
        if message_id is None:
            return
        return self.cached_messages.get(message_id)

    def fetch_user(self, user_id: str) -> Optional[User]:
        if user_id is None:
            return
        return self.cached_users.get(user_id)
    
    def get_voice(self) -> Optional[Voice]:
        return self.gateway.voice

    def get_channel(self, channel_id: str) -> Optional[Messageable|Callable]:
        if channel_id is None:
            return
        return self.cached_channels.get(channel_id)
    
    def get_dm(self, user_id: str) -> Optional[DMChannel]:
        for channel in self.cached_channels.values():
            if isinstance(channel, DMChannel):
               
                if channel.recipient.id == user_id:
                    return channel


    # Cry it's O(N) - max 100 guilds so it's cool
    def fetch_guild(self, guild_id: str) -> Optional[Guild]:
        if guild_id is None:
            return
        for guild in self.user.guilds:
            if guild.id == guild_id:
                return guild

    
    def fetch_role(self, role_id: str) -> Optional[Role]:
        if role_id is None:
            return
        for guild in self.user.guilds:
            for role in guild.roles:
                if role.id == role_id:
                    return role



    async def get_user(self, user_id: str) -> Optional[User]:
        """
        Function to retrieve user data. Probably need to be friends with them to retrieve the details.

        Args:
            user_id (Str): ID of the other user.

        Returns:

            User: The User object
        """
        data = await self.http.request(method="get", endpoint=f"/users/{user_id}")
        if data is not None:
            user = User(data, bot=self)
            self.cached_users[user.id] = user
            return user
        return
    
    async def join_invite(self, invite_code: str) -> Optional[Guild|GroupChannel]:
        json = await self.http.request(method="post", endpoint=f"/invites/{invite_code}", json={})

        if json is not None:
            if "guild" in json:
                guild = Guild(json["guild"], bot=self)
                self.user.guilds.append(guild)
                return guild
            elif "channel" in json:
                channel = GroupChannel(json["channel"], bot=self)
                self.user.private_channels.append(channel)
                self.cached_channels[channel.id] = channel
                return channel


 
