#! /usr/bin/python
import argparse
import asyncio

import aiohttp
import orjson
import redis.asyncio as redis
from aiohttp import ClientConnectorError
from playwright.async_api import async_playwright
from rich import print
from selectolax.parser import HTMLParser

# Kick.com API and WebSocket URLs
BASE_URL = "https://kick.com/api/v2/channels"
WS_URL = "wss://ws-us2.pusher.com/app/eb1d5f283081a78b932c?protocol=7&client=js&version=7.6.0&flash=false"

# Create a Redis connection
try:
	r = redis.Redis(host='localhost', port=6379)
except Exception as e:
	print(f"An error occurred when connecting to Redis: {e}")

def parse_arguments():
	parser = argparse.ArgumentParser(description="Kick Chat Listener")
	parser.add_argument("--channel", type=str, required=True, help="Kick channel name")
	args = parser.parse_args()
	return args.channel

async def get_chatroom_id(channel_name: str):
	url = f"{BASE_URL}/{channel_name}"
	async with async_playwright() as p:
		try:
			# Launch a Chromium browser to bypass Cloudflare
			browser = await p.chromium.launch(headless=False)
			page = await browser.new_page()
			await page.goto(url)
			html = HTMLParser(await page.content())
			await browser.close()

			# Get the chatroom ID from the JSON
			channel_data = orjson.loads(html.css_first("body").text())
			channel_id = channel_data["chatroom"]["id"]
			return channel_id
		except Exception as e:
			print(f"An error occurred when getting chatroom id: {e}")
			return None

async def connect_to_kick_chat(chatroom_id: int, channel_name: str):
	async with aiohttp.ClientSession() as session:
		try:
			async with session.ws_connect(WS_URL) as ws:
				print(f"Connected to {channel_name} chat, listening for messages...")
				chatroom_subscribe_message = {
					"event": "pusher:subscribe",
					"data": {"auth": "", "channel": f"chatrooms.{chatroom_id}.v2"}}
				await ws.send_str(orjson.dumps(chatroom_subscribe_message).decode())

				channel_subscribe_message = {
					"event": "pusher:subscribe",
					"data": {"auth": "", "channel": f"channel.{chatroom_id}"}}
				await ws.send_str(orjson.dumps(channel_subscribe_message).decode())

				async for msg in ws:
					data = orjson.loads(msg.data)
					if data.get("event") == "App\\Events\\ChatMessageEvent":
						message_data = orjson.loads(data["data"])
						message = {
							"platform": "Kick",
							"channel": data["channel"],
							"channel_name": channel_name,
							"message_id": message_data["id"],
							"chatroom_id": message_data["chatroom_id"],
							"content": message_data["content"],
							"message_type": message_data["type"],
							"created_at": message_data["created_at"],
							"sender_id": message_data["sender"]["id"],
							"username": message_data["sender"]["username"],
							"slug": message_data["sender"]["slug"],
							"color": message_data["sender"]["identity"]["color"],
							"badges": message_data["sender"]["identity"]["badges"],
						}

						# Publish data to the Redis channel
						await r.publish(f'{channel_name}_chat', orjson.dumps(message))
		except ClientConnectorError as e:
			print(f"Could not connect to the WebSocket: {e}")
		except Exception as e:
			print(f"An unexpected error occurred: {e}")

async def main(channel_name):
	chatroom_id = await get_chatroom_id(channel_name)
	if chatroom_id is not None:
		print(f"Chatroom ID: {chatroom_id}")
		await connect_to_kick_chat(chatroom_id, channel_name)

if __name__ == "__main__":
	channel_name = parse_arguments()
	asyncio.run(main(channel_name))
