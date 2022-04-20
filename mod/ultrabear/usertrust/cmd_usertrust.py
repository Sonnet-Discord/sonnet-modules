# UserTrust (for trolling nachog)
# Ultrabear 2021

import importlib

import discord

import lib_db_obfuscator

importlib.reload(lib_db_obfuscator)
import lib_parsers

importlib.reload(lib_parsers)
import lib_sonnetcommands

importlib.reload(lib_sonnetcommands)

from lib_parsers import parse_role, parse_boolean, parse_user_member_noexcept
from lib_db_obfuscator import db_hlapi
from lib_sonnetcommands import CommandCtx

from typing import Final, List, Set
import lib_lexdpyk_h as lexdpyk


def get_trust_pool(guild: discord.Guild, kernel_ramfs: lexdpyk.ram_filesystem) -> Set[int]:

    tset: Set[int]

    try:
        tset = kernel_ramfs.read_f(f"{guild.id}/usertrust_pool")
    except FileNotFoundError:
        tset = kernel_ramfs.create_f(f"{guild.id}/usertrust_pool", f_type=set, f_args=[])

    return tset


async def usertrust_role(message: discord.Message, args: List[str], client: discord.Client, ctx: CommandCtx) -> int:

    return await parse_role(message, args, "usertrust-trusted-role", verbose=ctx.verbose)


async def usertrust_count(message: discord.Message, args: List[str], client: discord.Client, ctx: CommandCtx) -> int:
    if not message.guild:
        return 1

    COUNT_CONFIG: Final = "usertrust-message-count"

    try:
        count = int(args[0])
    except ValueError:
        raise lib_sonnetcommands.CommandError("ERROR: No int is invalid")
    except IndexError:

        with db_hlapi(message.guild.id) as db:
            if (v := db.grab_config(COUNT_CONFIG)) is not None:
                await message.channel.send(f"Usertrust count is set to {v} messages")
            else:
                await message.channel.send("Usertrust count is unset")

        return 0

    if 2**32 < count or count < 10:
        raise lib_sonnetcommands.CommandError(f"ERROR: Count cannot exceed range 10-{2**32}")

    with db_hlapi(message.guild.id) as db:
        db.add_config(COUNT_CONFIG, str(count))

    await message.channel.send(f"Updated usertrust message count to {count}")
    return 0


async def set_usertrust_use(message: discord.Message, args: List[str], client: discord.Client, ctx: CommandCtx) -> int:
    if not message.guild:
        return 1

    if args:
        gate = bool(parse_boolean(args[0]))
        with db_hlapi(message.guild.id) as db:
            db.add_config("usertrust-enabled", str(int(gate)))
            if ctx.verbose: await message.channel.send(f"Set usertrust enabled to {bool(gate)}")
    else:
        with db_hlapi(message.guild.id) as db:
            gate = bool(int(db.grab_config("usertrust-enabled") or "0"))
        await message.channel.send(f"Usertrust enabled is {bool(gate)}")

    return 0


async def get_users_trust(message: discord.Message, args: List[str], client: discord.Client, ctx: CommandCtx) -> int:
    if not message.guild:
        return 1

    user, _ = await parse_user_member_noexcept(message, args, client, default_self=True)

    t_count: int

    with db_hlapi(message.guild.id) as db:
        db.inject_enum("usertrust", [("userID", str), ("count", int)])

        trust = db.grab_enum("usertrust", str(user.id))

        if trust and isinstance(trust[1], int):
            t_count = trust[1]
        else:
            t_count = 0

    trusted = get_trust_pool(message.guild, ctx.kernel_ramfs)

    fmt = f"```\nUser: {user}\nMcount: {t_count}\nHas Trusted Role: {user.id in trusted}\n```"

    await message.channel.send(fmt)
    return 0


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
    'usertrust-checkuser': {
        'pretty_name': 'usertrust-checkuser <user>',
        'description': 'Checks a users trust status',
        'permission': 'moderator',
        'cache': 'keep',
        'execute': get_users_trust
        },
    }

version_info: str = "ut-1.0.3"
