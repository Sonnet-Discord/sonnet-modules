# Role based giveaway system
# Ultrabear 2021

import importlib

import random
import time

import discord

import lib_constants

importlib.reload(lib_constants)

import lib_constants as constants

from typing import List, Any, Set


async def giveaway_role(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:
    if not message.guild:
        return 1

    tstart = time.monotonic()

    try:
        roleid = int(args[0].strip("<@&>"))
    except ValueError:
        await message.channel.send(constants.sonnet.error_role.invalid)
        return 1
    except IndexError:
        await message.channel.send(constants.sonnet.error_role.none)
        return 1

    if not (role := message.guild.get_role(roleid)):
        await message.channel.send(constants.sonnet.error_role.invalid)
        return 1

    try:
        winner_count = int(args[1])
    except IndexError:
        winner_count = 1
    except ValueError:
        await message.channel.send("ERROR: Winner count is not valid int")
        return 1

    if winner_count > 20:
        await message.channel.send("ERROR: Cannot pick more than 20 winners")
        return 1

    members = list(role.members)

    if winner_count > len(members):
        await message.channel.send("ERROR: More winners specified than members that have the role")
        return 1

    winners: Set[discord.Member] = set()

    for _ in range(winner_count):
        winners.add(members.pop(random.randint(0, len(members) - 1)))

    tend = time.monotonic()

    await message.channel.send(f"Winners: {', '.join(i.mention for i in winners)}\nComputed in: {(tend-tstart)*1000:.1f}ms", allowed_mentions=discord.AllowedMentions.none())


category_info = {"name": "giveaway", "pretty_name": "Giveaways", "description": "Giveaway by role module"}

commands = {
    'giveaway-draw': {
        'pretty_name': 'giveaway-draw <role> [winner count]',
        'description': 'Draw winners of a giveaway',
        'permission': 'administrator',
        'cache': 'keep',
        'execute': giveaway_role
        }
    }

version_info = "1.0.0"
