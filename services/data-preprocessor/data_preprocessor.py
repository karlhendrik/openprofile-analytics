#! /usr/bin/python
import argparse
import asyncio
import re

import aiohttp
import nltk
import orjson
import redis.asyncio as redis
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from rich import print


def parse_arguments():
	parser = argparse.ArgumentParser(description="Data Preprocessor")
	parser.add_argument("--channel", type=str, required=True, help="Channel name")
	args = parser.parse_args()
	return args.channel

# Precompile regular expressions
url_pattern = re.compile(r'https?://\S+|www\.\S+')
non_word_number_pattern = re.compile(r'[^\w\s]|d+')
emote_pattern = re.compile(r'\[emote:\d+:[\w\d]+\]')


# Download and setup NLTK Stop words
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
stop_words = set(stopwords.words('english'))

async def preprocess_message(message):
    word_tokens = word_tokenize(message)
    filtered_message = [w for w in word_tokens if not w in stop_words] # noqa
    return filtered_message

async def has_min_words(text, min_words=4):
    return len(text.split()) >= min_words

async def has_min_chars(text, min_chars=3):
    return len(text) >= min_chars

async def remove_urls(text):
    return url_pattern.sub(r'', text)

async def has_emoji(text):
    return emote_pattern.search(text) is not None

async def is_bot(username):
    return username in {
        'nightbot',
        'streamelements', 
        'streamlabs',
        'moobot', 
        'commanderroot', 
        'pretzelrocks', 
        'streamcaptainapp',
        'BotRix',
        'fossabot'
    }

async def process_badges(badges):
    return [badge['type'] for badge in badges]

async def preprocess_kick_data(data):
    # Drop message if it's from a bot
    if 'username' in data and await is_bot(data['username']):
        return None

    # Drop message if emoji detected
    if 'content' in data and emote_pattern.search(data['content']):
        return None

    # Preprocess 'content'
    if 'content' in data and await has_min_words(data['content']) and await has_min_chars(data['content']): # noqa
        # Remove emojis, urls, punctuation, and numbers
        processed_text = data['content']
        processed_text = await remove_urls(processed_text)
        return {
            'platform': 'Kick',
            'channel': data.get('channel_name'),
            'username': data.get('username'),
            'message': processed_text,
            'message_tokens': await preprocess_message(processed_text),
            'slug': data.get('slug'),
            'sender_id': data.get('sender_id'),
            'badges': await process_badges(data.get('badges')) if data.get('badges') else None, # noqa
            'timestamp': data.get('created_at'),
        }
        
    return None

async def preprocess_twitch_data(data):
    # Drop message if it's from a bot
    if 'user' in data and await is_bot(data['user']):
        return None

    # Drop message if emoji detected
    if 'text' in data and emote_pattern.search(data['text']):
        return None

    # Preprocess 'text'
    if 'text' in data and await has_min_words(data['text']) and await has_min_chars(data['text']): # noqa
        # Remove emojis, urls, punctuation, and numbers
        processed_text = data['text']
        processed_text = await remove_urls(processed_text)
        processed_content = await preprocess_message(processed_text)

        # Include necessary fields in the return value
        return {
            'platform': data.get('platform'),
            'channel': data.get('channel'),
            'username': data.get('user'),
            'message': processed_text,
            'message_tokens': processed_content,
            'timestamp': data.get('timestamp'),
        }

    return None

async def handle_message(message):
    data = orjson.loads(message['data'].decode('utf-8'))
    match data['platform']:
        case 'Twitch':
            processed_data = await preprocess_twitch_data(data)
        case 'Kick':
            processed_data = await preprocess_kick_data(data)
        case _:
            processed_data = None

    if data is not None and processed_data is not None:
        print(processed_data)

async def main():
    channel_name = parse_arguments()
    try:
        r = redis.Redis(host='localhost', port=6379)
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(**{f'{channel_name}_chat': handle_message})
    except Exception as e:
        print(f"An error occurred when connecting to Redis: {e}")

    while True:
        message = await p.get_message()
        if message:
            await p.handle_message(message)

asyncio.run(main())
