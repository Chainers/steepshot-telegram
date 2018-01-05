import re
import string


class Object(object):
    def __init__(self, **kwargs):
        for kw in kwargs:
            setattr(self, kw, kwargs[kw])


def construct_identifier(author: str, permlink: str):
    return '@{}/{}'.format(author, permlink)


def parse_hashtags(title_raw: str):
    """
    Parse tags from title. Tags from the end of the title will be remove.
    For example: Title "Hello, #this is my first post #photo #test, #lol"
    will be return ('Hello, #this is my first post', ['this', 'photo', 'test', 'lol'])
    """
    literals = title_raw.split()
    tags = []
    title_words = []
    tag_from_end = literals[-1].startswith('#')
    for literal in literals[::-1]:
        if literal.startswith('#'):
            tags = [literal.strip(string.punctuation + string.whitespace)] + tags
        else:
            tag_from_end = False

        if not tag_from_end:
            title_words = [literal] + title_words
    return ' '.join(title_words), tags


def resolve_identifier(url):
    author, permlink = re.findall('@([\w\.-]+)/(.+)', url)[0]
    return construct_identifier(author, permlink)
