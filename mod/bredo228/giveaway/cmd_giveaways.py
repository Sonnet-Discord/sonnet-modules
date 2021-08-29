# cmd_giveaways.py
# Command module for giveaways
# Created by bredo228, 2021-07-08

# this module isn't great but it should work

import discord, random

from typing import Any, List

async def gw_from_role_id(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:

    # attempt to get role
    try:
        role = message.guild.get_role(int(args[0].strip("<@!&>")))
    except ValueError:
        await message.channel.send("Error. Invalid role")
        return
    except IndexError:
        await message.channel.send("Error. Please provide a role")
        return

    if role == None: # for some reason this needs to happen because you won't get an error on the previous try except if it's just a random int
        await message.channel.send("Error. Invalid role")
        return

    # sorta shitty way to change the number of winners
    try:
        numWinners = int(args[1])
    except IndexError:
        numWinners = 1
    except ValueError:
        numWinners = 1

    winners = []

    # cap number of winners at amount of people with role
    if numWinners > len(role.members):
        numWinners = len(role.members)

    while len(winners) < numWinners:

        rand = random.randint(0, len(role.members) - 1)
        winner_id = role.members[rand].id

        # add winner if the winner hasn't already won
        if winner_id not in winners:
            winners.append(winner_id)

    msg = ""

    # construct message (badly)
    for i in range(0, len(winners)):
        msg = f"{msg}<@{winners[i]}> "

    # send message
    await message.channel.send(f"Winners: {numWinners}\n\n{msg}")

category_info = {'name': 'giveaways', 'pretty_name': 'Giveaways', 'description': 'Giveaway commands'}

commands = {
    'gw-draw': {
        'pretty_name': 'gw-draw',
        'description': 'Draw users from a role.',
        'permission': 'administrator',
        'cache': 'keep',
        'execute': gw_from_role_id
        },
    }

version_info: str = "1.0.0"
