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



    with db_hlapi(message.guild.id) as db:
        db.inject_enum("marketrep", marketrep_table)
        db.set_enum("marketrep", [userid, newrep])


category_info: Dict[str, str] = {}

commands: Dict[str, Dict[str, Any]] = {}

version_info: str = "MR-1.0.0"
