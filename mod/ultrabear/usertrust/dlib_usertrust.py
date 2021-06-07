# Reactionrole dlib for managing logic
# Ultrabear 2021

import importlib

import discord

import lib_parsers

importlib.reload(lib_parsers)
import lib_loaders

importlib.reload(lib_loaders)
import lib_db_obfuscator

importlib.reload(lib_db_obfuscator)

from lib_parsers import parse_skip_message
from lib_loaders import load_message_config
from lib_db_obfuscator import db_hlapi

from typing import Dict, Any, Union, Set
import lib_lexdpyk_h as lexdpyk

trust_types: Dict[Union[str, int], Any] = {0: "usertrust_enabled", "text": [["usertrust-trusted-role", ""], ["usertrust-message-count", ""], ["usertrust-enabled", "0"]]}


def get_trust_pool(message: discord.Message, kernel_ramfs: lexdpyk.ram_filesystem) -> Set[int]:

    tset: Set[int]

    try:
        tset = kernel_ramfs.read_f(f"{message.guild.id}/usertrust_pool")
    except FileNotFoundError:
        tset = kernel_ramfs.create_f(f"{message.guild.id}/usertrust_pool", f_type=set, f_args=[])

    return tset


async def on_usertrust_message(message: discord.Message, **kargs: Any) -> None:

    if parse_skip_message(kargs["client"], message):
        return

    trusted = get_trust_pool(message, kargs["kernel_ramfs"])

    # Give up if user is already trusted
    if message.author.id in trusted:
        return

    utrust_cache = load_message_config(message.guild.id, kargs["ramfs"], datatypes=trust_types)

    if not bool(int(utrust_cache["usertrust-enabled"])):
        return

    with db_hlapi(message.guild.id) as db:

        db.inject_enum("usertrust", [("userID", str), ("count", int)])

        # Inc counter
        if ucol := db.grab_enum("usertrust", str(message.author.id)):
            count = int(ucol[1]) + 1
        else:
            count = 1

        db.set_enum("usertrust", [str(message.author.id), count])

        if (r := utrust_cache["usertrust-trusted-role"]) and (c := utrust_cache["usertrust-message-count"]):
            if int(c) < count and (drole := message.guild.get_role(int(r))):
                try:
                    await message.author.add_roles(drole)
                    trusted.add(message.author.id)
                except discord.errors.Forbidden:
                    pass


category_info = {'name': 'UserTrust'}

commands = {
    "on-message-0": on_usertrust_message,
    }

version_info = "ut-1.0.1"
