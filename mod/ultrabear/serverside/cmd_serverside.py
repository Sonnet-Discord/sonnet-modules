# ServerSide packet sender for sonnet
# Ultrabear 2021

# ServerSide provides an api for client users to programmatically parse commands and information on the sonnet instance
# This allows for tighter integration with clients that chose to use that data and provide a better end user experience

import importlib

import discord
import json
import io
import time

import lib_parsers

importlib.reload(lib_parsers)
import lib_sonnetcommands

importlib.reload(lib_sonnetcommands)

from lib_parsers import parse_permissions
from lib_sonnetcommands import SonnetCommand, CommandCtx

from typing import List, Dict, TypedDict


# These TypedDict's are excessive but serve to build a solid base of what each type requires and its layout in a python parsable way
# The true documentation should be consulted for making an implementation in a different language, but these can act as predefined constants for other python implementations
class BaseCommandMapT(TypedDict):
    pretty_name: str
    description: str


class SSPermT(TypedDict):
    name: str
    hasperm: bool


class CommandMapT(BaseCommandMapT, total=False):
    category: str
    permission: SSPermT
    wants: List[str]


class BaseMapT(TypedDict):
    commands: Dict[str, CommandMapT]
    prefixes: List[str]
    bot: str
    guild: str
    user: str


class CategoryT(TypedDict):
    description: str


class ServerSidePacketT(BaseMapT, total=False):
    aliases: Dict[str, str]
    categories: Dict[str, CategoryT]


# Serve commands will implement a data describing hashmap in json format
# The first 16 bytes is the format and version identifier, these are in ascii
# This spec conforms to the 'ServerCommands01' header, the version number is defined as a hexadecimal 2 digit number where 0 is invalid, making 255 versions possible
#
# optional datums are suffixed with OPTIONAL
# 'v': T means that some key value v should be of json type T
# [T] represents a list of a given type T
# v(T) represents a subset of T where only specified variants are defined under section v (this can be defined as an enum)
#
# base hashmap (begin after header ends):
# {
#     'commands':{}, command hashmap, defined below
#     'aliases': {}, alias hashmap, defined below, OPTIONAL
#     'categories': {}, category hashmap, defined below, OPTIONAL
#     'prefixes': [str], a list of prefixes the bot takes, can be one element
#     'bot': str, the bots id, can be used to identify the calling bot
#     'guild': str, the guild id the packet is designed for, this alleviates packet misdirection
#     'user': str, the user id the packet is designed for, this alleviates packet misdirection
# }
# bot guild and user are all represented as str, this is due to discords oversized ids that will exceed 64 bits in the future
# this allows us to maintain cleaner compatibility with languages that do not have native big numbers
#
# The command api serve commands will implement:
# 'command': {
#     'pretty_name': str, the name displayed in docs
#     'description': str, command description
#     'category': str, command category, this is OPTIONAL
#     'permission': {"name": str, "hasperm": bool}, permission name and if you have that perm, this is OPTIONAL
#     'wants': [ArgType(str)], the arguments the command wants, types are defined below, this is OPTIONAL
# }
#
# IMPLEMENTATION FOR ALIAS MAP:
# {'alias': 'command'}
#
# Category hashmap (OPTIONAL)
# 'category': {
#     'description': str, category description
# }
#
#
# ArgType(str): a input type a command can take
# valid specifiers (encoded in string format):
# - str, int, float, bool : base types
# - member, user, role, text-channel, voice-channel, guild, emoji : discord specific numeric types that can have discords decorators
# - message : a message url or channel_id-message_id configuration
# - channel : generic for channel, can be any of TextChannel, StageChannel, VoiceChannel etc
# note: member should be treated as a subset of user
# note: bool is defined by JSON's bool syntax of "true" or "false"
#
async def serve_commands(message: discord.Message, args: List[str], client: discord.Client, ctx: CommandCtx) -> int:
    if not message.guild:
        return 1

    start = time.monotonic_ns()

    prefix: str = ctx.conf_cache["prefix"]

    returner: ServerSidePacketT = {
        "prefixes": [prefix],
        "bot": str(client.user.id),
        "guild": str(message.guild.id),
        "user": str(message.author.id),
        "commands": {},
        "categories": {},
        "aliases": {},
        }

    for mod in ctx.cmds:

        returner["categories"][mod.category_info["name"]] = {"description": mod.category_info["description"]}

        for i in mod.commands:

            try:
                al = ctx.cmds_dict[i]["alias"]

                returner["aliases"][i] = al

            except KeyError:

                command = SonnetCommand(ctx.cmds_dict[i])
                perm = command.permission

                returner["commands"][i] = {
                    "pretty_name": command.pretty_name,
                    "description": command.description,
                    "category": mod.category_info["name"],
                    "permission": {
                        "name": perm if isinstance(perm, str) else perm[0],
                        "hasperm": await parse_permissions(message, ctx.conf_cache, perm, verbose=False)
                        },
                    }

                try:
                    wants = command["wants"]
                    returner["commands"][i]["wants"] = wants
                except KeyError:
                    pass

    fdata = io.BytesIO(b"ServerCommands01" + json.dumps(returner).encode("utf8"))

    fp = discord.File(fdata, filename=f"{message.author.id}.cmds")

    end = time.monotonic_ns()

    await message.channel.send(f"ServerSide packet for {message.author.mention} parsed in {((end-start)/1000/1000):.1f}ms", files=[fp])

    return 0


category_info = {'name': 'serverside', 'pretty_name': 'ServerSide', 'description': 'Tools to send client parsable packets to improve integration of bot commands'}

commands = {
    "serverside-commands": {
        'pretty_name': 'serverside-commands',
        'description': 'Grabs list of commands, prefix, and docs for client side parsing, user specific.',
        'execute': serve_commands
        },
    }

version_info = "ss-1.0.0"
