# Plasma

A Discord bot that generates things.

## Features
- Flip coin / roll dice / choose random item or number
- Get a random submission from the front page of a Reddit subreddit
- Get a random WW2-era warship class from Wikipedia

## Requirements

- Python 3.5.1
- BeautifulSoup 4.6
- discord.py 0.16.8
- PRAW (Python Reddit API Wrapper) 4.5.1
- wikipedia.py 1.4

These specific versions do work; others might. Obviously newer versions have a higher probability of working than older 
versions

## How to use

Under ./data/, create file "secrets.py" and set the following values:
- discord_key
- reddit_client_id
- reddit_client_secret
- reddit_user_agent

Default command prefix is "?", but can be changed in ./plasma.py.

## To-do

- Remove dependency on wikipedia.py (a lot of work is already done by BeautifulSoup)
- Speed up warship generator by caching nation/type specifications
- Add commands to warship generator (e.g. lookup specific ships)
- More features

## Bugs
- If a command is missing arguments, exceptions thrown are uncatchable. Bot continues running though.