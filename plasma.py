import logging

import discord
from discord.ext import commands
import os

from helpers import classes


def main():

    # Initialize
    set_logging()
    description = "A generator bot."
    prefix = "?"
    bot = commands.Bot(command_prefix=prefix, description=description)
    playing_message = 'on {delimiter}help'.format(delimiter=prefix)

    @bot.event
    async def on_ready():
        print("Logged in as")
        print(bot.user.name)
        print(bot.user.id)
        print("---")
        await bot.change_presence(game=discord.Game(name=playing_message))

    # Remove default help
    bot.remove_command("help")

    # Add commands
    categories = (classes.Basic, classes.Web)
    for category in categories:
        bot.add_cog(category(bot))

    # Start bot
    bot.run(os.environ["DISCORD_TOKEN"])


def set_logging():

    # Copied from the docs
    logger = logging.getLogger("discord")
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename="data\\bot.log", encoding="utf-8", mode="w")
    text = "%(asctime)s:%(levelname)s:%(name)s: %(message)s"
    handler.setFormatter(logging.Formatter(text))
    logger.addHandler(handler)

main()
