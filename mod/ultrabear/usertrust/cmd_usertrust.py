# UserTrust (for trolling nachog)
# Ultrabear 2021

import importlib

import discord

import lib_db_obfuscator

importlib.reload(lib_db_obfuscator)
import lib_parsers

importlib.reload(lib_parsers)

from lib_parsers import parse_role, parse_boolean
from lib_db_obfuscator import db_hlapi

from typing import Any, List


async def usertrust_role(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:

    verbose: bool = kwargs["verbose"]
    return await parse_role(message, args, "usertrust-trusted-role", verbose=verbose)


async def usertrust_count(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:

    try:
        count = int(args[0])
    except (ValueError, IndexError):
        await message.channel.send("ERROR: No int supplied or int is invalid")
        return 1

    if 2**32 < count or count < 10:
        await message.channel.send(f"ERROR: Count cannot exceed range 10-{2**32}")

    with db_hlapi(message.guild.id) as db:
        db.add_config("usertrust-message-count", str(count))

    await message.channel.send(f"Updated usertrust message count to {count}")


async def set_usertrust_use(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:

    if args:
        gate = bool(parse_boolean(args[0]))
        with db_hlapi(message.guild.id) as db:
            db.add_config("usertrust-enabled", str(int(gate)))
            if kwargs["verbose"]: await message.channel.send(f"Set usertrust enabled to {bool(gate)}")
    else:
        with db_hlapi(message.guild.id) as db:
            gate = bool(int(db.grab_config("usertrust-enabled") or "0"))
        await message.channel.send(f"Usertrust enabled is {bool(gate)}")


category_info = {'name': 'usertrust', 'pretty_name': 'User Trust', 'description': 'Commands to configure the user trust system'}

commands = {
    'usertrust-role': {
        'pretty_name': 'usertrust-role <role>',
        'description': 'Set the trusted role to give',
        'permission': 'administrator',
        'cache': 'regenerate',
        'execute': usertrust_role
        },
    'usertrust-count':
        {
            'pretty_name': 'usertrust-count <int>',
            'description': 'Set amount of messages before a user is given the trusted role',
            'permission': 'administrator',
            'cache': 'regenerate',
            'execute': usertrust_count
            },
    'usertrust-enabled':
        {
            'pretty_name': 'usertrust-enabled <bool>',
            'description': 'Sets whether usertrust is enabled or not',
            'permission': 'administrator',
            'cache': 'regenerate',
            'execute': set_usertrust_use
            },
    }

version_info: str = "ut-1.0.0"
