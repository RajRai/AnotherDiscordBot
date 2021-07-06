import discord
from tbot.dbops import *
from sqlite3 import Error
import asyncio
from discord.ext import commands
from datetime import datetime
import pytz
import random as rng
import sys

from tbot.atoken import TOKEN

prefix = '^'

debug = False

bot = commands.Bot(command_prefix=prefix)

channels = {}  # {Guild: Channel}
phrases = {}  # {Guild: [Phrases]}
nicknames = {}  # {User: Nickname}
disabled = []


def is_admin(ctx):
    return ctx.message.author.top_role.permissions.administrator


def is_dev(ctx):
    return ctx.author.id == 296153936665247745


def is_server_manager(ctx):
    return ctx.message.author.top_role.permissions.manage_guild


def server_manager_or_dev(ctx):
    return is_server_manager(ctx) or is_dev(ctx)


@bot.command(name='announcement', help='Dev use only')
@commands.check(is_dev)
async def announcement(ctx, *words):
    sentence = []
    for word in words:
        if word == r'\n':
            sentence.append('\n')
        else:
            sentence.append(word)
    message = " ".join(sentence)
    for guild in channels:
        await channels[guild].send(message)


@bot.command(name='disable', help='Tells Tucker not to tuck you in')
async def disable(ctx):
    disabled.append(ctx.author.id)
    store_disabled(ctx.author.id)
    await ctx.reply("Ok, disabled your goodnight messages")


@bot.command(name='enable', help='Tells Tucker to tuck you in')
async def enable(ctx):
    disabled.remove(ctx.author.id)
    remove_disabled(ctx.author.id)
    await ctx.reply("Ok, enabled your goodnight messages")


@bot.command(name='setnickname', help='Tell Tucker what to call you')
async def set_nickname(ctx, *words):
    name = " ".join(words)
    nicknames[ctx.author.id] = name
    store_nickname(ctx.author.id, name)
    await ctx.reply(f"Ok, set your nickname to {name}")


@bot.command(name='removenickname', help='Tells Tucker to use your mention when talking to you')
async def remove_nickname(ctx):
    nicknames.pop(ctx.author.id)
    remove_stored_nickname(ctx.author.id)
    await ctx.reply(f"Removed your nickname {ctx.author.mention}")


@bot.command(name='addphrase', help='Adds a custom goodnight phrase to the bot')
@commands.check(server_manager_or_dev)
async def add_phrase(ctx, *words):
    global phrases
    phrase = " ".join(words)
    try:
        phrases[ctx.guild].append(phrase)
        store_phrases(ctx.guild.id, phrase)
        await ctx.channel.send("Saved the phrase!")
    except KeyError:
        phrases[ctx.guild] = [phrase]
        store_phrases(ctx.guild.id, phrase)
        await ctx.channel.send("Saved the phrase!")
    except Error:
        await ctx.channel.send("Couldn't add that phrase to the list...")


@bot.command(name='showphrases', help='Shows the custom goodnight phrases saved by the bot')
@commands.check(server_manager_or_dev)
async def show_phrases(ctx):
    if ctx.guild in phrases:
        lst = phrases[ctx.guild]
    else:
        lst = []
    out = "Stored phrases:\n"
    for n in range(0, len(lst)):
        out += f"{n + 1}. {lst[n]}\n"
    if len(lst) == 0:
        out += "Nothing to see here yet..."
    await ctx.reply(out)


@bot.command(name='removephrase', help='Removes a custom goodnight phrase from the bot')
@commands.check(server_manager_or_dev)
async def remove_phrase(ctx, which):
    try:
        idx = int(which) - 1
    except ValueError:
        await ctx.reply(
            f"Sorry, but I was expecting a number referencing a stored phrase. Do {prefix}showphrases for the list.")
    phrase = phrases[ctx.guild][idx]
    del phrases[ctx.guild][idx]
    remove_stored_phrase(ctx.guild.id, phrase)
    await ctx.reply("Removed the phrase from storage.")


@bot.command(name='channel', help='Tells the bot which channel to send messages in')
@commands.check(server_manager_or_dev)
async def channel(ctx, channel):
    ch = discord.utils.get(ctx.guild.text_channels, name=channel)
    channels[ctx.guild] = ch
    if ch is None:
        await ctx.channel.send("Couldn't find a channel with that name...")
    else:
        await ctx.channel.send("Will send goodnight messages in " + ch.name)
        store_channel(ctx.guild.id, ch.id)


async def say_goodnight(member):
    message_pool = ["Sweet dreams!",
                    "May the sheep you count tonight be numerous and fluffy.",
                    "Sleep well!",
                    "I'll miss you, as much as a Discord bot can.",
                    "And if you dream about a toilet, don't use it."
                    ]
    if 'Phasmophobia' in [str(r) for r in member.roles] or 'Phasmo' in [str(r) for r in member.roles]:
        message_pool.append("Don't forget to keep an eye out for ghosts...")
    try:
        message_pool.extend(phrases[member.guild])
    except KeyError:
        pass

    if 'Europe' in [str(r) for r in member.roles] or 'EU' in [str(r) for r in member.roles]:
        tz = pytz.timezone('Europe/London')
    else:
        tz = pytz.timezone('US/Eastern')
    now = datetime.now(tz)
    if (now.hour >= 22 or now.hour <= 6 or (member.guild.name == "Raj's server")) and member.id not in disabled:
        randomized_message = rng.choice(message_pool)
        try:
            if member.id in nicknames:
                await channels[member.guild].send(f"Goodnight, {nicknames[member.id]}! {randomized_message}")
            else:
                await channels[member.guild].send(f"Goodnight, {member.mention}! {randomized_message}")
        except Error:
            pass


@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is not None and after.channel is None:
        if member.guild.name != "Raj's server":
            await asyncio.sleep(15)
        if member is not None and member.voice is None:
            await say_goodnight(member)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply("A required argument for that command is missing!")
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("You lack the permissions to use that command...")


@bot.event
async def on_ready():
    global channels, phrases, nicknames, disabled
    channels = get_stored_channels(bot)
    phrases = get_stored_phrases(bot)
    nicknames = get_stored_nicknames()
    disabled = get_disabled()

    print(channels)
    print(phrases)
    print(nicknames)
    print(disabled)

    if debug:
        for guild in list(channels.keys()):
            if guild.name != "Raj's server":
                channels.pop(guild)


def parse_mode():
    global debug
    try:
        for arg in sys.argv:
            if arg in ("-d", "--debug"):
                debug = True
                print("Enabled debugging mode")
    except Exception as err:
        print(str(err))


parse_mode()
bot.run(TOKEN)
