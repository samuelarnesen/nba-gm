import asyncio
import discord
import subprocess
import dotenv
import os
import re
import sys
import threading
import time


dotenv.load_dotenv()
token = os.getenv('DISCORD_TOKEN')
channel_id = os.getenv('CHANNEL_ID')
bot_id = os.getenv("BOT_ID")

client = discord.Client(intents=discord.Intents.default())
process = None

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    global process

    if message == None or message.content == None:
        print("Ignoring None")
        return

    if 'nba-fantasy-gm' in message.author.name:
        return

    if len(message.content.split()) <= 1 or bot_id not in message.content:
        print("Ignoring empty")
        print("message content is " + message.content)
        print("message length is ", len(message.content))
        print("Message: ", message)
        print("Author", message.author)
        print("Split length", len(message.content.split()))
        return

    if '!start_game' in message.content and process == None:
        process = await asyncio.create_subprocess_exec(
            'python3', './play_game.py',
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        print("started game")

    if 'nba-fantasy-gm' not in message.author.name and "!start_game" not in message.content and len(message.content.split()) > 1:
        str_input = " ".join(message.content.split()[1:]) + "\n"
        process.stdin.write(str_input.encode())
        try:
            await process.stdin.drain()
        except:
            print("Connection reset error")



    total = ""
    line = ""
    while "Error" not in line and "executed" not in line.lower() and "Accepting" not in line and \
        "to select" not in line and "end game" not in line.lower() and "Trade complete" not in line.lower():
        line = await process.stdout.readline()
        line = line.decode('utf-8')
        print(line)
        total = total + line
        if not line:
            break

    if len(total) > 1:
        if "...And your champion is..." in total:
            game = 1
            for individual_line in re.split("Finals Game \d", total):
                if individual_line:
                    await message.channel.send(f"\n\n\n===\n\n\nGame {game}\n{individual_line}")
                    game += 1
                    time.sleep(2)
        else:
            print("LENGTH:", len(total))
            if len(total) > 2000:
                await message.channel.send(total[0:2000])
                await message.channel.send(total[2000:])
            else:
                await message.channel.send(total)

    return

client.run(token)


