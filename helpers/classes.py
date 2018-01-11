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
                "**Commands:**\n"
                "```\n"
                "{d}coin: flips a coin\n"
                "{d}dice: rolls a dice\n"
                "{d}choose <option 1> <option 2> <etc>: randomly picks from list\n"
                "{d}int <optional min> <optional max>: randomly picks integer from range, default 1-10\n\n"
                "{d}reddit <subreddit name>: gets random hot submission from subreddit\n"
                "{d}warship <optional specification>: under construction\n"
                "{d}more: loads more information from last `{d}warship` call\n"
                "{d}refresh: reloads warship database; use sparingly\n\n"
                "{d}help: displays this list\n"
                "{d}help <command>: displays detailed information about a command"
                "```"
            ).format(d=delimiter)
        elif command == "warship":
            s = (
                "```\n"
                "Gets a random WW2-era warship class via Wikipedia.\n"
                "Use -n to specify a navy/nation, -t to specify a hull type.\n"
                "Enter a name to look a ship up.\n"
                "Leave it blank to get totally random ship.\n"
                "\n"
                "Navies: IJN, USN, KM, RN, RM, FN, minor\n"
                "Hull types CV, CA, CL, DD, BB, SS, other\n"
                "\n"
                "IJN = Imperial Japanese Navy\n"
                "USN = United States Navy\n"
                "KM = Kriegsmarine (Nazi Germany)\n"
                "RN = Royal Navy (Britain)\n"
                "RM = Regia Marina (Kingdom of Italy)\n"
                "FN = French Navy\n"
                "\n"
                "CV = Aircraft Carrier\n"
                "CA = Heavy Cruiser\n"
                "CL = Light Cruiser\n"
                "DD = Destroyer\n"
                "BB = Battleship\n"
                "SS = Submarine\n"
                "\n"
                "CAs, CLs, and SSs are currently broken.\n"
                "```\n"
                "Example: `{d}warship -t cv` to get an aircraft carrier or `{d}warship -n rn` to get a British ship.\n"
                "`{d}warship` to get a random ship, or `{d}warship Ark Royal` to look up the Ark Royal."
            ).format(d=delimiter)
        else:
            s = "Doesn't get any more detailed than what's listed in `{d}help`, kiddo.".format(d=delimiter)

        await self._bot.say(s)


class Web:
    """Gets data from various online sources."""

    def __init__(self, bot):
        self._bot = bot
        self._reddit = None

        self._wikipedia_root = "https://en.wikipedia.org/wiki/"
        self._cached = False
        self._ship_table = {}
        self._ship_nation_table = {}
        self._ship_type_table = {}
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

    def _get_random_ship(self, table, key):
        """
        Get random ship based on specifications.
        If nothing specified, choose random nation then choose random ship from nation.

        :param table: Str; name of table to look in (i.e. nation or type)
        :param key: Str; which key in table to look in
        :return: String and Dict of properties
        """

        choice = {}
        choice_name = ""

        if not table and not key:
            nation = random.choice(list(constants.NATIONS.values()))
            ships_of_nation = self._ship_nation_table[nation]
            choice_name = random.choice(ships_of_nation)
            choice = self._ship_table[choice_name]

        if table == "nation":
            ships_of_nation = self._ship_nation_table[key]
            choice_name = random.choice(ships_of_nation)
            choice = self._ship_table[choice_name]
        elif table == "type":
            ships_of_type = self._ship_type_table[key]
            choice_name = random.choice(ships_of_type)
            choice = self._ship_table[choice_name]

        return choice_name, choice

    def _get_ship(self, name):
        """
        Get ship by name.
        :param name: String
        :return: Dict of ship properties.
        """
        # Todo: Implement fuzzy searching (e.g. Search for 'Bismark' failed. Did you mean 'Bismarck'?)
        try:
            ship = self._ship_table[name]
        except KeyError:
            return {}
        else:
            return ship

    def _generate_ship_reply(self, name, ship):
        """
        Create discord response.
        :param name: String, name of the ship
        :param ship: Dict, properties of the ship
        :return: Two strings: one for text blurb, one for image url
        """

        image_link = ""

        # Get summary if page exists
        if ship["link title"]:

            title = ship["link title"]

            # Try to get summary and image via wikipedia.py
            try:
                page = wikipedia.page(title=title)
                raw_summary = page.summary
                image_link = webdata.get_wikipedia_first_image(self._wikipedia_root, title)

            # If page load fails, do it yourself
            except wikipedia.exceptions.PageError:
                raw_summary = webdata.get_wikipedia_summary(self._wikipedia_root, title)
                image_link = webdata.get_wikipedia_first_image(self._wikipedia_root, title)

            # Set generator so that paragraphs can be yielded if called by self.more()
            self._generator = self._text_generator(raw_summary)
            summary = "\n\n" + next(self._generator)
            self._last_ship_url = self._wikipedia_root + title.replace(" ", "_")

        else:
            summary = ""
            self._last_ship_url = "No Wikipedia article for this ship exists."

        blurb = "Name: {name}\n" \
                "Class: {_class}\n" \
                "Type: {ship_type}\n" \
                "Navy: {navy}\n" \
                "Displacement: {displacement}\n" \
                "Commissioned: {commissioned}\n" \
                "Fate: {fate}" \
                "{summary}".format(name=name,
                                   _class=ship["class"],
                                   ship_type=ship["type"].title(),
                                   navy=ship["country"],
                                   displacement=ship["displacement"],
                                   commissioned=ship["commissioned"],
                                   fate=ship["fate"].title(),  # wikipedia, why are all the months lowercase
                                   summary=summary)

        return blurb, image_link

    @commands.command()
    async def warship(self, *, str_args: str = ""):
        """
        Gets a random WW2-era warship class via Wikipedia.
        Under construction.
        -s to search by hull type or country.
        """

        ship = {}
        name = ""
        arg_error = False

        # Get cache if don't have it yet
        if not self._cached:
            self._ship_table, self._ship_type_table, self._ship_nation_table = webdata.get_warship_data()

        args = str_args.split(" ")
        if not str_args:
            name, ship = self._get_random_ship(table="", key="")
        else:
            if args[0] == "-n":
                try:
                    nation = constants.NATIONS[args[1].lower()]
                except KeyError:
                    arg_error = True
                else:
                    name, ship = self._get_random_ship(table="nation", key=nation)
            elif args[0] == "-t":
                try:
                    _type = constants.HULL_TYPES[args[1].lower()]
                except KeyError:
                    arg_error = True
                else:
                    name, ship = self._get_random_ship(table="type", key=_type)
            else:
                if "-" in args[0]:
                    # Avoid searching if obvious typo present
                    arg_error = True
                else:
                    name = " ".join(args).title()
                    ship = self._get_ship(name)

        if arg_error:
            await self._bot.say("Invalid specification. Try again.")
        else:
            if ship:
                # If no ship by now, user entered something wrong
                text, image_link = self._generate_ship_reply(name, ship)
                await self._bot.say("```\n" + text + "\n```")
                if image_link:
                    await self._bot.say(image_link)
            else:
                await self._bot.say("No warship was found. Check arguments and/or spelling.")

    @commands.command()
    async def more(self):
        """Gets more information from the last ?warship call."""
        try:
            reply = "```\n" + next(self._generator) + "\n```"
        except (StopIteration, TypeError):
            if self._last_ship_url:
                reply = "Read more online!\n\n" + self._last_ship_url
            else:
                reply = "A warship was not previously generated, so there's nothing to get."
        await self._bot.say(reply)

    @commands.command()
    async def refresh(self):
        """Re-fetches cached data. Use sparingly."""
        self._ship_table, self._ship_type_table, self._ship_nation_table = webdata.generate_warship_cache()
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
