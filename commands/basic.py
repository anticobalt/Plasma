'''
Rudimentary Discord commands.
'''


import random
from discord.ext import commands


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
                "{d}warship <optional specification>: looks up or gets random WW2-era ships\n"
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
                "DDs, CAs, CLs, and SSs are currently broken.\n"
                "```\n"
                "Example: `{d}warship -t cv` to get an aircraft carrier or `{d}warship -n rn` to get a British ship.\n"
                "`{d}warship` to get a random ship, or `{d}warship Ark Royal` to look up the Ark Royal."
            ).format(d=delimiter)
        else:
            s = "Doesn't get any more detailed than what's listed in `{d}help`, kiddo.".format(d=delimiter)

        await self._bot.say(s)
