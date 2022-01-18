# BOT COMMANDS
# Ultrabear 2021

import importlib

import asyncio, discord

import lib_sonnetcommands

importlib.reload(lib_sonnetcommands)

from lib_sonnetcommands import CommandCtx

from typing import List, Any, Container

# Import BOT OWNER
from LeXdPyK_conf import BOT_OWNER as KNOWN_OWNER

UNKNOWN_OWNER: Any = KNOWN_OWNER
BOT_OWNER: Container[int]

if isinstance(UNKNOWN_OWNER, (int, str)):
    BOT_OWNER = [int(UNKNOWN_OWNER)] if UNKNOWN_OWNER else []
elif isinstance(UNKNOWN_OWNER, (list, tuple)):
    BOT_OWNER = list(map(int, UNKNOWN_OWNER))
else:
    BOT_OWNER = []

BOT_OWNER = set(BOT_OWNER)


class fakersp:
    def __init__(self) -> None:
        self.status = "This didint actually fail"
        self.reason = "Its intentional trust me"


async def fatal_lol(message: discord.Message, args: List[str], client: discord.Client, ctx: CommandCtx) -> None:
    raise RuntimeError("This command is designed to fatal error")


async def fatal_lol2(message: discord.Message, args: List[str], client: discord.Client, ctx: CommandCtx) -> None:
    raise discord.errors.Forbidden(fakersp(), "This command is designed to fatal error")  # type: ignore[arg-type]


async def cont_echo(message: discord.Message, args: List[str], client: discord.Client, ctx: CommandCtx) -> None:
    await message.channel.send(f"{message.content}\n{args}")


async def bot_update(message: discord.Message, args: List[str], client: discord.Client, ctx: CommandCtx) -> None:
    proc = await asyncio.create_subprocess_exec("git", "pull")
    await proc.wait()
    await message.channel.send(f"returned {proc.returncode}")


async def get_commit(message: discord.Message, args: List[str], client: discord.Client, ctx: CommandCtx) -> None:

    proc = await asyncio.create_subprocess_exec("git", "log", "-n", "1", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()

    await message.channel.send(f"Most Recent Commit:```\n{stdout.decode('utf8')}{stderr.decode('utf8')}```")


def isowner(m: discord.Message) -> bool:
    return m.author.id in BOT_OWNER


category_info = {'name': 'botowner', 'pretty_name': 'OwnerTools', 'description': 'A module providing a commands api for ultrabear to play with lol'}

commands = {
    'exception2': {
        'pretty_name': 'exception2',
        'description': 'Cause an exception',
        'permission': ("bot-owner", isowner),
        'cache': 'keep',
        'execute': fatal_lol2
        },
    'exception': {
        'pretty_name': 'exception',
        'description': 'Cause an exception',
        'permission': ("bot-owner", isowner),
        'cache': 'keep',
        'execute': fatal_lol
        },
    'echoback':
        {
            'pretty_name': 'echoback',
            'description': 'Echo the exact message contents, to be used to debug systems that alter message content',
            'permission': ("bot-owner", isowner),
            'cache': 'keep',
            'execute': cont_echo
            },
    'gitlog': {
        'pretty_name': 'gitlog',
        'description': 'get the git log',
        'permission': ("bot-owner", isowner),
        'cache': 'keep',
        'execute': get_commit
        },
    'update': {
        'pretty_name': 'update',
        'description': 'update the bot',
        'permission': ("bot-owner", isowner),
        'cache': 'keep',
        'execute': bot_update
        },
    }

version_info = "ot-1.0.1"
