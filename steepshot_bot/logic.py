from peewee import DoesNotExist

from steepshot_bot import steem, steepshot_api
from steepshot_bot.db import User
from steepshot_bot.exceptions import SteepshotServerError, SteemError
from steepshot_bot.utils import parse_hashtags


def post_to_steem(
        image_bytes: bytes,
        title_raw: str,
        username: str):
    title, tags = parse_hashtags(title_raw)
    data = steepshot_api.post_prepare(image_bytes, title, username, tags)
    if not data or 'payload' not in data:
        error_msg = ''
        if data:
            error_msg += ' '.join([v[0] for v in data.values()])
        else:
            error_msg = 'Failed to connect to Steepshot server'
        raise SteepshotServerError(error_msg)
    try:
        steem.add_post_to_steem(data)
        steepshot_api.log_new_post(username)
    except SteemError as e:
        steepshot_api.log_new_post(username, str(e))


def upvote(identifier, username):
    """raises (PostDoesNotExist, SteepshotServerError)"""
    steem.upvote_post(identifier, username)
    steepshot_api.log_upvote_post(identifier, username)


def is_authenticated(user_id):
    try:
        User.get(User.id == user_id)
        return True
    except DoesNotExist:
        return False
