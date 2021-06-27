from os.path import dirname, join
import discord
import sqlite3
from sqlite3 import Error
import asyncio
from discord.ext import commands
from datetime import datetime
import pytz
import random as rng

from tbot.atoken import TOKEN

prefix = '!'

bot = commands.Bot(command_prefix=prefix)

channels = {}

phrases = {}


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
async def announcement(ctx, message):
    for guild in channels:
        await channels[guild].send(message)


@bot.command(name='addphrase', help='Adds a custom goodnight phrase to the bot')
@commands.check(server_manager_or_dev)
async def add_phrase(ctx, phrase):
    global phrases
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
    lst = phrases[ctx.guild]
    out = "Stored phrases:\n"
    for n in range(0, len(lst)):
        out += f"{n+1}. {lst[n]}\n"
    if len(lst) == 0:
        out += "Nothing to see here yet..."
    await ctx.reply(out)


@bot.command(name='removephrase', help='Removes a custom goodnight phrase from the bot')
@commands.check(server_manager_or_dev)
async def remove_phrase(ctx, which):
    try:
        idx = int(which)-1
    except ValueError:
        await ctx.reply(
            f"Sorry, but I was expecting a number referencing a stored phrase. Do {prefix}showphrases for the list.")
    phrase = phrases[ctx.guild][idx]
    del phrases[ctx.guild][idx]
    remove_stored_phrase(ctx.guild.id, phrase)
    await ctx.reply("Removed the phrase from storage.")


@bot.command(name='channel', help='Tells the bot which channel to send messages in.')
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
    except Error:
        pass

    if 'Europe' in [str(r) for r in member.roles] or 'EU' in [str(r) for r in member.roles]:
        tz = pytz.timezone('Europe/London')
    else:
        tz = pytz.timezone('US/Eastern')
    now = datetime.now(tz)
    if now.hour >= 22 or now.hour <= 6:
        randomized_message = rng.choice(message_pool)
        try:
            await channels[member.guild].send("Goodnight, " + member.mention + "! " + randomized_message)
        except:
            pass


@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is not None and after.channel is None:
        await asyncio.sleep(15)
        if member is not None and member.voice is None:
            await say_goodnight(member)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply("A required argument for that command is missing!")
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("You lack the permissions to use that command...")


def get_stored_phrases():
    data = get_from_db("SELECT * FROM phrases")
    phrases = {}
    for row in data:
        guild = bot.get_guild(int(row[0]))
        phrase = row[1]
        try:
            phrases[guild].append(phrase)
        except KeyError:
            phrases[guild] = [phrase]
    return phrases


def store_phrases(guild, phrase):
    db = connectToDB()
    cur = db.cursor()
    try:
        cur.execute("INSERT INTO phrases VALUES (?,?)", [guild, phrase])
    except Exception as e:
        print(e)
        try:
            cur.execute("UPDATE phrases SET phrase = ? WHERE guild = ?;", [phrase, guild])
        except Exception as e:
            print(e)
    db.commit()
    db.close()


def remove_stored_phrase(guild, phrase):
    db = connectToDB()
    cur = db.cursor()
    cur.execute("DELETE FROM phrases WHERE guild = ? AND phrase = ?", [guild, phrase])
    db.commit()
    db.close()


def store_channel(guild, channel):
    db = connectToDB()
    cur = db.cursor()
    try:
        cur.execute("INSERT INTO channels VALUES (?,?)", [guild, channel])
    except Exception as e:
        print(e)
        try:
            cur.execute("UPDATE channels SET channel = ? WHERE guild = ?;", [channel, guild])
        except Exception as e:
            print(e)
    db.commit()
    db.close()


def get_stored_channels():
    channels = {}
    data = get_from_db("SELECT * FROM channels")
    for row in data:
        guild = bot.get_guild(int(row[0]))
        channel = bot.get_channel(int(row[1]))
        channels[guild] = channel
    return channels


def get_from_db(sql):
    db = connectToDB()
    cur = db.cursor()
    cur.execute(sql)
    data = cur.fetchall()
    db.close()
    return data


def connectToDB():
    db_file = join(dirname(dirname(__file__)), 'sqlite', 'botdb.db')
    conn = None
    try:
        conn = sqlite3.connect(db_file, isolation_level=None)
        return conn
    except Error as e:
        print(e)
    return conn


@bot.event
async def on_ready():
    global channels, phrases
    channels = get_stored_channels()
    phrases = get_stored_phrases()


bot.run(TOKEN)
