"""
Commands and functions related to the warship Discord command.
"""

import random
from discord.ext import commands
from bs4 import BeautifulSoup
from urllib.request import urlopen
import wikipedia
import pickle
import json
import unicodedata

from helpers import text_manipulation, wiki

# TODO: remove redundant hull type constants
NATIONS = {
    "usn": "United States Navy",
    "km": "Kriegsmarine",
    "rm": "Regia Marina",
    "ijn": "Imperial Japanese Navy",
    "fn": "French Navy",
    "rn": "Royal Navy",
    "minor": "minor"
}
HULL_TYPES = {
    "cv": "aircraft carriers",
    "bb": "battleships",
}
TYPE_NAMES = ["battleships", "aircraft carriers"]


def get_warship_data():
    """
    Returns the cache of warship data.
    :return: Tuple of Dicts
    """

    cache = load_cache()

    if cache:
        ships = cache[0]
        ships_by_type = cache[1]
        ships_by_nation = cache[2]
    else:
        ships, ships_by_type, ships_by_nation = generate_warship_cache()

    return ships, ships_by_type, ships_by_nation


def generate_warship_cache():
    """
    Fetches data and saves to cache.
    :return: Three Dicts
    """
    print("Generating ship data...")
    ships = {}
    ships_by_nation = {}
    ships_by_type = {}

    for nation in NATIONS.values():
        ships_by_nation[nation] = []

    for _type in TYPE_NAMES:

        page_name = "List of {} of World War II".format(_type)
        ships_of_type, nation_partial_dict = scrap_wiki_table_by_type(page_name, ships)
        ships_by_type[_type] = ships_of_type

        # Update nation lists
        for nation, array in nation_partial_dict.items():
            ships_by_nation[nation].extend(array)

        print(_type + " is done.")

    save_cache(ships, ships_by_type, ships_by_nation)
    print("Done.")
    return ships, ships_by_type, ships_by_nation


def load_cache():
    """
    :return: Tuple of Dicts
    """

    # Todo: use JSON instead of object serialization
    try:
        with open("data\\cache.pkl", "rb") as file:
            data = pickle.load(file)
        r = (data["ships"], data["types"], data["nations"])
    except FileNotFoundError:
        r = ({}, {}, {})

    return r


def save_cache(ships, types, nations):
    """
    :param ships: Dict
    :param types: Dict
    :param nations: Dict
    :return: NoneType
    """

    with open("data\\cache.pkl", "wb") as file:
        data = {"ships": ships, "types": types, "nations": nations}
        pickle.dump(data, file)


def save_cache_to_json():

    data = load_cache()
    ships, types, nations = data

    s = {
        "ships": ships,
        "types": types,
        "nations": nations
    }

    with open("data\\data.json", "w") as file:
        json.dump(s, file, indent=4)


def scrap_wiki_table_by_type(page_name, ships):
    """
    Given name of Wikipedia page with "Ships of World War II" template, scrap table for ships, and generate
        a) a list of the names of the ships belonging to the type defined by the page
        b) a dictionary of nations (each nation holding a list of ship encountered that belong to the nation)
    and add encountered ships to the dictionary of ships.

    :param page_name: Str ; the title of the Wikipedia page
    :param ships: Dict in form {ship:{property:value}}
    :return: Tuple in form (list, dict) ; dict = {nation:[ship]}
    """

    # Initialize
    ships_of_type = []
    nations_encountered = {}
    for nation in NATIONS.values():
        nations_encountered[nation] = []

    # Get soup
    # TODO: stop using wikipedia library, it's redundant
    data = urlopen(wikipedia.page(title=page_name).url)
    soup = BeautifulSoup(data, "html.parser")
    rows = soup.find("table", "wikitable").find_all("tr")
    for row in rows:

        # If row only has headers (i.e. only th cells), skip
        if not row.find("td"):
            continue

        try:
            ship = process_row(row)
        except IndexError:
            # the row is incorrectly formatted
            continue

        # Add ship to ship dictionary
        # Todo: handle cases where field is empty; right now it just prints a blank
        ships[ship["name"]] = {
            "class": ship["class"],
            "country": ship["country"],
            "type": ship["type"],
            "commissioned": ship["commissioned"],
            "displacement": ship["displacement"] + " tons",
            "fate": ship["fate"],
            "link title": ship["link title"]
        }

        ships_of_type.append(ship["name"])

        # Add ship to nation if it belongs to a major nation, else add to nation "minor"
        if ship["country"] in NATIONS.values():
            nations_encountered[ship["country"]].append(ship["name"])
        else:
            if "minor" not in nations_encountered:
                nations_encountered["minor"] = []
            nations_encountered["minor"].append(ship["name"])

    return ships_of_type, nations_encountered


def process_row(row):
    """
    Extracts and prettifies row data.
    :param row: BeautifulSoup
    :return: Dict
    """

    columns = row.find_all("td")
    link = columns[0].find("a")

    # If link exists, is not "create new page" request, and is not a section of another page,
    #   then save it. Otherwise, no link.
    if link and "?" not in link["href"] and "#" not in link["href"]:
        link_title = link["title"]  # Hoping the title is similar to the last part of url
    else:
        link_title = None

    # Scrap properties
    name = columns[0].get_text()
    country = columns[1].get_text()
    _class = columns[2].get_text()
    _type = columns[3].get_text()
    displacement = columns[4].get_text()
    commissioned = columns[5].get_text()
    fate = columns[6].get_text().capitalize()

    # Replace special unicode characters; stolen from https://stackoverflow.com/a/39612904.
    # Still not enough to remove \u00a0 from countries, so manual it is.
    # Todo: Observed: \u0142 (lowercase L with slash) not resolved
    problem_strings = [name, _class, country, fate]
    resolved_version = {name: "", _class: "", country: "", fate: ""}
    for string in problem_strings:
        new_string = ''.join((c for c in unicodedata.normalize('NFD', string) if unicodedata.category(c) !=
                              'Mn')).replace("\u00a0", "")
        resolved_version[string] = new_string

    name = resolved_version[name]
    country = resolved_version[country]
    _class = resolved_version[_class]
    fate = resolved_version[fate]

    # Modify class to remove subclasses and synonyms
    _class = _class.split("(")[0].split("=")[0].rstrip()

    return {"name": name, "class": _class, "country": country, "type": _type, "commissioned": commissioned,
            "displacement": displacement, "fate": fate, "link title": link_title}


class Warship:

    def __init__(self, bot):
        self._bot = bot

        self._wikipedia_root = "https://en.wikipedia.org/wiki/"
        self._cached = False
        self._ship_table = {}
        self._ship_nation_table = {}
        self._ship_type_table = {}
        self._generator = None
        self._last_ship_url = ""

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
            nation = random.choice(list(NATIONS.values()))
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
                image_link = wiki.get_article_first_image(title)

            # If page load fails, do it yourself
            except wikipedia.exceptions.PageError:
                raw_summary = wiki.get_article_summary(title)
                image_link = wiki.get_article_first_image(title)

            # Set generator so that paragraphs can be yielded if called by self.more()
            self._generator = text_manipulation.text_generator(raw_summary)
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
        Gets a random WW2-era warship via Wikipedia.
        Under construction.
        -s to search by hull type or country.
        """

        ship = {}
        name = ""
        arg_error = False

        # Get cache if don't have it yet
        if not self._cached:
            self._ship_table, self._ship_type_table, self._ship_nation_table = get_warship_data()

        args = str_args.split(" ")
        if not str_args:
            name, ship = self._get_random_ship(table="", key="")
        else:
            if args[0] == "-n":
                try:
                    nation = NATIONS[args[1].lower()]
                except KeyError:
                    arg_error = True
                else:
                    name, ship = self._get_random_ship(table="nation", key=nation)
            elif args[0] == "-t":
                try:
                    _type = HULL_TYPES[args[1].lower()]
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
        self._ship_table, self._ship_type_table, self._ship_nation_table = generate_warship_cache()
        await self._bot.say("Data refreshed.")

    @commands.command()
    async def json(self):
        """For debugging."""
        save_cache_to_json()
        await self._bot.say("Data saved to JSON file.")
