from bs4 import BeautifulSoup
import pickle
from urllib.parse import quote
from urllib.request import urlopen
import wikipedia


def _load_cache():
    """
    :return: Dict
    """

    try:
        with open("data\\cache.pkl", "rb") as file:
            data = pickle.load(file)
    except FileNotFoundError:
        data = {}

    return data


def _save_cache(classes):
    """
    :param classes: List
    :return: NoneType
    """

    with open("data\\cache.pkl", "wb") as file:
        data = {"warships": classes}
        pickle.dump(data, file)


def get_warship_classes(force_recache=False):
    """
    :param force_recache: Bool
    :return: List of Dictionaries
    """

    cache = _load_cache()
    if cache and cache.get("warships", None):
        classes = cache["warships"]
    else:
        classes = []

    if not classes or force_recache:

        classes = []  # for force recache

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
                page_title = link["title"]  # Hoping the title is similar to the last part of url
            else:
                page_title = None

            name = columns[0].get_text()
            ship_type = columns[1].get_text().capitalize()
            faction = columns[2].get_text()
            launch_years = columns[3].get_text()
            displacement = columns[4].get_text()
            number = columns[5].get_text()

            classes.append(
                {
                    "name": name,
                    "ship_type": ship_type,
                    "faction": faction,
                    "launch_years": launch_years,
                    "displacement": displacement + " tons",
                    "number": number + " (wartime/total built)",
                    "page_title": page_title
                }
            )

        _save_cache(classes)
        print("Done.")

    return classes


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
