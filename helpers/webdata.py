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
    :return: Dict
    """

    # Todo: use JSON instead of object serialization
    try:
        with open("data\\cache.pkl", "rb") as file:
            data = pickle.load(file)
    except FileNotFoundError:
        data = {}

    return data


def _save_cache(classes, specifications):
    """
    :param classes: Dict
    :return: NoneType
    """

    with open("data\\cache.pkl", "wb") as file:
        data = {"classes": classes, "specifications": specifications}
        pickle.dump(data, file)


def get_warship_data(force_recache=False):
    """
    :param force_recache: Bool
    :return: Tuple of Dictionaries in form class_name:properties and specification:class_name
    """

    cache = _load_cache()
    if cache and cache.get("classes", None) and cache.get("specifications", None):
        classes = cache["classes"]
        specifications = cache["specifications"]
    else:
        classes = {}
        specifications = {}

    if force_recache:
        classes = {}
        specifications = {}

    if not classes and not specifications:  # if cache load fails or re-cache requested

        print("Generating ship class data...")

        page_name = "List of ship classes of World War II"
        data = urlopen(wikipedia.page(title=page_name).url)
        soup = BeautifulSoup(data, "html.parser")
        rows = soup.find("table", "wikitable").find_all("tr")

        for row in rows:

            # If row has no standard cells (only th cells), skip
            if not row.find("td"):
                continue

            columns = row.find_all("td")
            link = columns[0].find("a")

            # If link exists, is not "create new page" request,
            # and if link is not a section of a page
            if link and "?" not in link["href"] and "#" not in link["href"]:
                link_title = link["title"]  # Hoping the title is similar to the last part of url
            else:
                link_title = None

            # Scrap properties
            name = columns[0].get_text()
            ship_type = columns[1].get_text().capitalize()
            faction = columns[2].get_text()
            launch_years = columns[3].get_text()
            displacement = columns[4].get_text()
            number = columns[5].get_text()

            # Replace special unicode characters; stolen from https://stackoverflow.com/a/39612904
            # Still not enough to remove \u00a0 from factions, so manual it is
            # Todo: Observed: \u0142 (lowercase L with slash) not resolved
            name = ''.join((c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn'))
            ship_type = ''.join((c for c in unicodedata.normalize('NFD', ship_type) if unicodedata.category(c) != 'Mn'))
            faction = ''.join((c for c in unicodedata.normalize('NFD', faction) if unicodedata.category(c) !=
                               'Mn')).replace("\u00a0", "")

            # Modify name to remove subclasses and synonyms
            name = name.split("(")[0].split("=")[0].rstrip()

            # Find duplicates by link title (because multiple subclasses often point to same page)
            # Todo: calculate single year/displacement range instead of just concatenating values
            if link_title in classes:

                classes[link_title]["launch_years"] += "; " + launch_years
                classes[link_title]["displacement"] += "; " + displacement
                classes[link_title]["number"] += " + " + number

            else:

                # Manually fixing Wikipedia's errors, because we can't all be perfect
                if name == "Royal Sovereign":
                    continue
                # Todo: handle cases where field is empty; right now it just prints a blank
                classes[link_title] = {
                        "name": name,
                        "ship_type": ship_type,
                        "faction": faction,
                        "launch_years": launch_years,
                        "displacement": displacement + " tons",
                        "number": number + " (wartime/total built)",
                        "link_title": link_title
                        }

                # If type is not "other"
                if ship_type in constants.HULL_TYPES.values():
                    # Add ship type to specifications dictionary of sets
                    # Todo: deal with multi-nation ships and ambiguous hull classifications
                    if ship_type not in specifications:
                        specifications[ship_type] = set()
                    # Assumes no two distinct ships/classes will share same name
                    # Todo: this is a bad assumption; see rename_keys() as well
                    specifications[ship_type].add(name)
                else:
                    if "other" not in specifications:
                        specifications["other"] = set()
                    specifications["other"].add(name)

                # If faction is not "minor"
                if faction in constants.NATIONS.values():
                    # Add faction to specifications
                    if faction not in specifications:
                        specifications[faction] = set()
                    specifications[faction].add(name)
                else:
                    if "minor" not in specifications:
                        specifications["minor"] = set()
                    specifications["minor"].add(name)

        classes = rename_keys(classes)

        _save_cache(classes, specifications)
        print("Done.")

    return classes, specifications


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


def rename_keys(ships):
    """
    Convert keys from link/page titles to names
    :param ships: Dict
    :return: Dict
    """
    formatted_ships = {}  # In-place alteration of dict causes runtime error

    for link_name, properties in ships.items():
        # Assumes no two ships/classes will have the same name, which is probably a bad assumption
        formatted_ships[properties["name"]] = properties

    return formatted_ships


def save_cache_to_json():

    data = _load_cache()

    # Convert sets to lists
    temp = {}
    for category in data["specifications"].keys():
        for member in data["specifications"][category]:
            if category not in temp:
                temp[category] = []
            temp[category].append(member)

    modded_data = {"classes": data["classes"], "specifications": temp}
    with open("data\\data.json", "w") as file:
        json.dump(modded_data, file, indent=4)
