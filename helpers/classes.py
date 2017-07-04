import random

import praw
import wikipedia
from discord.ext import commands

from data import secrets
from helpers import webdata


class Basic:
    """Generates random outcomes."""

    def __init__(self, bot):
        self._bot = bot

    @commands.command()
    async def coin(self):
        side = {0: "heads",
                1: "tails"}
        reply = "Coin landed {side}.".format(side=random.choice(side))
        await self._bot.say(reply)

    @commands.command()
    async def dice(self):
        reply = "Rolled a {side}.".format(side=random.randint(1, 6))
        await self._bot.say(reply)

    @commands.command()
    async def choose(self, *args):
        try:
            reply = "I choose {choice}.".format(choice=random.choice(args))
        except IndexError:
            reply = "I choose nothing."
        await self._bot.say(reply)

    @commands.command()
    async def int(self, lower=1, upper=10):
        try:
            reply = "I choose {num}.".format(num=random.randint(int(lower), int(upper)))
        except ValueError:
            reply = "I choose {num}.".format(num=random.randint(int(upper), int(lower)))
        await self._bot.say(reply)


class Web:
    """Gets data from various online sources."""

    def __init__(self, bot):
        self._bot = bot
        self._reddit = None
        self._ship_classes = None

    def _get_random_ship_class(self, specification):

        while 1:
            ship_class = random.choice(self._ship_classes)
            f_names = ["Japanese", "United States", "Kriegsmarine", "Royal Navy", "Regia", "French"]
            t_names = ["carrier", "destroyer", "battle", "heavy cruiser", "light cruiser", "submarine"]
            if (
                not specification or
                (specification == "ijn" and f_names[0] in ship_class["faction"]) or
                (specification == "usn" and f_names[1] in ship_class["faction"]) or
                (specification == "km" and f_names[2] in ship_class["faction"]) or
                (specification == "rn" and f_names[3] in ship_class["faction"]) or
                (specification == "rm" and f_names[4] in ship_class["faction"]) or
                (specification == "fn" and f_names[5] in ship_class["faction"]) or
                (specification == "minor" and not any(name in ship_class["faction"] for name in f_names)) or

                (specification == "cv" and t_names[0] in ship_class["ship_type"].lower()) or
                (specification == "dd" and t_names[1] in ship_class["ship_type"].lower()) or
                (specification == "bb" and t_names[2] in ship_class["ship_type"].lower()) or
                (specification == "ca" and t_names[3] in ship_class["ship_type"].lower()) or
                (specification == "cl" and t_names[4] in ship_class["ship_type"].lower()) or
                (specification == "other" and not any(name in ship_class["ship_type"].lower() for name in t_names))
            ):
                break

        return ship_class

    @commands.command()
    async def warship(self, specification=None):
        """
        Gets a random WW2-era warship class via Wikipedia.
        [specification] can be faction acronym (IJN, USN, KM, RN, RM, FN, minor).
        [specification] can also be a hull type (CV, CA, CL, DD, BB, SS, other).

        IJN = Imperial Japanese Navy
        USN = United States Navy
        KM = Kriegsmarine (Nazi Germany)
        RN = Royal Navy (Britain)
        RM = Regia Marina (Kingdom of Italy)
        FN = French Navy

        CV = Aircraft Carrier
        CA = Heavy Cruiser
        CL = Light Cruiser
        DD = Destroyer
        BB = Battleship/Battlecruiser
        SS = Submarine
        """

        # Fetch classes if none exist yet (i.e. first request since bot startup)
        if self._ship_classes is None:
            self._ship_classes = webdata.get_warship_classes()

        spec = (specification.lower() if specification else specification)
        ship_class = self._get_random_ship_class(spec)
        link = ""

        # Get summary if page exists
        if ship_class["page_title"]:

            title = ship_class["page_title"]

            # Try to get summary and link via wikipedia.py
            try:
                page = wikipedia.page(title=title)
                summary = "\n\n" + page.summary.split("\n")[0]
                link = webdata.get_wikipedia_first_image(title)

            # If page load fails, do it yourself
            except wikipedia.exceptions.PageError:
                summary = webdata.get_wikipedia_summary(title)
                link = webdata.get_wikipedia_first_image(title)

        else:
            summary = ""

        reply = "Class Name: {name}\n" \
                "Type: {ship_type}\n" \
                "Faction: {faction}\n" \
                "Launch Years: {years}\n" \
                "Displacement: {displacement}\n" \
                "Number in Class: {number}" \
                "{summary}".format(name=ship_class["name"],
                                   ship_type=ship_class["ship_type"],
                                   faction=ship_class["faction"],
                                   years=ship_class["launch_years"],
                                   displacement=ship_class["displacement"],
                                   number=ship_class["number"],
                                   summary=summary)

        await self._bot.say("```\n" + reply + "\n```")
        if link:
            await self._bot.say(link)

    @commands.command()
    async def refresh(self):
        """Re-fetches cached data. Use sparingly."""
        self._ship_classes = webdata.get_warship_classes(force_recache=True)
        await self._bot.say("Data refreshed.")

    @commands.command()
    async def reddit(self, subreddit):
        """
        Gets a random hot submission from any subreddit.
        Ex. ?reddit android
        """

        # Set reddit client once
        if not self._reddit:
            try:
                self._reddit = praw.Reddit(client_id=secrets.reddit_client_id,
                                           client_secret=secrets.reddit_client_secret,
                                           user_agent=secrets.reddit_user_agent)
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
