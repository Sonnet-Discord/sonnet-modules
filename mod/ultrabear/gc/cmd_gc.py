# garbage collection commands
# Ultrabear 2021

import gc, psutil, time, os
import discord

from typing import Any, List

# Import BOT OWNER
from LeXdPyK_conf import BOT_OWNER

if (t := type(BOT_OWNER)) == str or t == int:
    BOT_OWNER = [int(BOT_OWNER)] if BOT_OWNER else []
elif BOT_OWNER:
    BOT_OWNER = [int(i) for i in BOT_OWNER]


async def psutil_call(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:

    p = psutil.Process(os.getpid())
    pid = p.pid
    mbused = p.memory_info()[0] // 1024**2

    await message.channel.send(f"```py\nPID: {pid}\nResident MB: {mbused}MB\nAutoCollection: {gc.isenabled()}\n```")


async def collection_call(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:

    tstart = time.monotonic_ns()
    amnt = gc.collect()
    tend = time.monotonic_ns()

    await message.channel.send(f"Cleaned out {amnt} objects, took {(tend-tstart)//1000//1000}ms")


def isowner(m):
    return m.author.id in BOT_OWNER


category_info = {'name': 'gc', 'pretty_name': 'Garbage Collector', 'description': 'Garbage collection and process info toolkit for developers'}

commands = {
    'gc-stats': {
        'pretty_name': 'gc-stats',
        'description': 'Give stats on used memory and PID',
        'permission': ('bot-owner', isowner),
        'cache': 'keep',
        'execute': psutil_call
        },
    'gc-collect': {
        'pretty_name': 'gc-collect',
        'description': 'runs gc.collect(), returns object collection count',
        'permission': ('bot-owner', isowner),
        'cache': 'keep',
        'execute': collection_call
        },
    }

version_info: str = "gc-1.0.0"
