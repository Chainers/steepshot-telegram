import datetime
import logging
import os

from peewee import *
from playhouse.db_url import connect

from steepshot_bot import settings
from steepshot_bot.utils import Object

logger = logging.getLogger(__name__)
db = None


def get_db():
    global db

    if db:
        return db

    try:
        if settings.DEBUG:
            logger.info('Connecting to SQLite database.')
            db = connect(settings.SQLITE_DATABASE_URL)
        else:
            logger.info('Connecting to PostgreSQL database.')
            db = connect(os.getenv('DATABASE_URL', ''))

        return db
    except OperationalError as e:
        logger.error('Failed to connect to database: %s', e)
        raise ConnectionError


class User(Model):
    id = IntegerField(index=True, unique=True, primary_key=True)
    name = CharField(default='')
    chat_id = IntegerField(default=-1)
    wif_message_id = IntegerField(default=-1)
    last_action_time = DateTimeField(default=datetime.datetime.now)
    last_login_time = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = get_db()

    def get_wif_msg(self):
        return Object(chat=Object(id=self.chat_id), message_id=self.wif_message_id)


class Post(Model):
    chat_id = IntegerField(default=-1)
    message_id = IntegerField(default=-1)
    identifier = CharField(default='')

    class Meta:
        database = get_db()
