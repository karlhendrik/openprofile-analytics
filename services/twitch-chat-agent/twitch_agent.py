#! /usr/bin/python
import argparse
import asyncio
import datetime

import aiohttp
import orjson
import redis.asyncio as redis
from aiohttp import ClientConnectorError
from rich import print

# Twitch API and WebSocket URLs
WS_URL = "wss://irc-ws.chat.twitch.tv:443"

# Create a Redis connection
try:
    r = redis.Redis(host='localhost', port=6379)
except Exception as e:
    print(f"An error occurred when connecting to Redis: {e}")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Twitch Chat Listener")
    parser.add_argument("--channel", type=str, required=True, help="Twitch channel name")
    args = parser.parse_args()
    return args.channel

async def connect_to_tmi_chat(channel_name: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.ws_connect(WS_URL) as ws:
                await ws.send_str("PASS oauth:abcdefghijk")
                await ws.send_str("NICK justinfan123")
                await ws.send_str(f"JOIN #{channel_name}")

                async for msg in ws:
                    message = msg.data.strip()
                    if message.startswith("PING"):
                        await ws.send_str("PONG")
                    elif "PRIVMSG" in message:
                        user, text = message.split("PRIVMSG", 1)
                        user = user.split("!")[0][1:]
                        text = text.split(":", 1)[1].strip()
                        timestamp = datetime.datetime.now().isoformat()

                        message = {
                            "platform": "Twitch",
                            "channel": channel_name,
                            "timestamp": timestamp,
                            "user": user,
                            "text": text
                        }
                        await r.publish(f'{channel_name}_chat', orjson.dumps(message))

        except ClientConnectorError as e:
            print(f"Could not connect to the WebSocket: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    channel_name = parse_arguments()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(connect_to_tmi_chat(channel_name))
    except KeyboardInterrupt:
        tasks = asyncio.all_tasks(loop=loop)
        for task in tasks:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        loop.close()