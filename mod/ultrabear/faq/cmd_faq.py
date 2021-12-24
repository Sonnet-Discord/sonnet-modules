# Custom FAQ writing module
# Ultrabear 2021

import importlib

import discord

import lib_db_obfuscator

importlib.reload(lib_db_obfuscator)
import lib_parsers

importlib.reload(lib_parsers)

from lib_db_obfuscator import db_hlapi
from lib_parsers import parse_permissions

from typing import Any, Union, List, Tuple, Type, Final, Optional, cast  # pytype: disable=import-error

faq_enum: Final[List[Tuple[str, Type[Union[str, int]]]]] = [("faq_name", str), ("faq_meta", str), ("faq_body", str), ("faq_perm", str)]
faq_name: Final[str] = "faq_data"


def stripargs(content: str, argc: int) -> str:
    """
    Strips space seperated arguments out of a string
    """

    out: List[str] = []

    for idx, val in enumerate(content.split(" ")):
        if idx >= argc:
            # If index is greater than args count then add to output
            out.append(val)
        elif not val:
            # If value is blank increase args count to compensate empty argument
            argc += 1

    return " ".join(out)


async def faq_get(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:
    if not message.guild:
        return 1

    if not args:
        await message.channel.send("No args passed")
        return 1

    with db_hlapi(message.guild.id) as db:
        db.inject_enum(faq_name, faq_enum)

        faq_name_list = cast(List[str], db.list_enum(faq_name))

        if args[0] not in faq_name_list:
            await message.channel.send("ERROR: FAQ requested does not exist")
            return 1

        # We can cast because list_enum had the entry
        # pylint: disable=E0633
        _, _, content, perm = cast(Tuple[str, str, str, str], db.grab_enum(faq_name, args[0]))

        if await parse_permissions(message, kwargs["conf_cache"], perm, verbose=False):
            await message.channel.send(content)
            return 0
        else:
            await message.channel.send("You dont have permission to request this FAQ")
            return 1


async def faq_set(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:
    if not message.guild:
        return 1

    if not args:
        await message.channel.send("ERROR: Missing FAQ name")
        return 1

    if len(args) < 2:
        await message.channel.send("ERROR: Missing FAQ body")
        return 1

    name = args[0]
    body = stripargs(message.content, 2)

    if len(body) > 2000:
        await message.channel.send("ERROR: FAQ body too large")
        return 1
    elif len(name) >= 128:
        await message.channel.send("ERROR: FAQ name too large")
        return 1

    with db_hlapi(message.guild.id) as db:
        db.inject_enum(faq_name, faq_enum)

        db.set_enum(faq_name, [name, "", body, "everyone"])

    if kwargs["verbose"]: await message.channel.send(f"Created new FAQ entry under name {name}")


async def faq_delete(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:
    if not message.guild:
        return 1

    if not args:
        await message.channel.send("ERROR: No args supplied")
        return 1

    with db_hlapi(message.guild.id) as db:
        db.inject_enum(faq_name, faq_enum)

        if not args[0] in db.list_enum(faq_name):
            await message.channel.send("ERROR: No such FAQ entry")
            return 1

        db.delete_enum(faq_name, args[0])

    if kwargs["verbose"]: await message.channel.send("Deleted FAQ entry")


async def faq_list(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:
    if not message.guild:
        return 1

    with db_hlapi(message.guild.id) as db:
        db.inject_enum(faq_name, faq_enum)

        faq_name_list = cast(List[str], db.list_enum(faq_name))

    # TODO(ultrabear) Improve rendering
    if faq_name_list:
        newline = "\n"
        await message.channel.send(f"```\n{newline.join(faq_name_list)}```"[:2000]) # TODO(ultrabear) this is lazy
    else:
        await message.channel.send("This guild has no FAQ entries")


# Override category help to provide faq listings
async def __help_override__(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Optional[Tuple[str, List[Tuple[str, str]]]]:
    if not message.guild:
        return None

    PREFIX = kwargs["conf_cache"]["prefix"]

    clist: List[Tuple[str, str]] = [f"{PREFIX}{v['pretty_name']}", str(v["description"])) for _, v in commands.items()]

    clist.sort(key=lambda s: s[0])

    with db_hlapi(message.guild.id) as db:
        db.inject_enum(faq_name, faq_enum)

        for i in sorted(db.list_enum(faq_name)):
            # We can cast here because list_enum confirmed its existance
            # pylint: disable=E0633
            _, meta, _, _ = cast(Tuple[str, str, str, str], db.grab_enum(faq_name, i))

            clist.append((f"{PREFIX}faq {i}", str(meta if meta else i)), )

    # TODO(ultrabear) Custom description per guild
    return category_info["description"], clist


# TODO(ultrabear) Add description setting per faq entry
# TODO(ultrabear) Add permission setting per faq entry

category_info = {"name": "faq", "pretty_name": "FAQ", "description": "FAQ Module for making guild level custom faq posts"}

commands = {
    "faq": {
        "pretty_name": "faq <name>",
        "description": "Grabs the FAQ entry with the given name",
        "execute": faq_get,
        },
    "faq-set": {
        "pretty_name": "faq-set <name> <content>",
        "description": "Sets a new FAQ entry with the given name",
        "permission": "administrator",
        "execute": faq_set,
        },
    "faq-delete": {
        "pretty_name": "faq-delete <name>",
        "description": "Deletes the FAQ entry with the given name",
        "permission": "administrator",
        "execute": faq_delete,
        },
    "faq-list": {
        "pretty_name": "faq-list",
        "description": "Lists all guild FAQ entries",
        "execute": faq_list,
        },
    }

version_info = "1.0.0-2"
