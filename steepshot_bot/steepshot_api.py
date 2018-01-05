import json
import logging

import requests
from requests.exceptions import RequestException

from steepshot_bot import settings
from steepshot_bot.exceptions import SteepshotServerError
from steepshot_bot.steem import get_signed_transaction

logger = logging.getLogger(__name__)


API_URLS = {
    'posts_recent': settings.STEEPSHOT_API + '/v1_1/recent',
    'posts_new': settings.STEEPSHOT_API + '/v1_1/posts/new',
    'posts_hot': settings.STEEPSHOT_API + '/v1_1/posts/hot',
    'posts_top': settings.STEEPSHOT_API + '/v1_1/posts/top',
    'post_prepare': settings.STEEPSHOT_API + '/v1/post/prepare',
    'log_post': settings.STEEPSHOT_API + '/v1/log/post',
    'log_upvote': settings.STEEPSHOT_API + '/v1/log/post/%s/upvote'
}


def get_recent_posts(username: str) -> list:
    try:
        return requests.get(API_URLS['posts_recent'], params={'username': username}).json().get('results', [])
    except RequestException as error:
        logger.error('Failed to retrieve data from api: {error}'.format(error=error))
        return []


def get_new_posts(username: str) -> list:
    try:
        return requests.get(API_URLS['posts_new'], params={'username': username}).json().get('results', [])
    except RequestException as error:
        logger.error('Failed to retrieve data from api: {error}'.format(error=error))
        return []


def get_hot_posts(username: str) -> list:
    try:
        return requests.get(API_URLS['posts_hot'], params={'username': username}).json().get('results', [])
    except RequestException as error:
        logger.error('Failed to retrieve data from api: {error}'.format(error=error))
        return []


def get_top_posts(username: str) -> list:
    try:
        return requests.get(API_URLS['posts_top'], params={'username': username}).json().get('results', [])
    except RequestException as error:
        logger.error('Failed to retrieve data from api: {error}'.format(error=error))
        return []


def post_prepare(photo, title: str, username: str, tags: list = None):
    try:
        trx = get_signed_transaction(username)
        files = {'photo': photo}
        payload = [
            ('title', title),
            ('username', username),
            ('trx', json.dumps(trx.json()))
        ]
        if tags:
            for tag in tags:
                payload.append(('tags', tag))
        resp = requests.post(API_URLS['post_prepare'], data=payload, files=files)
        return resp.json()
    except RequestException as e:
        logger.error('Failed to retrieve data from api: %s', e)
        return {}


def log_new_post(username: str, error_occured: str = None):
    try:
        payload = {
            'username': username,
            'error': error_occured
        }
        return requests.post(API_URLS['log_post'], data=payload).json()
    except RequestException as error:
        logger.error('Failed to retrieve data from api: {error}'.format(error=error))
        return []


def log_upvote_post(identifier: str, username: str, error_occured: str = None):
    try:
        payload = {
            'username': username,
            'error': error_occured
        }
        return requests.post(API_URLS['log_upvote'] % identifier, data=payload).json()
    except RequestException as error:
        logger.error('Failed to retrieve data from api: {error}'.format(error=error))
        raise SteepshotServerError(error)
