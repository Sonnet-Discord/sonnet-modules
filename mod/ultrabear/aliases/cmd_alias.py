# Alias processor
# Ultrabear 2022

import importlib
from dataclasses import dataclass
import copy as pycopy
import discord
import shlex
import io
import math

import lib_sonnetcommands

importlib.reload(lib_sonnetcommands)
import lib_db_obfuscator

importlib.reload(lib_db_obfuscator)
import lib_parsers

importlib.reload(lib_parsers)
import lib_lexdpyk_h

importlib.reload(lib_lexdpyk_h)
import lib_tparse

importlib.reload(lib_tparse)

from lib_db_obfuscator import db_hlapi
from lib_sonnetcommands import CommandCtx, SonnetCommand
from lib_parsers import parse_permissions
from lib_tparse import Parser

import lib_lexdpyk_h as lexdpyk

from typing import Collection, List, Tuple, Union, Type, Final, Any, TypeVar, Callable

# simlist is a simulated list with a max size of 500 items, its used to assert arg lookups
simlist = 500

# dbenums datatype for Alias table
AliasDBT: Final[Tuple[str, List[Tuple[str, Union[Type[str], Type[int]]]]]] = ("aliases", [('aliasName', str), ('aliasValue', str)])


@dataclass
class Slice:
    start: int
    stop: int


class Index(int):
    ...


class InvalidParse(Exception):
    ...


class NotAToken(Exception):
    ...


# parses arglookup index given a list length
def parse_arglookupidx(val: str, listlen: int) -> Union[Slice, Index]:

    if val == "$":
        return Slice(0, listlen)

    elif val.startswith("$[") and val.endswith("]"):
        idxorslice = val.lstrip("$[").rstrip("]")

        if idxorslice.count(':') == 1:
            pre, post = idxorslice.split(':')
            if not pre: pre = "0"
            if not post: post = str(listlen)

            try:
                return Slice(int(pre, 0), int(post, 0))
            except ValueError:
                raise InvalidParse("ERROR: Tried to parse int value but failed")

        else:
            try:
                v: Final = int(idxorslice, 0)
                if v >= listlen or v < -1 * listlen:
                    raise InvalidParse(f"ERROR: Lookup idx of {v} is larger than max list size of {listlen}")
                return Index(v)

            except ValueError:
                raise InvalidParse("ERROR: Tried to parse int value but failed")
    else:
        raise NotAToken("ERROR: Could not parse index from index lookup")


def positive_idx(idx: int, length: int) -> int:
    return length + idx if idx < 0 else idx


def assert_arglookup(val: str) -> Collection[int]:

    typ: Final = parse_arglookupidx(val, simlist)

    if isinstance(typ, Slice):
        start: Final = positive_idx(typ.start, simlist)
        stop: Final = positive_idx(typ.stop, simlist)
        return range(start, stop)

    else:
        idx: Final = positive_idx(int(typ), simlist)
        return {idx}


def pushassert(lis: List[Collection[int]], new: Collection[int]) -> None:
    for i in lis:
        for n in new:
            if n in i:
                raise lib_sonnetcommands.CommandError("ERROR: Consumed argument attempted to be consumed again")
    lis.append(new)


async def new_alias(message: discord.Message, args: List[str], client: discord.Client, ctx: CommandCtx) -> int:
    if not message.guild:
        return 1

    if len(args) >= 2:
        alias_name: Final = args[0]
        alias_args: Final = args[1:]

        if len(alias_name) > 128:
            raise lib_sonnetcommands.CommandError("ERROR: length of alias name exceeds 128 chars")

        arglist: List[Collection[int]] = []

        for idx, v in enumerate(alias_args):

            # Assert consuming
            try:
                ncapture = assert_arglookup(v)
                pushassert(arglist, ncapture)
            except InvalidParse as ip:
                raise lib_sonnetcommands.CommandError(ip)
            except NotAToken:
                if idx == 0 and v == "a":
                    raise lib_sonnetcommands.CommandError("ERROR: Cannot call alias from alias command")
                elif idx == 0 and v not in ctx.cmds_dict:
                    raise lib_sonnetcommands.CommandError("ERROR: No such command found after processing alias")

        with db_hlapi(message.guild.id) as db:
            with db.inject_enum_context(*AliasDBT) as alias_db:
                alias_db.set([alias_name, " ".join(alias_args)])

        if ctx.verbose: await message.channel.send(f"New alias with name {alias_name} has been created")
        return 0

    else:
        raise lib_sonnetcommands.CommandError("ERROR: not enough args supplied")


# Copied directly from cmd_scripting.py -> make into lib/merge alias into scripting later
def do_cache_sweep(cache: str, ramfs: lexdpyk.ram_filesystem, guild: discord.Guild) -> None:

    if cache in ["purge", "regenerate"]:
        for i in ["caches", "regex"]:
            try:
                ramfs.rmdir(f"{guild.id}/{i}")
            except FileNotFoundError:
                pass

    elif cache.startswith("direct:"):
        for i in cache[len('direct:'):].split(";"):
            try:
                if i.startswith("(d)"):
                    ramfs.rmdir(f"{guild.id}/{i[3:]}")
                elif i.startswith("(f)"):
                    ramfs.remove_f(f"{guild.id}/{i[3:]}")
                else:
                    raise RuntimeError("Cache directive is invalid")
            except FileNotFoundError:
                pass


async def call_alias(message: discord.Message, args: List[str], client: discord.Client, ctx: CommandCtx) -> Any:
    if not message.guild:
        return 1

    if not ctx.verbose:
        raise lib_sonnetcommands.CommandError("ERROR: Cannot call alias as a subcommand")
    
    try:
        spargs = shlex.split(" ".join(args[1:]))
    except ValueError:
        raise lib_sonnetcommands.CommandError("ERROR: Shlex failed to parse arguments, unclosed parenthesis/backslashes")

    if len(spargs) > simlist:
        raise lib_sonnetcommands.CommandError(f"ERROR: More than {simlist} args passed (hard limit)")

    # Add quotations back to arguments so ['reason text', 'arg2'] becomes ['"reason text"', 'arg2']
    spargs = [f'"{i}"' if ' ' in i else i for i in spargs]

    # flow: get alias from db -> do arg replacements (bounds check) -> check perms -> check command is not alias command

    if args:
        alias_name = args[0]

        with db_hlapi(message.guild.id) as db:
            with db.inject_enum_context(*AliasDBT) as alias_db:
                cont = alias_db.grab(alias_name)

                if cont is None:
                    raise lib_sonnetcommands.CommandError("ERROR: No such alias exists")

                data = cont[1]
                assert isinstance(data, str)

        newbuild: List[str] = []

        for i in data.split(" "):
            try:
                v = parse_arglookupidx(i, len(spargs))

                if isinstance(v, Slice):
                    newbuild.extend(spargs[v.start:v.stop])
                else:
                    newbuild.append(spargs[v])

            except InvalidParse as ip:
                raise lib_sonnetcommands.CommandError(ip)
            except NotAToken:
                newbuild.append(i)

        if newbuild:
            try:
                cname = newbuild[0]
                if 'alias' in ctx.cmds_dict[cname]:
                    cname = ctx.cmds_dict[cname]['alias']
                cmd = SonnetCommand(ctx.cmds_dict[cname])
            except KeyError:
                raise lib_sonnetcommands.CommandError("ERROR: The command requested does not exist")
        else:
            raise lib_sonnetcommands.CommandError("ERROR: No command left after processing alias replacements")

        if cmd.execute_ctx == call_alias:
            raise lib_sonnetcommands.CommandError("ERROR: Attempted to call alias from alias command")

        if not await parse_permissions(message, ctx.conf_cache, cmd.permission):
            return 1

        # We can finally run the command now
        oldcont = message.content
        try:

            message.content = f'{ctx.conf_cache["prefix"]}{" ".join(newbuild)}'
            newctx = pycopy.copy(ctx)
            return await cmd.execute_ctx(message, newbuild[1:], client, newctx)

        finally:
            message.content = oldcont
            do_cache_sweep(cmd.cache, ctx.ramfs, message.guild)


async def inspect_alias(message: discord.Message, args: List[str], client: discord.Client, ctx: CommandCtx) -> int:
    if not message.guild:
        return 1

    if args:
        with db_hlapi(message.guild.id) as db:
            with db.inject_enum_context(*AliasDBT) as alias_db:
                cont: Final = alias_db.grab(args[0])

                if cont is None:
                    raise lib_sonnetcommands.CommandError("ERROR: Alias does not exist")
                else:
                    await message.channel.send(f"Alias: {cont[0]}```{cont[1]}```")
                    return 0

    else:
        raise lib_sonnetcommands.CommandError("ERROR: No alias passed")


T = TypeVar("T")


def notneg(v: int) -> int:
    if v < 0:
        raise ValueError("Value is below zero")
    return v


# low effort pager does what it says on the tin, prelude to high effort pager
def low_effort_pager_noexcept(v: List[T], fmt: Callable[[T], str], args: List[str], lim: int) -> Tuple[str, int, int]:

    p: Final = Parser("LEP")
    pageP: Final = p.add_arg(["-p", "--page"], lambda s: notneg(int(s) - 1))
    per_pageP: Final = p.add_arg(["-i", "--items-perpage"], int)

    try:
        p.parse(args, stderr=io.StringIO(), exit_on_fail=False, lazy=True)
    except lib_tparse.ParseFailureError:
        raise lib_sonnetcommands.CommandError("ERROR: Failed to parse paging/items per page")

    page: Final = pageP.get(0)
    per_page: Final = per_pageP.get(10)

    if not (1 <= per_page <= 20):
        raise lib_sonnetcommands.CommandError("ERROR: Per page outside range 1-20")

    plen = math.ceil(len(v) / per_page)

    if not (0 <= page < plen):
        raise lib_sonnetcommands.CommandError("ERROR: Page requested is out of range")

    max_size = lim // per_page

    return '\n'.join(fmt(i)[:max_size] for i in v[page * per_page:page * per_page + per_page]), page, plen


async def list_alias(message: discord.Message, args: List[str], client: discord.Client, ctx: CommandCtx) -> int:
    if not message.guild:
        return 1

    with db_hlapi(message.guild.id) as db:
        with db.inject_enum_context(*AliasDBT) as alias_db:
            names: Final = alias_db.list()
            lis = list(filter(None, (alias_db.grab(i) for i in names)))

    if not lis:
        await message.channel.send("No aliases in database")
        return 0

    lis.sort(key=lambda i: i[0])

    pagedata, page, totalpages = low_effort_pager_noexcept(lis, lambda s: f"{s[0]} : {s[1]}", args, 1900)

    await message.channel.send(f"Aliases page {page+1} / {totalpages} ({len(lis)} total)```{pagedata}```")
    return 0


async def rm_alias(message: discord.Message, args: List[str], client: discord.Client, ctx: CommandCtx) -> int:
    if not message.guild:
        return 1

    if not args:
        raise lib_sonnetcommands.CommandError("ERROR: No alias name passed")

    with db_hlapi(message.guild.id) as db:
        with db.inject_enum_context(*AliasDBT) as alias_db:
            if alias_db.grab(args[0]) is not None:
                alias_db.delete(args[0])
            else:
                raise lib_sonnetcommands.CommandError("ERROR: Alias does not exist")

    if ctx.verbose: await message.channel.send(f"Deleted alias with name {args[0]}")
    return 0


# TODO(ultrabear): add help override?

category_info: Final = {'name': "alias", "pretty_name": "Aliases", "description": "A userland command alias creation library"}

commands: Final = {
    'new-alias':
        {
            'pretty_name':
                'new-alias <name> [args]',
            'description':
                'Create a new alias with given args, see `help new-alias` for details on [args].',
            'rich_description':
                'The first argument to args is the command to call, and further args are passed verbatim, use $[idx] syntax to consume arguments from the alias call, where idx is a standard array slice as seen in python (supports slicing and negative indexing). Arguments are not available again once consumed once (`new-alias bam $[0] $[0]` is invalid), this is to avoid duplication exploits.',
            'permission':
                'administrator',
            'execute':
                new_alias,
            },
    'a': {
        'alias': 'alias'
        },
    'alias': {
        'pretty_name': 'alias <name> [args]',
        'description': 'Process an alias and run it',
        'execute': call_alias,
        },
    'list-aliases': {
        'pretty_name': 'list-aliases [-p PAGE] [-i PER_PAGE]',
        'description': 'List aliases',
        'execute': list_alias,
        },
    'rm-alias': {
        'pretty_name': 'rm-alias <name>',
        'description': 'Removes an alias with the given name',
        'permission': 'administrator',
        'execute': rm_alias,
        },
    'inspect-alias': {
        'pretty_name': 'inspect-alias <alias>',
        'description': 'Returns an aliases content',
        'execute': inspect_alias,
        }
    }

version_info: Final = "al-1.0.4"
