import requests     # For The Cat API
import json         # For The Cat API
import aiohttp      # For creating emojis
from datetime import datetime # For uptime
import asyncio      # For music cog and stan

from env import TOKEN, PREFIX
from other import (daily_stan, greeting_required, greet, echo_uwu,
        is_rainbow, be_rainbow)

import discord
from discord.ext import commands
intents = discord.Intents.all()
intents.members = True
intents.presences = True
intents.typing = True
intents.reactions = True
client = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# https://stackoverflow.com/questions/62351392/load-extension-in-python-discordpy#62351528
async def main():
    await client.load_extension("music")

if __name__ == "__main__":
    asyncio.run(main())


@client.event
async def on_ready():
    print(f'Logged in as {client.user}!')

    await client.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening,
        name=f'{PREFIX}help'))

    print("\nServers: ")
    for guild in client.guilds:
        print(f"- {guild.name} ({guild.member_count} members)")

    start_time = datetime.now()
    print(f"\nStart time: {start_time}\n")

    client.loop.create_task(daily_stan(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    await client.process_commands(message)

    text = message.content.lower()
    
    if not text or text[0] == PREFIX:
        return

    if greeting_required(text):
        return await greet(message)

    if is_rainbow(text):
        return await be_rainbow(message)

    if text == "yay":
        return await message.channel.send("yay")

    if "uwu" in text or "owo" in text:
        return await echo_uwu(message)

    if text == len(text) * 'a' or text == len(text) * 'A':
        return await message.channel.send(message.content)


@client.command(aliases=['h'])
async def help(ctx):
    embed = discord.Embed(title=f"Qubitz's prefix: `{PREFIX}`",
            description=f"Qubitz is an uwubot and a music bot, with "
            "custom emoji uploading capability, role-finding, and connectivity "
            "to The Cat API just for fun. Their source code can be found at "
            "https://github.com/radixsh/qubitz.",
            color=0xb2558d)

    music_cmds = (f'`{PREFIX}p[lay] <search term>`: Streams the first YouTube '
                'result in vc.\n')
    music_cmds += (f'`{PREFIX}np`: Displays the current song.\n')
    music_cmds += (f'`{PREFIX}q[ueue]`: Displays the song queue.\n')
    music_cmds += (f'`{PREFIX}rm <some song>`: Removes the specified song '
                'from the queue.\n')
    music_cmds += (f'`{PREFIX}skip`: Skips the currently playing song.\n')
    music_cmds += (f'`{PREFIX}stop`: Disconnects Qubitz from vc.\n')
    embed.add_field(name=f'**Music**',
            value=music_cmds,
            inline=False)

    utilities_cmds = (f'`{PREFIX}l[ist]`: Lists each role and everyone in them.\n')
    utilities_cmds += (f'`{PREFIX}f[ind] <some role>`: Prints a list of everyone '
                    'with the specified role.\n')
    utilities_cmds += (f"`{PREFIX}p[ing]`: Pokes Qubitz to see if they're "
                    "awake.\n")
    utilities_cmds += (f"`{PREFIX}up[time]`: Displays how long Qubitz has "
                    "been awake.\n")
    utilities_cmds += (f'`{PREFIX}i[nfo] ("all")`: Displays guild and channel '
                    'information, and if "all" is given as an argument, then '
                    'displays guild member information as well.\n')
    embed.add_field(name=f'**Utilities**',
            value=utilities_cmds,
            inline=False)

    miscellaneous_cmds = (f'`{PREFIX}create <emoji_name>`: Sets attached image as '
                    'a custom server emoji with the given name.\n')
    miscellaneous_cmds += (f"`{PREFIX}uwu[ify] <something>`: Uwuifies "
                    "your message, deleting the command message.\n")
    miscellaneous_cmds += (f"`{PREFIX}echo <something>`: Echoes back your "
                    "message, deleting the command message.\n")
    miscellaneous_cmds += (f"`{PREFIX}c[at]`: Shows a cat from The Cat API.\n")
    embed.add_field(name=f'**Miscellaneous**',
            value=miscellaneous_cmds,
            inline=False)

    embed.set_footer(text="Contact radix#9084 with issues.")
    return await ctx.send(embed=embed)


@client.command(aliases=[])
async def ping(ctx):
    await ctx.send(f'Pong! {round(client.latency * 1000)} ms :)')


@client.command(aliases=['up', 'u'])
async def uptime(ctx):
    current_time = datetime.now()
    delta = int((current_time - start_time).total_seconds())
    d, rem = divmod(delta, 24 * 60 * 60)
    h, rem = divmod(rem, 60 * 60)
    m, s = divmod(rem, 60)
    uptime = f"Uptime: `{d} day{'' if d == 1 else 's'}, "
    uptime += f"{h} hour{'' if h == 1 else 's'}, "
    uptime += f"{m} minute{'' if m == 1 else 's'}, "
    uptime += f"{s} second{'' if s == 1 else 's'}`"
    await ctx.send(uptime)


@client.command(aliases=['emoji', 'create'])
async def create_emoji(ctx, *args):
    async with ctx.typing():
        if len(args) == 0:
            return await ctx.send(f'Error: give the emoji a name!')
    name = args[0]
    if len(name) < 2 or len(name) > 32:
        return await ctx.send(f'Error: the emoji\'s name must be between 2 and '
                '32 in length.')
    if name in str(ctx.guild.emojis):
        return await ctx.send(f'Error: that name is taken!')
    try:
        attachment_url = ctx.message.attachments[0].url
    except IndexError:
        return await ctx.send(f'Error: please attach the image to your message.'
                ' Also, Discord won\'t let me set external images as emojis, so'
                ' please attach/upload the image instead of sending a link :(')

    extensions = [".png",".jpg",".jpeg"]
    if not any(ext in attachment_url.lower() for ext in extensions):
        return await ctx.send(f'Error: please make sure the image is `.png`, '
                '`.jpg`, or `.jpeg` format.')

    if len(ctx.guild.emojis) >= ctx.guild.emoji_limit:
        await ctx.send(f'Error: all the emoji spots ({ctx.guild.emoji_limit}) '
                'are already taken!')

    async with aiohttp.ClientSession() as session:
        async with session.get(attachment_url, timeout = 20) as response:
            if response.status == 200:
                image_bytes = await response.content.read()
                try:
                    emoji = await ctx.guild.create_custom_emoji(name=name,
                            image=image_bytes)
                except aiohttp.ServerTimeoutError:
                    return await ctx.send(f'Sorry, server timed out! '
                            'Try again?')
                except Exception as e:
                    if "String value did not match validation regex" in str(e):
                        return await ctx.send(f"Sorry, special characters "
                                "aren't allowed!")
                    return await ctx.send(e)
                await ctx.send(f'New emoji: <:{emoji.name}:{emoji.id}> '
                        '(`<:{emoji.name}:{emoji.id}>`)')
            else:
                await ctx.send(f'Something went wrong; please contact '
                        'radix#9084 :(')


@client.command(aliases=['i'])
async def info(ctx, *args):
    def _details(members_info_requested=False):
        embed = discord.Embed(title="Information", color=0xb2558d)

        guild_details = f'**{ctx.guild}**'
        guild_details += f'\nID: `{ctx.guild.id}`'
        guild_details += f'\n{ctx.guild.member_count} members'
        embed.add_field(name=f'Guild', value=guild_details, inline=False)

        channel_details = f'**{ctx.channel}**'
        channel_details += f'\nID: `{ctx.channel.id}`'
        embed.add_field(name=f'Channel', value=channel_details, inline=False)

        if not members_info_requested:
            return embed

        for m in ctx.guild.members:
            name = m.nick if m.nick else m.name

            member_details = f'Username: {m.name}#{m.discriminator}'
            member_details += f'\nID: `{m.id}`'
            member_details += f'\nJoined on {m.joined_at.strftime("%-d %b %Y")}'
            if len(m.activities):
                gerund = str(m.activities[0].type)
                gerund = gerund[gerund.index('.')+1:] + " "
                if gerund == "listening ":
                    gerund += "to "
                if gerund == "custom ":
                    gerund = ""
                member_details += f'\nStatus: {gerund}{m.activities[0].name}'
            else:
                member_details += f'\nNo current activities'

            embed.add_field(name=f'{name}', value=member_details, inline=True)

        return embed

    if args and args[0] in ["users", "all", "*"]:
        await ctx.send(embed=_details(members_info_requested=True))
    else:
        await ctx.send(embed=_details())


@client.command(aliases=['uwu'])
async def uwuify(ctx, *, arg):
    await ctx.message.delete()
    arg = arg.replace("r", "w")
    arg = arg.replace("small", "smol")
    arg = arg.replace("l", "w")
    arg = arg.replace("na","nya")
    arg = arg.replace("no", "nyo")
    # Fix overcorrection
    arg = arg.replace("smow", "smol")
    await ctx.send(arg)


@client.command(aliases=[])
async def echo(ctx, *, arg):
    await ctx.message.delete()
    await ctx.send(arg)


@client.command(aliases=['c'])
async def cat(ctx):
    async with ctx.typing():
        response = requests.get("https://api.thecatapi.com/v1/images/search")
    json_data = json.loads(response.text)[0]
    await ctx.send(json_data["url"])


@client.command(aliases=['l'])
async def list(ctx, *args):
    ALL_ROLES = {}

    for m in ctx.guild.members:
        for role in m.roles:
            if role.name != "@everyone":
                if role.name in ALL_ROLES:
                    ALL_ROLES[role.name].append(f'`{m.name}#{m.discriminator}`')
                else:
                    ALL_ROLES[role.name] = [f'`{m.name}#{m.discriminator}`']

    for role in ALL_ROLES:
        long_list = f'**{role}**: {", ".join(ALL_ROLES[role])}\n'
        if len(long_list) < 2000:
            await ctx.send(long_list)
        else:
            parts = []
            for i in range(0, len(long_list), 1000):
                parts.append(long_list[i:i+1000])
            if len(parts) > 3:
                await ctx.send(f'(**{role}** has too many people in it to '
                        'list)')
            else:
                for part in parts:
                    await ctx.send(part)
    return


@client.command(aliases=['f'])
async def find(ctx, *, role):
    real_roles = []
    for real_role in ctx.guild.roles:
        real_roles.append(real_role.name)
    if role not in real_roles:
        return await ctx.send("That role does not exist!")

    people_in_role = []
    for m in ctx.guild.members:
        member_specific_roles = []
        for r in m.roles:
            member_specific_roles.append(r.name)
        if role in member_specific_roles:
            people_in_role.append(f'`{m.name}#{m.discriminator}`')

    if not people_in_role:
        return await ctx.send(f'No one with that role!')

    long_list = f'People with role `{role}`:\n'
    for person in people_in_role:
        long_list += f'{person}\n'
    parts = []
    for i in range(0, len(long_list)-1, 1900):
        temp = long_list[i:i+1900].rindex("\n")
        try:
            await ctx.send(long_list[i:temp])
        except:
            print(f'Failed to ctx.send: {long_list[i:temp]}')
    return


client.run(TOKEN)
