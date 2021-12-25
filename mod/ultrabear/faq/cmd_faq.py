# Custom FAQ writing module
# Ultrabear 2021

import importlib

import discord

import lib_db_obfuscator

importlib.reload(lib_db_obfuscator)
import lib_parsers

importlib.reload(lib_parsers)
import lib_constants

importlib.reload(lib_constants)

from lib_db_obfuscator import db_hlapi
from lib_parsers import parse_permissions

import lib_constants as constants

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

        maybedata = db.grab_enum(faq_name, args[0])

        if maybedata is None:
            await message.channel.send("ERROR: FAQ requested does not exist")
            return 1

        _, _, content, perm = maybedata  # pylint: disable=E0633

        if await parse_permissions(message, kwargs["conf_cache"], str(perm), verbose=False):
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

    if len(body) > constants.message.content:
        await message.channel.send("ERROR: FAQ body too large")
        return 1
    elif len(name) >= 32:
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
        await message.channel.send(f"```\n{newline.join(faq_name_list)}```"[:2000])  # TODO(ultrabear) this is lazy
    else:
        await message.channel.send("This guild has no FAQ entries")


async def faq_set_description(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:
    if not message.guild:
        return 1

    if not args:
        await message.channel.send("ERROR: Missing FAQ name")
        return 1

    if len(args) < 2:
        await message.channel.send("ERROR: Missing FAQ desc")
        return 1

    name = args[0]
    desc = stripargs(message.content, 2)

    if len(desc) > 256:
        await message.channel.send("ERROR: FAQ description too large")
        return 1

    with db_hlapi(message.guild.id) as db:
        db.inject_enum(faq_name, faq_enum)

        maybefaq = db.grab_enum(faq_name, name)

        if maybefaq is None:
            await message.channel.send("ERROR: FAQ entry does not exist")
            return 1

        _, _, body, perm = maybefaq  # pylint: disable=E0633

        db.set_enum(faq_name, [name, desc, body, perm])

    if kwargs["verbose"]: await message.channel.send(f"Updated description for FAQ entry {name}")


async def faq_set_permission(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:
    if not message.guild:
        return 1

    if not args:
        await message.channel.send("ERROR: Missing FAQ name")
        return 1

    if len(args) < 2:
        await message.channel.send("ERROR: Missing FAQ perm")
        return 1

    name = args[0]
    perm = args[1]

    if perm not in {"everyone", "moderator", "administrator", "owner"}:
        await message.channel.send("ERROR: Perm must be one of [everyone moderator administrator owner]")
        return 1

    with db_hlapi(message.guild.id) as db:
        db.inject_enum(faq_name, faq_enum)

        maybefaq = db.grab_enum(faq_name, name)

        if maybefaq is None:
            await message.channel.send("ERROR: FAQ entry does not exist")
            return 1

        _, desc, body, _ = maybefaq  # pylint: disable=E0633

        db.set_enum(faq_name, [name, desc, body, perm])

    if kwargs["verbose"]: await message.channel.send(f"Updated FAQ permission for entry {name} to `{perm}`")


async def faq_guild_description(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:
    if not message.guild:
        return 1

    if not args:
        await message.channel.send("ERROR: Missing description")
        return 1

    desc = stripargs(message.content, 1)

    if len(desc) > 512:
        await message.channel.send("ERROR: Description too large")
        return 1

    with db_hlapi(message.guild.id) as db:
        db.add_config("faq_description", desc)

    if kwargs["verbose"]: await message.channel.send("Updated description for guild help")


async def clear_faq_description(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:
    if not message.guild:
        return 1

    with db_hlapi(message.guild.id) as db:
        db.delete_config("faq_description")

    if kwargs["verbose"]: await message.channel.send("Deleted FAQ help description")


# Override category help to provide faq listings
async def __help_override__(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Optional[Tuple[str, List[Tuple[str, str]]]]:
    if not message.guild:
        return None

    PREFIX = kwargs["conf_cache"]["prefix"]

    clist: List[Tuple[str, str]] = [(f"{PREFIX}{v['pretty_name']}", str(v["description"])) for _, v in commands.items()]

    clist.sort(key=lambda s: s[0])

    with db_hlapi(message.guild.id) as db:
        db.inject_enum(faq_name, faq_enum)

        for i in sorted(db.list_enum(faq_name)):
            # We can cast here because list_enum confirmed its existance
            # pylint: disable=E0633
            _, meta, _, _ = cast(Tuple[str, str, str, str], db.grab_enum(faq_name, i))

            clist.append((f"{PREFIX}faq {i}", str(meta if meta else i)), )

        faq_description = db.grab_config("faq_description") or category_info["description"]

    # TODO(ultrabear) Custom description per guild
    return faq_description, clist


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
    "faq-set-description":
        {
            "pretty_name": "faq-set-description <name> <description>",
            "description": "Sets an FAQ entries description",
            "permission": "administrator",
            "execute": faq_set_description,
            },
    "faq-set-permission":
        {
            "pretty_name": "faq-set-permission <name> <permission>",
            "description": "Sets an FAQ entries permission level",
            "permission": "administrator",
            "execute": faq_set_permission,
            },
    "faq-delete-guild-description":
        {
            "pretty_name": "faq-delete-guild-description",
            "description": "deletes the helptext description",
            "permission": "administrator",
            "execute": clear_faq_description,
            },
    "faq-set-guild-description":
        {
            "pretty_name": "faq-set-guild-description <description>",
            "description": "Sets the helptext description",
            "permission": "administrator",
            "execute": faq_guild_description,
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

version_info = "1.0.1"
