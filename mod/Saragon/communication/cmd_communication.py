# communications
# Saragon 2021

import importlib

import discord

import lib_parsers
importlib.reload(lib_parsers)

from lib_parsers import parse_channel_message


def getMessage(cmdlen, message):
    '''
    Takes in length of command defined by num of args + base command and original message and outputs the message after the arguments defined
    '''
    output = []
    for a, i in enumerate(message.content.split(" ")):
        if i or a > cmdlen:
            if a > cmdlen:
                output.append(i)
        else:
            cmdlen += 1
    return (" ".join(output))


async def edit(message, args, client, **kwargs):

    try:
        discord_message, nargs = await parse_channel_message(message, args, client)
    except lib_parsers.errors.message_parse_failure:
        return

    await discord_message.edit(content=getMessage(nargs, message))


async def write(message, args, client, **kwargs):

    log_channel = args[0].strip("<#>")

    # taken from cmd_moderation
    # yes this is shared code, but I cba to make it work that way
    try:
        log_channel = int(log_channel)
    except ValueError:
        await message.channel.send("Channel is not a valid channel")
        return

    discord_channel = client.get_channel(log_channel)
    if not discord_channel:
        await message.channel.send("Channel is not a valid channel")
        return

    if discord_channel.guild.id != message.channel.guild.id:
        await message.channel.send("Channel is not in guild")
        return

    await discord_channel.send(getMessage(1, message))


category_info = {'name': 'communication', 'pretty_name': 'Communication', 'description': 'Communication commands.'}

commands = {
    'write': {
        'pretty_name': 'write <channel> <mesage>',
        'description': 'Send a message to a specified channel',
        'permission': 'moderator',
        'cache': 'keep',
        'execute': write
        },
    'edit': {
        'pretty_name': 'edit <channel> <message_id> <mesage>',
        'description': 'Edit a message sent by the bot',
        'permission': 'moderator',
        'cache': 'keep',
        'execute': edit
        },
    }

version_info = "Communicatons-1.2.0"
