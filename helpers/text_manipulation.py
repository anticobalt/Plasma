"""
Functions that modify strings for specific uses.
"""


def text_generator(text):
    """
    Generator for text separated into paragraphs (i.e. by newlines)
    :param text: Str
    :yield: Str
    """
    paragraphs = text.split("\n")
    for paragraph in paragraphs:
        yield paragraph


def codeblock(text):
    """
    Returns text in a Markdown-style code block
    :param text: Str
    :return: Str
    """
    return "```\n" + text + "\n```"
