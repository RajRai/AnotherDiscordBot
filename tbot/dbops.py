import sqlite3
from sqlite3 import Error
from os.path import join, dirname


def get_stored_nicknames():
    data = get_from_db("SELECT * FROM nicknames")
    names = {}
    for row in data:
        names[int(row[0])] = row[1]
    return names


def store_nickname(account, name):
    db = connectToDB()
    cur = db.cursor()
    try:
        cur.execute("INSERT INTO nicknames VALUES (?,?)", [account, name])
    except Exception as e:
        print(e)
        try:
            cur.execute("UPDATE nicknames SET nickname = ? WHERE account = ?;", [name, account])
        except Exception as e:
            print(e)
    db.commit()
    db.close()


def remove_stored_nickname(account):
    db = connectToDB()
    cur = db.cursor()
    cur.execute("DELETE FROM nicknames WHERE account = ?", [account])
    db.commit()
    db.close()


def get_stored_phrases(bot):
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
    except Error as e:
        print(e)
        try:
            cur.execute("UPDATE channels SET channel = ? WHERE guild = ?;", [channel, guild])
        except Error as e:
            print(e)
    db.commit()
    db.close()


def get_stored_channels(bot):
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
