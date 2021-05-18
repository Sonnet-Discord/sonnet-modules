# BOT COMMANDS
# Ultrabear 2021

import os, tempfile, discord

# Import BOT OWNER
from LeXdPyK_conf import BOT_OWNER

if (t := type(BOT_OWNER)) == str or t == int:
    BOT_OWNER = [int(BOT_OWNER)] if BOT_OWNER else []
elif BOT_OWNER:
    BOT_OWNER = [int(i) for i in BOT_OWNER]


class fakersp:
    def __init__(self):
        self.status = "This didint actually fail"
        self.reason = "Its intentional trust me"


async def fatal_lol(message, args, client, **kwargs):
    raise RuntimeError("This command is designed to fatal error")


async def fatal_lol2(message, args, client, **kwargs):
    raise discord.errors.Forbidden(fakersp(), "This command is designed to fatal error")


async def cont_echo(message, args, client, **kwargs):
    await message.channel.send(f"{message.content}\n{args}")


async def bot_update(message, args, client, **kwargs):
    ret = os.system("git pull")
    await message.channel.send(f"returned {ret}")


async def get_commit(message, args, client, **kwargs):
    f = tempfile.NamedTemporaryFile()
    os.system(f"git log -n 1 > {f.name}")
    f.seek(0)

    dat = f.read().decode("utf8")
    f.close()

    await message.channel.send(f"Most Recent Commit:```\n{dat}```")


def isowner(m):
    return m.author.id in BOT_OWNER


category_info = {'name': 'botowner', 'pretty_name': 'OwnerTools', 'description': 'A module providing a commands api for ultrabear to play with lol'}

commands = {
    'exception2': {
        'pretty_name': 'exception2',
        'description': 'Cause an exception',
        'permission': ("bot-owner", isowner),
        'cache': 'keep',
        'execute': fatal_lol2
        },
    'exception': {
        'pretty_name': 'exception',
        'description': 'Cause an exception',
        'permission': ("bot-owner", isowner),
        'cache': 'keep',
        'execute': fatal_lol
        },
    'echoback':
        {
            'pretty_name': 'echoback',
            'description': 'Echo the exact message contents, to be used to debug systems that alter message content',
            'permission': ("bot-owner", isowner),
            'cache': 'keep',
            'execute': cont_echo
            },
    'gitlog': {
        'pretty_name': 'gitlog',
        'description': 'get the git log',
        'permission': ("bot-owner", isowner),
        'cache': 'keep',
        'execute': get_commit
        },
    'update': {
        'pretty_name': 'update',
        'description': 'update the bot',
        'permission': ("bot-owner", isowner),
        'cache': 'keep',
        'execute': bot_update
        },
    }

version_info = "ot-1.0.0"
