from __future__ import annotations

import inspect
import re
import shlex
from collections import defaultdict
from traceback import format_exception
from typing import TYPE_CHECKING, Any, Optional
from ..models import Message
from .logging import logging
from aioconsole import aprint

if TYPE_CHECKING:
    from ..api import *
    from ..bot import Bot
    from ..models import *





class Extension:
    """Extension object. Discord.py equivalent of cogs, a helper system to help manage and organise code into multiple files"""

    def __init__(self, **kwargs):
        self.name: Optional[str] = kwargs.get("name")
        self.description: Optional[str] = kwargs.get("description")
        self.ext: Optional[Extension] = kwargs.get("ext")
        self._events = defaultdict(list)
        _events: defaultdict = self.ext._events
        commands: CommandCollection = self.ext.commands
        self.commands = CommandCollection()
        for cmd in commands.recents():
            setattr(cmd, "ext", self.ext)
            self.commands.add(cmd)
        self.commands.copy()
        commands.clear()
        self._events.update(_events)
        _events.clear()


class ExtensionCollection:
    """Extension collection, where extensions are stored into. Utilised for Extender, Extensions as a whole. This is also used within help commands and command invocation."""

    def __init__(self):
        self.extensions = {}

    def __iter__(self):
        yield from self.extensions.values()

    def __len__(self):
        return len(self.extensions.keys())

    def _is_already_registered(self, ext: Extension) -> bool:
        """Whether the specified Extension is already registered

        Args:
            ext (Extension): Extension to check

        Returns:
            bool: True or False
        """
        for extension in self.extensions.values():
            return ext.name == extension
        else:
            return False

    def add(self, ext: Extension):
        """Adds an extension

        Args:
            ext (Extension): Extension to add

        Raises:
            ValueError: Extension must be subclass of extension
            ValueError: A name or alias is already registered
        """
        if not isinstance(ext, Extension):
            raise ValueError("Extension must be subclass of Extension")
        if self._is_already_registered(ext):
            raise ValueError("A name or alias is already registered")
        # Add extension to the collection
        self.extensions[ext.name] = ext

    def get(self, alias: str) -> Optional[Extension]:
        """Get an extension

        Args:
            alias (str): Name of the extension

        Returns:
            Extension: Extension obtained
        """
        try:
            return self.extensions[alias]
        except KeyError as e:
            raise KeyError(f"Extension {alias} is not registered") from e
        for extension in self.extensions:
            if extension.name in extension.aliases:
                return extension


class Command:
    """Command Object pretty much"""

    def __init__(self, **kwargs):
        self.name: Optional[str] = kwargs.get("name")
        self.aliases: Optional[list[str]] = [self.name] + kwargs.get("aliases", [])
        self.description: Optional[str] = kwargs.get("description")
        self.mass_token: bool = kwargs.get("mass_token", False)
        self.func: Optional[function] = kwargs.get("func")
        self.check: Optional[Any] = inspect.signature(self.func).return_annotation
        self.signature = inspect.signature(self.func).parameters.items()


class CommandCollection:
    """Commands collection, where commands are stored into. Utilised for help commands and general command invocation."""

    def __init__(self, **kwargs):
        self.commands: dict[CommandCollection, function] = {}
        self.recent_commands: dict[CommandCollection, function] = {}

    def __len__(self):
        return len(self.commands)

    def __iter__(self):
        yield from self.commands.values()

    def _is_already_registered(self, cmd: Command) -> bool:
        """Whether the specified Command is already registered

        Args:
            cmd (Command): Command to check

        Returns:
            bool: True or False
        """
        for command in self.commands.values():
            for alias in cmd.aliases:
                return alias in command.aliases
            else:
                return False
        else:
            return False

    def append(self, collection):
        """Append to commands, and recent_commands

        Args:
            collection (CommandCollection): Collection instance

        Raises:
            ValueError: Collection must be subclass of CommandCollection
        """
        if not isinstance(collection, CommandCollection):
            raise ValueError("Collection must be subclass of CommandCollection")
        for item in collection:
            self.commands[item.name] = item
            self.recent_commands[item.name] = item

    def add(self, cmd: Command):
        """Add a Command to the collection

        Args:
            cmd (Command): Command to be added

        Raises:
            ValueError: cmd must be a subclass of Command
            ValueError: Name or Alias is already registered
        """
        if not isinstance(cmd, Command):
            raise ValueError("cmd must be a subclass of Command")
        if self._is_already_registered(cmd):
            raise ValueError("Name or Alias is already registered")
        self.commands[cmd.name] = cmd
        self.recent_commands[cmd.name] = cmd

    def remove(self, cmd: Command):
        if not isinstance(cmd, Command):
            raise ValueError(f"{cmd} is not a subclass of Command")
        self.recent_commands.pop(cmd.name)
        self.commands.pop(cmd.name)

    def recents(self):
        """View commands recently acquired

        Yields:
            Generator: [Command]
        """
        yield from self.recent_commands.values()

    def copy(self):
        """Copy commands from recents to main collection"""
        self.commands.update(self.recent_commands)
        self.clear()

    def clear(self):
        """Clear recents"""
        self.recent_commands.clear()

    def get(self, alias) -> Optional[Command]:
        """Get a specific command from the collection

        Args:
            alias (str): Name of the command

        Returns:
            Command: Command obtained
        """
        try:
            return self.commands[alias]
        except KeyError as e:
            raise KeyError(f"Command {alias} is not registered") from e
        for command in self.commands:
            if alias in command.aliases:
                return command


class Event:
    """Event object"""

    def __init__(self, name: str, coro, ext: Extension, mass_token: bool = False) -> None:
        self.name: str = name
        self.coro = coro
        self.ext: Extension = ext
        self.mass_token = mass_token


class Extender:
    """Extender subclass for extensions, used for implementing the decorators."""

    commands = CommandCollection()
    _events: defaultdict = defaultdict(list)

    def __init_subclass__(cls, name: str, description: str = "") -> None:
        super().__init_subclass__()
        cls.name = name
        cls.description = description

    @classmethod
    def cmd(cls, description: str = "", aliases: list[str] = []):
        """Decorator to add commands for the bot

        Args:
            description (str, optional): Description of command. Defaults to "".
            aliases (list[str], optional): Alternative names for command. Defaults to [].

        Raises:
            RuntimeWarning: If you suck and don't use a coroutine
        """
        if isinstance(aliases, str):
            aliases = [aliases]

        def decorator(coro):
            name = coro.__name__
            if not inspect.iscoroutinefunction(coro):
                
                raise RuntimeError("Not a coroutine")
            else:
                cmd = Command(
                    name=name, description=description, aliases=aliases, func=coro
                )
                cls.commands.add(cmd)

            return cmd

        return decorator

    @classmethod
    def on(cls, event: str, mass_token: bool = False):
        """Decorator for events

        Args:
            event (str): The event to check for
        """

        def decorator(coro):
            if not inspect.iscoroutinefunction(coro):
                raise RuntimeError("Not a coroutine")
            else:
                eve = Event(name=event, coro=coro, ext=cls, mass_token=mass_token)
                cls._events[event].append(eve)

                def wrapper(*args, **kwargs):
                    result = cls._events[event].append(eve)
                    return result

                return wrapper

        return decorator

    @classmethod
    def add_cmd(cls, coro, description="", aliases=[], mass_token: bool = False):
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
            raise RuntimeError("Not a coroutine")
        else:
            cmd = Command(
                name=name, description=description, aliases=aliases, func=coro, ext=cls, mass_token=mass_token
            )
            cls.commands.add(cmd)


class Context:
    """Context related for commands, and invocation"""

    def __init__(self, message: Message, bot: Bot) -> None:
        self.bot: Bot = bot
        self.message = message
        self.http = bot.http

    @property
    def author(self) -> User:
        return self.message.author

    @property
    def guild(self) -> Guild:
        return self.message.guild

    @property
    def channel(self) -> Messageable | Voiceable:
        return self.message.channel

    @property
    def content(self) -> str:
        return self.message.content

    @property
    def command(self) -> Optional[function]:
        if self.prefix is None:
            return None
        for command in self.bot.commands:
            for alias in command.aliases:
                if self.content.lower().startswith(self.prefix + alias):
                    return command
        for extension in self.bot.extensions:
            for command in extension.commands:
                for alias in command.aliases:
                    if self.content.lower().split(" ")[0] == self.prefix + alias:
                        self.extension = extension.ext
                        return command
        return None

    @property
    def alias(self) -> Optional[str]:
        for command in self.bot.commands:
            for alias in command.aliases:
                if self.content.lower().startswith(self.prefix + alias.lower()):
                    return alias
        for extension in self.bot.extensions:
            for command in extension.commands:
                for alias in command.aliases:
                    if self.content.lower().startswith(self.prefix + alias.lower()):
                        self.extension = extension.ext
                        return alias
        return None

    @property
    def prefix(self) -> Optional[str]:
        for prefix in self.bot.prefixes:
            if self.content.startswith(prefix):
                return prefix

    @property
    def command_content(self) -> Optional[str]:
        """The content minus the prefix and command name, essentially the args

        Returns:
            str: String of content
        """
        if self.alias is None:
            return
        try:
            cut = len(self.prefix + self.alias)
            return self.content[cut:]
        except:
            return None

    def get_converter(self, param) -> Optional[type[str]] | Any:
        if param.annotation is param.empty:
            return str
        if callable(param.annotation):
            return param.annotation
        else:
            raise ValueError("Not a callable")


    async def convert(self, param, value) -> str | Any:
        """Attempts to turn x value in y value, using get_converter func for the values

        Args:
            param (_type_): function parameter
            value (_type_): value in message

        Returns:
            Type[str]: The type of parameter
        """
        from ..models import User
        converter = self.get_converter(param)
        if converter is User:
            id = re.findall(r"[0-9]{18,19}", value)
            if len(id) > 0:
                user = await self.bot.get_user(id[0])
                return user
            raise ValueError("User not found")
        return converter(value)

    async def get_arguments(self) -> tuple[list, dict]:
        """Get arguments by checking function arguments and comparing to arguments in message.

        Returns:
            _type_: _description_
        """
        args: list[Any] = []
        kwargs: dict[Any, Any] = {}

        if self.command.signature is not None:
            signature = self.command.signature
        if self.command_content == "":
            return args, kwargs
        if self.command_content is None:
            return args, kwargs
        sh = shlex.shlex(self.command_content[1:], posix=False)
        sh.whitespace = " "
        sh.whitespace_split = True
        splitted = list(sh)

        
        for index, (name, param) in enumerate(signature):
            if name in ["ctx", "self"]:
                continue

            if param.kind is param.POSITIONAL_OR_KEYWORD:
                try:
                    arg: str | Any = await self.convert(param, splitted.pop(0))
                    args.append(arg)
                except Exception as e:
                    pass

            if param.kind is param.VAR_KEYWORD:
                for arg in splitted:
                    arg = await self.convert(param, arg)
                    args.append(arg)

            if param.kind is param.VAR_POSITIONAL:
                for arg in splitted:
                    arg = await self.convert(param, arg)
                    args.append(arg)

            if param.kind is param.KEYWORD_ONLY:
                arg = await self.convert(param, " ".join(splitted))
                kwargs[name] = arg

        for key in kwargs.copy():
            if not kwargs[key]:
                kwargs.pop(key)

        return args, kwargs

    async def invoke(self):
        """Used to actually run the command"""
        if self.command is None:
            return
        
        if self.bot.token_leader is not None:
            if self.message.author.id != self.bot.token_leader:
                return

        if not self.bot.userbot:
            if self.message.author.id != self.bot.user.id:
                return
        
        if self.command_content != None:
            args, kwargs = await self.get_arguments()
            func = self.command.func
            if func.__code__.co_varnames[0] == "self":
                args.insert(0, self.extension)
                args.insert(1, self)
            else:
                args.insert(0, self)

        try:
            await func(*args, **kwargs)
        except Exception as e:
            error = "".join(format_exception(e, e, e.__traceback__))
            raise Exception(error)


    async def reply(self, content, file_paths: Optional[list] = None, delete_after: Optional[int] = None, tts=False) -> Optional[Message]:
        """Helper function to reply to your own message containing the command

        Args:
            content (str): The message you would like to send
            tts (bool, optional): Whether message should be tts or not. Defaults to False.
        """
        return await self.message.reply(content, file_paths, delete_after, tts)

    async def send(self, content, file_paths: list = [], delete_after: Optional[int] = None, tts=False) -> Optional[Message]:
        """Helper function to send message to the current channel

        Args:
            content (str): The message you would like to send
            tts (bool, optional): Whether message should be tts or not. Defaults to False.
        """
        return await self.channel.send(content=content, files=file_paths, delete_after=delete_after, tts=tts)


    async def purge(self, amount: int = 0):
        """Helper function to purge messages in the current channel, uses asyncio gather.

        Args:
            amount (int): The amount of messages to purge, defaults to All.
        """
        await self.channel.purge(amount)

    async def typing(self):
        await self.channel.typing()

    async def edit(self, content, file_paths: list = [], delete_after: Optional[int] = None) -> Message:
        """Helper function to edit the message you sent

        Args:
            content (str): Content to edit to
        """
        return await self.message.edit(content, file_paths, delete_after)

