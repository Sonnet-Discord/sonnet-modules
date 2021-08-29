# Command to disable threading permissions on roles
# Ultrabear 2021

import discord

from typing import Any, List


# IMPORTANT Any permissions added after thread perms will also be disabled by this
async def disable_role_perms(message: discord.Message, args: List[str], client: discord.Client, **kwargs: Any) -> Any:
    if not message.guild:
        return 1


    # Perms of Public threads and Private threads
    remove = 0b11 << 35

    # This is the value discords dev portal perm builder gives, make sure it is the same
    assert remove == 103079215104

    fullmask = ~(1<<64) ^ remove

    failure: List[discord.Role] = []

    for r in await message.guild.fetch_roles():

        perms = r.permissions

        perms.value = fullmask & perms.value

        try:
            await r.edit(permissions=perms)
        except discord.errors.Forbidden:
            failure.append(r)

    if failure:
        await message.channel.send(f"Missed roles: {', '.join([i.mention for i in failure])}", allowed_mentions=discord.AllowedMentions.none())
    else:
        await message.channel.send("Updated all roles")


category_info = {'name': 'disablethreads', 'pretty_name': 'Thread Disabling', 'description': 'Commands to disable thread perms on roles'}

commands = {
    'disablethreads-roles':
        {
            'pretty_name': 'disablethreads-roles',
            'description': 'Disables all role perms the bot can that are thread perms',
            'permission': 'administrator',
            'cache': 'keep',
            'execute': disable_role_perms
            },
    }

version_info: str = "dt-1.0.0"
