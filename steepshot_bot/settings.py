import os

PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

DEBUG = os.getenv('DEBUG') == 'True'

USE_WEBSOCKET_NODES = True

STEEM_NODES = (
    ('https://api.steemit.com', 'https://steemd.steemitstage.com', 'https://steemd2.steepshot.org'),
    ('wss://steemd.steemitstage.com', 'wss://steemd2.steepshot.org', 'wss://steemd-int.steemit.com')
)[USE_WEBSOCKET_NODES]

STEEPSHOT_API = 'https://steepshot.org/api'
if DEBUG:
    STEEPSHOT_API = 'https://qa.steepshot.org/api'

WEBHOOK_HOST = '<enter-you-domain-name>'  # IP/host where the bot is running

WEBHOOK_URL_BASE = 'https://%s:%s' % (WEBHOOK_HOST, 443)
WEBHOOK_URL_PATH = '/%s/' % TELEGRAM_BOT_TOKEN

DATA_PATH = os.path.join(os.path.dirname(PROJECT_PATH), 'data')
SQLITE_DATABASE_URL = 'sqlite:///' + os.path.join(DATA_PATH, 'users.db')

POST_BASE_URL = 'https://alpha.steepshot.io/post'

LOGGER_CONF = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s (%(filename)s:%(lineno)d %(threadName)s) %(levelname)s - %(name)s: "%(message)s"'
        }
    },

    'handlers': {
        'stream': {
            'class': "logging.StreamHandler",
            'level': 'DEBUG',
            'formatter': 'simple'
        }
    },

    'root': {
        'level': 'INFO',
        'handlers': ['stream']
    }
}
