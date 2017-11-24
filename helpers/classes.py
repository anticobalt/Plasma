import random

from discord.ext import commands
import os
import praw
import wikipedia

from helpers import constants, webdata


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

    @commands.command()
    async def help(self, command=None):
        delimiter = "?"
        if command is None:
            s = (
                "**Commands:**\n\n"
                "`{d}coin`: flips a coin\n"
                "`{d}dice`: rolls a dice\n"
                "`{d}choose <option 1> <option 2> <etc>`: randomly picks from list\n"
                "`{d}int <optional min> <optional max>`: randomly picks integer from range, default 1-10\n\n"
                "`{d}reddit <subreddit name>`: gets random hot submission from subreddit\n"
                "`{d}warship <optional specification>`: under construction\n"
                "`{d}more`: loads more information from last `{d}warship` call\n"
                "`{d}refresh`: reloads warship database; use sparingly\n\n"
                "`{d}help`: displays this list\n"
                "`{d}help <command>`: displays detailed information about a command"
            ).format(d=delimiter)
        elif command == "warship":
            s = (
                "```\n"
                "Gets a random WW2-era warship class via Wikipedia.\n"
                "[specification] can be faction acronym (IJN, USN, KM, RN, RM, FN, minor).\n"
                "[specification] can also be a hull type (CV, CA, CL, DD, BB, SS, other).\n\n"

                "IJN = Imperial Japanese Navy\n"
                "USN = United States Navy\n"
                "KM = Kriegsmarine (Nazi Germany)\n"
                "RN = Royal Navy (Britain)\n"
                "RM = Regia Marina (Kingdom of Italy)\n"
                "FN = French Navy\n"

                "CV = Aircraft Carrier\n"
                "CA = Heavy Cruiser\n"
                "CL = Light Cruiser\n"
                "DD = Destroyer\n"
                "BB = Battleship\n"
                "SS = Submarine\n"
                "```"
            )
        else:
            s = "Doesn't get any more detailed than what's listed in `{d}help`, kiddo.".format(d=delimiter)

        await self._bot.say(s)


class Web:
    """Gets data from various online sources."""

    def __init__(self, bot):
        self._bot = bot
        self._reddit = None
        self._wikipedia_root = "https://en.wikipedia.org/wiki/"
        self._ship_classes = {}
        self._ship_spec_table = {}
        self._generator = None
        self._last_ship_url = ""

    def _text_generator(self, text):
        """
        Generator for text separated by paragraphs (i.e. newlines)
        :param text: Str
        :yield: Str
        """
        paragraphs = text.split("\n")
        for paragraph in paragraphs:
            yield paragraph

    def _get_random_ship_class(self, specification):
        """
        :param specification: lower-case Str; already validated
        :return: Dict
        """
        expansions = {**constants.NATIONS, **constants.HULL_TYPES}
        if specification:
            name = random.sample(self._ship_spec_table[expansions[specification]], 1)[0]
        else:
            rand_spec = random.choice(list(expansions.values()))
            name = random.sample(self._ship_spec_table[rand_spec], 1)[0]
        choice = self._ship_classes[name]
        return choice

    def _get_ship_class(self, name):
        # Todo: Implement
        # Todo: Allow searching for individual ships as opposed to ship classes
        # Todo: Implement fuzzy searching (e.g. Search for 'Bismark' failed. Did you mean 'Bismarck'?)
        pass

    def _generate_class_reply(self, ship_class, link):
        # Get summary if page exists
        if ship_class["link_title"]:

            title = ship_class["link_title"]

            # Try to get summary and link via wikipedia.py
            try:
                page = wikipedia.page(title=title)
                raw_summary = page.summary
                link = webdata.get_wikipedia_first_image(self._wikipedia_root, title)

            # If page load fails, do it yourself
            except wikipedia.exceptions.PageError:
                raw_summary = webdata.get_wikipedia_summary(self._wikipedia_root, title)
                link = webdata.get_wikipedia_first_image(self._wikipedia_root, title)

            # Set generator so that paragraphs can be yielded if called by self.more()
            self._generator = self._text_generator(raw_summary)
            summary = "\n\n" + next(self._generator)
            self._last_ship_url = self._wikipedia_root + title.replace(" ", "_")

        else:
            summary = ""
            self._last_ship_url = "No Wikipedia article for this ship exists."

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

        return reply

    def _generate_ship_reply(self, ship, link):
        pass

    @commands.command()
    async def warship(self, *, str_args: str):
        """
        Gets a random WW2-era warship class via Wikipedia.
        Under construction.
        -s to search by hull type or faction.
        """

        # Fetch classes if none exist yet (i.e. first request since bot startup)
        if not self._ship_classes:
            self._ship_classes, self._ship_spec_table = webdata.get_warship_data()

        # Check and modify specification string
        args = str_args.split(" ")
        if args and args[0] == "-s" and len(args) == 2:
            # Get random class
            specification = args[1].lower()
            if specification:
                named = set({**constants.NATIONS, **constants.HULL_TYPES}.keys())
                if not (specification in named or specification == "minor" or specification == "other"):
                    await self._bot.say("Invalid specification. Defaulting to none ...")
                    specification = None
            else:
                specification = None
            ship_class = self._get_random_ship_class(specification)
            link = ""
            reply = self._generate_class_reply(ship_class, link)
        elif len(args) == 0:
            pass  # Get random ship
        else:
            pass  # lookup ship from args

        await self._bot.say("```\n" + reply + "\n```")
        if link:
            await self._bot.say(link)

    @commands.command()
    async def more(self):
        """Gets more information from the last ?warship call."""
        try:
            reply = "```\n" + next(self._generator) + "\n```"
        except (StopIteration, TypeError):
            reply = (self._last_ship_url if self._last_ship_url else "?warship was not previously called.")
        await self._bot.say(reply)

    @commands.command()
    async def refresh(self):
        """Re-fetches cached data. Use sparingly."""
        self._ship_classes, self._ship_spec_table = webdata.get_warship_data(force_recache=True)
        await self._bot.say("Data refreshed.")

    @commands.command()
    async def json(self):
        """For debugging."""
        webdata.save_cache_to_json()
        await self._bot.say("Data saved to JSON file.")

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
