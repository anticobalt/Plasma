from bs4 import BeautifulSoup
import pickle
from urllib.parse import quote
from urllib.request import urlopen
import wikipedia
import json
import unicodedata

from helpers import constants


def _load_cache():
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


def _save_cache(ships, types, nations):
    """
    :param ships: Dict
    :param types: Dict
    :param nations: Dict
    :return: NoneType
    """

    with open("data\\cache.pkl", "wb") as file:
        data = {"ships": ships, "types": types, "nations": nations}
        pickle.dump(data, file)


def get_warship_data():
    """
    Returns the cache of warship data.
    :return: Tuple of Dicts
    """

    cache = _load_cache()

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
    print("Generating ship class data...")
    ships = {}
    ships_by_nation = {}
    ships_by_type = {}

    for nation in constants.NATIONS.values():
        ships_by_nation[nation] = []

    for _type in constants.TYPE_NAMES:

        page_name = "List of {} of World War II".format(_type)
        ships_of_type, nation_partial_dict = scrap_wiki_table_by_type(page_name, ships)
        ships_by_type[_type] = ships_of_type

        # Update nation lists
        for nation, array in nation_partial_dict.items():
            ships_by_nation[nation].extend(array)

        print(_type + " is done.")

    _save_cache(ships, ships_by_type, ships_by_nation)
    print("Done.")
    return ships, ships_by_type, ships_by_nation


def get_wikipedia_summary(wiki_root, title):
    """
    Manually scraps summaries, as wikipedia.py sometimes fails lookup of pages with hyphens in title.
    :param title: Str
    :return: Str
    """

    url = wiki_root + quote(title.replace(" ", "_"))  # Quote fixes unicode errors
    data = urlopen(url)
    soup = BeautifulSoup(data, "html.parser")
    return soup.body.p.get_text() + " [m]"


def get_wikipedia_first_image(wiki_root, title):
    """
    Manually get first image of page.
    :param title: Str
    :return: Str
    """

    try:
        url = wiki_root + quote(title.replace(" ", "_"))  # Quote fixes unicode errors
        data = urlopen(url)
        soup = BeautifulSoup(data, "html.parser")
        img = soup.find("table", "infobox").find("img")

    # If infobox doesn't exist
    except AttributeError:
        img_url = ""

    # I saw an encoding error of sorts *once*, and haven't been able to reproduce it
    except Exception as e:
        img_url = "\n\n```Unexpected error occurred while trying to load image.\n{e}```".format(e=e)

    else:
        # Assume all important images (e.g. not logos) have alt attributes
        if img["alt"] != "":
            partial_img_url = img.get("src")
            a = partial_img_url.split("/")

            # If image is a thumbnail
            if "thumb" in a:
                a.remove("thumb")
                a = a[:-1]

            partial_img_url = "/".join(a)
            img_url = "https:" + partial_img_url

        else:
            img_url = ""

    return img_url


def save_cache_to_json():

    data = _load_cache()
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
    for nation in constants.NATIONS.values():
        nations_encountered[nation] = []

    # Get soup
    # TODO: stop using wikipedia library, it's redundant
    data = urlopen(wikipedia.page(title=page_name).url)
    soup = BeautifulSoup(data, "html.parser")
    rows = soup.find("table", "wikitable").find_all("tr")
    n=0
    for row in rows:

        # If row only has headers (i.e. only th cells), skip
        if not row.find("td"):
            continue

        try:
            ship = process_row(row)
        except IndexError:
            # the row is incorrectly formatted
            continue

        print(n)
        n+=1
        print(ship["name"])

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
        if ship["country"] in constants.NATIONS.values():
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
