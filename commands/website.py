"""
Commands that involving scrapping one specific website, and their related functions.
"""

import random
from discord.ext import commands
import os
import praw


class Website:

    def __init__(self, bot):
        self._bot = bot
        self._reddit = None

    @commands.command()
    async def reddit(self, subreddit):
        """
        Gets a random hot submission from any subreddit.
        Ex. ?reddit android
        """

        # Set reddit client once
        if not self._reddit:
            try:
                self._reddit = praw.Reddit(client_id=os.environ["REDDIT_CLIENT_ID"],
                                           client_secret=os.environ["REDDIT_CLIENT_SECRET"],
                                           user_agent=os.environ["REDDIT_USER_AGENT"])
            except:
                await self._bot.say("Reddit authorization failed.")
                return

        # Get random submission within limit
        limit = 50
        i = random.randrange(limit)
        for idx, post in enumerate(self._reddit.subreddit(subreddit).hot(limit=50)):
            if idx == i:
                reply = post.title + "\n" + post.url
                await self._bot.say(reply)
                break
