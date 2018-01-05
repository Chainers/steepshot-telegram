import os

HOST = '<enter-ip-of-your-host>'
SSH_PORT = '22'

CURRENT_HOST = '<enter-you-domain-name>'

REPOSITORY = 'https://github.com/Chainers/steepshot-telegram.git'
PROJECT_NAME = 'steepshotbot'

DEPLOYMENT_USER = 'steepshotbot'
DEPLOYMENT_GROUP = 'steepshotbot'

REMOTE_DEPLOY_DIR = os.path.join('/home', DEPLOYMENT_USER)
USER_PROFILE_FILE = os.path.join(REMOTE_DEPLOY_DIR, '.profile')
DEPLOY_DIR = os.path.join(REMOTE_DEPLOY_DIR, PROJECT_NAME)

LOCAL_CONF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conf_templates')
FLASK_APP = os.path.join(DEPLOY_DIR, 'steepshot_bot', 'main.py')

UBUNTU_PACKAGES = [
    'git',
    'python-pip',
    'python3-pip',
    'python3-dev',
    'nginx',
    'python3.5',
    'python-certbot-nginx',
    'postgresql',
    'postgresql-contrib',
]

WORKON_HOME = os.path.join(REMOTE_DEPLOY_DIR, '.virtualenvs')
ENVIRONMENT_NAME = PROJECT_NAME
VENV_BIN_DIR = os.path.join(WORKON_HOME, ENVIRONMENT_NAME, 'bin')
VENV_ACTIVATE = os.path.join(VENV_BIN_DIR, 'activate')
ENVIRONMENT_PATH = os.path.join(WORKON_HOME, ENVIRONMENT_NAME)

DB_HOST = 'localhost'
DB_PORT = 5432
DB_USER = PROJECT_NAME
DB_PASSWORD = '<enter-your-db-password>'
DB_NAME = PROJECT_NAME

NGINX_SERVICE = 'nginx.service'
STEEPSHOTBOT_SERVICE = 'steepshot_bot.service'

GUNI_HOST = '127.0.0.1'
GUNI_PORT = 8001
GUNI_WORKERS = 1

GUNI_TIMEOUT = 60
GUNI_GRACEFUL_TIMEOUT = 180

SETTINGS_MODULE = 'steepshot_bot.settings'

ENVIRONMENTS = {
    'PRODUCTION': {
        'HOST': HOST,
        'STEEPSHOTBOT_DOMAIN': CURRENT_HOST,
        'SSH_PORT': SSH_PORT,
        'GIT_BRANCH': 'master',
        'SETTINGS_MODULE': SETTINGS_MODULE,
        'IS_PRODUCTION': True,
        'IS_CERTBOT_CERT': True,
        'KEY_FILENAME': '~/.ssh/id_rsa',
    }
}

