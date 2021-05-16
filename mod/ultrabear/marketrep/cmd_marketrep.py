# A market rep implementation
# Ultrabear 2021

import importlib

import discord, json

import lib_db_obfuscator

importlib.reload(lib_db_obfuscator)

from lib_db_obfuscator import db_hlapi

from typing import Dict, List, Any, Optional, Tuple

marketrep_table: List[Tuple[str, Any]] = [("userID", str), ("reputation", int)]


# I am going to write a comment here specifically
# To spite anyone that reads the name of this
# Exception and does not understand its function
# If you are this person please pursue a career in not CS
# Because you will bobby tables everything
# Like the absolute idiot you are
class ItsBelowZero(Exception):
    pass


async def grab_member(message: discord.Message, args: List[str]) -> Optional[discord.Member]:

    try:
        member = message.guild.get_member(int(args[0].strip("<@!>")))
    except IndexError:
        await message.channel.send("ERROR: Not enough args")
        return None
    except ValueError:
        await message.channel.send("ERROR: Input not valid int")
        return None

    if member:
        return member
    else:
        await message.channel.send("ERROR: User not a member")
        return None


async def add_mr_role(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:

    if len(args) < 2:
        await message.channel.send("ERROR: Not enough args")
        return 1

    try:
        rep_number: int = int(args[0])
        if rep_number < 0: raise ItsBelowZero
    except (ValueError, ItsBelowZero):
        await message.channel.send("ERROR: Please enter a valid unsigned integer for the market rep number")
        return 1

    try:
        role: Optional[discord.Role] = message.guild.get_role(int(args[1].strip("<@&>")))
    except ValueError:
        await message.channel.send("ERROR: Role is not valid int")
        return 1

    if not role:
        await message.channel.send("ERROR: Role does not exist")
        return 1

    with db_hlapi(message.guild.id) as db:
        rolesdata: Dict[str, int] = json.loads(db.grab_config("mr-roles") or "{}")

        rolesdata[str(rep_number)] = role.id

        db.add_config("mr-roles", json.dumps(rolesdata))

    if kwargs["verbose"]: await message.channel.send(f"Added {role.mention} to index {rep_number} of market rep data", allowed_mentions=discord.AllowedMentions.none())


async def increment_user(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:

    if not (member := await grab_member(message, args)):
        return 1

    newrep: int
    rdb: Dict[str, int]

    with db_hlapi(message.guild.id) as db:
        table_name: str = "marketrep"
        db.inject_enum(table_name, marketrep_table)

        grep = db.grab_enum(table_name, str(member.id))

        if grep:
            newrep = grep[1] + 1
        else:
            newrep = 1

        rdb = json.loads(db.grab_config("mr-roles") or "{}")

        db.set_enum(table_name, [str(member.id), newrep])

    etypes: List[str] = []

    if (str(newrep) in rdb) and (r := message.guild.get_role(rdb[str(newrep)])):
        try:
            await member.add_roles(r)
        except discord.errors.Forbidden:
            etypes.append("Could not add new rep role (403)")
    else:
        etypes.append("Could not add new rep role (404)")

    if (str(newrep - 1) in rdb) and (r := message.guild.get_role(rdb[str(newrep - 1)])):
        try:
            await member.remove_roles(r)
        except discord.errors.Forbidden:
            etypes.append("Could not remove old rep role (403)")
    else:
        etypes.append("Could not remove old rep role (404)")

    await message.channel.send(f"Updated {member.mention}'s market rep to {newrep} in db" + bool(etypes) * f"\nErrors encountered: {', '.join(etypes)}")


async def decrement_user(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:

    if not (member := await grab_member(message, args)):
        return 1

    newrep: int
    rdb: Dict[str, int]

    with db_hlapi(message.guild.id) as db:
        table_name: str = "marketrep"
        db.inject_enum(table_name, marketrep_table)

        grep = db.grab_enum(table_name, str(member.id))

        if grep and grep[1] - 1 >= 0:
            newrep = grep[1] - 1
        else:
            await message.channel.send("ERROR: Users marketrep cannot be below 0")
            return 1

        db.set_enum(table_name, [str(member.id), newrep])

        rdb = json.loads(db.grab_config("mr-roles") or "{}")

    etypes: List[str] = []

    if newrep != 0:
        if (str(newrep) in rdb) and (r := message.guild.get_role(rdb[str(newrep)])):
            try:
                await member.add_roles(r)
            except discord.errors.Forbidden:
                etypes.append("Could not add new rep role (403)")
    else:
        etypes.append("Could not add new rep role (404)")

    if (str(newrep + 1) in rdb) and (r := message.guild.get_role(rdb[str(newrep + 1)])):
        try:
            await member.remove_roles(r)
        except discord.errors.Forbidden:
            etypes.append("Could not remove old rep role (403)")
    else:
        etypes.append("Could not remove old rep role (404)")

    await message.channel.send(f"Updated {member.mention}'s market rep to {newrep} in db" + bool(etypes) * f"\nErrors encountered: {', '.join(etypes)}")


category_info: Dict[str, str] = {
    "name": "marketrep",
    "pretty_name": "MarketRep",
    "description": "Market Reputation control commands",
    }

commands: Dict[str, Dict[str, Any]] = {
    "mr-addrole": {
        "pretty_name": "mr-addrole <id> <role>",
        "description": "add a role to the marketrep rolebase",
        "permission": "administrator",
        "cache": "keep",
        "execute": add_mr_role,
        },
    "mr-increp": {
        "pretty_name": "mr-increp <user>",
        "description": "increment a users market rep",
        "permission": "moderator",
        "cache": "keep",
        "execute": increment_user,
        },
    "mr-decrep": {
        "pretty_name": "mr-decrep <user>",
        "description": "decrement a users market rep",
        "permission": "moderator",
        "cache": "keep",
        "execute": decrement_user,
        },
    }

version_info: str = "MR-1.0.0"
