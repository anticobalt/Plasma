"""
Generalized functions for scrapping Wikipedia.
"""

from bs4 import BeautifulSoup
from urllib.parse import quote
from urllib.request import urlopen

WIKI_ROOT = "https://en.wikipedia.org/wiki/"


def get_article_summary(title):
    """
    Manually scraps summaries, as wikipedia.py sometimes fails lookup of pages with hyphens in title.
    :param title: Str
    :return: Str
    """

    url = WIKI_ROOT + quote(title.replace(" ", "_"))  # Quote fixes unicode errors
    data = urlopen(url)
    soup = BeautifulSoup(data, "html.parser")
    return soup.body.p.get_text() + " [m]"


def get_article_first_image(title):
    """
    Manually get first image of page.
    :param title: Str
    :return: Str
    """

    try:
        url = WIKI_ROOT + quote(title.replace(" ", "_"))  # Quote fixes unicode errors
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
