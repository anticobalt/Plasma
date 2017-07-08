# Plasma

A Discord bot that generates things.

## Features
- Flip coin / roll dice / choose random item or number
- Get a random submission from the front page of a Reddit subreddit
- Get a random WW2-era warship class from Wikipedia

## Requirements

- Python 3.6.1
- BeautifulSoup 4.6
- discord.py 0.16.8
- PRAW (Python Reddit API Wrapper) 4.5.1
- wikipedia.py 1.4

These specific versions do work; others might. Obviously newer versions have a higher probability of working than older 
versions

## To-do

- Make bot public
- Remove dependency on wikipedia.py (a lot of work is already done by BeautifulSoup)
- Speed up warship generator by caching nation/type specifications
- Add commands to warship generator (e.g. lookup specific ships)
- More features

## Bugs
- If a command is missing arguments, exceptions thrown are uncatchable. Bot continues running though.