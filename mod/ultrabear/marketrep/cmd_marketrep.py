# A market rep implementation
# Ultrabear 2021

import importlib

import discord, json

import lib_db_obfuscator

importlib.reload(lib_db_obfuscator)

from lib_db_obfuscator import db_hlapi


from typing import Dict, List, Any, Optional, Tuple


marketrep_table: List[Tuple[str, Any]]  = [("userID", str), ("reputation", int)]


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
        member = message.guild.get_member(int(args[0].strip("<@&>")))
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

    with db_hlapi(message.guild.id) as db:
        table_name: str = "marketrep"
        db.inject_enum(table_name, marketrep_table)

        grep = db.grab_enum(table_name, str(member.id))

        if grep:
            newrep = grep[1] + 1
        else:
            newrep = 1

        db.set_enum(table_name, [str(member.id), newrep])


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
}

version_info: str = "MR-1.0.0"
