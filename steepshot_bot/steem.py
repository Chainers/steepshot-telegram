import datetime
import logging

from steep import Steem
from steep.account import Account
from steep.instance import set_shared_steemd_instance, shared_steemd_instance
from steep.post import Post
from steep.utils import derive_permlink
from steepbase.exceptions import AccountDoesNotExistsException, InvalidWifError, PostDoesNotExist, \
    AlreadyVotedSimilarily

from steepshot_bot import settings
from steepshot_bot.db import User
from steepshot_bot.exceptions import SteemError, PostNotFound, VotedSimilarily
from steepshot_bot.utils import construct_identifier

logger = logging.getLogger(__name__)


def get_new_steem(nodes: list) -> Steem:
    steem = Steem(nodes=nodes)

    del (
        steem.commit.wallet.keyStorage,
        steem.commit.wallet.configStorage,
        steem.commit.wallet.MasterPassword,
    )
    steem.accounts = set()
    steem.__class__.__name__ = 'Steem'
    set_shared_steemd_instance(steem)
    return shared_steemd_instance()


steem_obj = get_new_steem(settings.STEEM_NODES)


def account_exists(username: str) -> bool:
    try:
        Account(username, steemd_instance=steem_obj)
        return True
    except AccountDoesNotExistsException as e:
        return False


def get_signed_transaction(username):
    username_to_follow = 'steepshot'
    steem_obj.commit.no_broadcast = True
    trx = steem_obj.commit.follow(username_to_follow, ['blog'], username)
    steem_obj.commit.no_broadcast = False
    return trx


def _add_posting_key(wif: str):
    logger.info('Adding local steem posting key')
    steem_obj.commit.wallet.setKeys(wif)


def _validate_posting_key(username: str):
    try:
        trx = get_signed_transaction(username)
        if not trx or not trx.get('signatures') or not steem_obj.verify_authority(trx):
            raise InvalidWifError()

        logger.info('Adding user to local steem accounts: %s', username)
        steem_obj.accounts.add(username)
    except Exception:
        raise InvalidWifError()


def login(username: str, wif: str):
    """
    Raises InvalidWifError
    """
    _add_posting_key(wif)
    _validate_posting_key(username)


def logout(user: User):
    a = Account(user.name, steemd_instance=steem_obj)
    posting_ppk = a['posting']['key_auths'][0][0]
    steem_obj.commit.wallet.keys.pop(posting_ppk, None)
    user.delete_instance()


def is_user_logged_in(username: str) -> bool:
    return username in steem_obj.accounts


def add_post_to_steem(data: dict) -> str:
    meta = data.pop('meta', {})
    # remove redundant info
    meta.pop('extensions', None)
    beneficiaries = data.pop('beneficiaries', None)
    payload = data.pop('payload', {})
    author = payload.pop('username', '')
    permlink = derive_permlink(payload.get('title') + ' ' + datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    try:
        steem_obj.commit.post(
            json_metadata=meta,
            author=author,
            self_vote=True,
            permlink=permlink,
            beneficiaries=beneficiaries,
            **payload
        )
        return construct_identifier(author, permlink)
    except Exception as e:
        logger.error('Failed to add post to Steem: %s', e)
        raise SteemError(e)


def upvote_post(identifier, username):
    try:
        p = Post(identifier, steemd_instance=steem_obj)
        p.upvote(voter=username)
    except PostDoesNotExist:
        raise PostNotFound('This post does not exists: "%s"' % identifier)
    except AlreadyVotedSimilarily:
        raise VotedSimilarily('Already voted similar way.')


def add_comment(identifier, username, message):
    try:
        p = Post(identifier, steemd_instance=steem_obj)
        p.reply(message, author=username)
    except PostDoesNotExist:
        raise PostNotFound('This post does not exists: "%s"' % identifier)
    except Exception as e:
        logger.error('Failed to leave a comment to Steem: %s', e)
        raise SteemError(e)
