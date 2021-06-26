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

bot = commands.Bot(command_prefix="!")

channels = {}


@bot.command(name='channel', help='Tells the bot which channel to send messages in.')
async def channel(ctx, channel):
    ch = discord.utils.get(ctx.guild.text_channels, name=channel)
    channels[ctx.guild] = ch
    if ch is None:
        await ctx.channel.send("Couldn't find a channel with that name...")
    else:
        await ctx.channel.send("Will send goodnight messages in " + ch.name)
        updateStoredChannel(ctx.guild.id, ch.id)


async def say_goodnight(member):
    message_pool = ["Sweet dreams!",
                    "May the sheep you count tonight be numerous and fluffy.",
                    "Sleep well!",
                    "I'll miss you, as much as a Discord bot can."
                    "And if you dream about a toilet, don't use it."
                    ]
    if 'Phasmophobia' in [str(r) for r in member.roles] or 'Phasmo' in [str(r) for r in member.roles]:
        message_pool.append("Don't forget to keep an eye out for ghosts...")

    if 'Europe' in [str(r) for r in member.roles]:
        tz = pytz.timezone('Europe/Paris')
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


def updateStoredChannel(guild, channel):
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
    print(channels)


def get_stored_channels():
    channels = {}
    db = connectToDB()
    cur = db.cursor()
    cur.execute("SELECT * FROM channels")
    data = cur.fetchall()
    for row in data:
        guild = bot.get_guild(int(row[0]))
        channel = bot.get_channel(int(row[1]))
        channels[guild] = channel
    return channels


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
    global channels
    channels = get_stored_channels()


bot.run(TOKEN)
