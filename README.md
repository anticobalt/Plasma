# Plasma

A Discord bot that generates things.

## Features
- Flip coin / roll dice / choose random item or number
- Get a random submission from the front page of a Reddit subreddit
- Look up specific or get random WW2-era warship class from Wikipedia

## Requirements

- Python 3.6.1
- BeautifulSoup 4.6
- discord.py 0.16.11
- PRAW (Python Reddit API Wrapper) 4.5.1
- wikipedia.py 1.4

## To-do

- Use JSON instead of object serialization for caching
- Add lookup/generation support for DDs, CLs, CAs, SSs; currently omitted as Wikipedia is not comprehensive
- Remove dependency on wikipedia.py (a lot of work is already done by BeautifulSoup)
- More features
- Update library requirements

## Bugs
- If a command is missing arguments, exceptions thrown are uncatchable. Bot continues running though.