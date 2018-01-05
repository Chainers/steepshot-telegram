import logging

from fabric.api import env, task, sudo, cd, settings, require, prefix
from fabric.contrib.files import upload_template, contains, append, exists

from deploy_settings import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _add_virtualenv_settings_to_profile(profile_file):
    if not exists(profile_file):
        logger.info("Creating user profile: {}".format(profile_file))

        sudo('touch %s' % profile_file,
             user=DEPLOYMENT_USER)

    lines_to_append = [
        'export WORKON_HOME={workon_home}'.format(workon_home=WORKON_HOME),
        'export PROJECT_HOME={remote_deploy_dir}'.format(remote_deploy_dir=REMOTE_DEPLOY_DIR),
        'export VIRTUALENVWRAPPER_PYTHON={python_path}'.format(python_path='/usr/bin/python3.5'),
        'source /usr/local/bin/virtualenvwrapper.sh',
    ]

    for line in lines_to_append:
        if not contains(profile_file, line):
            append(profile_file, '\n' + line,
                   use_sudo=True)

    sudo('chown {user}:{group} {file}'
         .format(user=DEPLOYMENT_USER,
                 group=DEPLOYMENT_GROUP,
                 file=profile_file))


def _load_environment(environment_name):
    logger.info('Loading environment...')

    if environment_name not in ENVIRONMENTS:
        raise ValueError("Incorrect environment name {env_name}".format(env_name=environment_name))

    _environment = ENVIRONMENTS[environment_name]

    user = input('Please enter user name for deploying: ')
    key_filename = input('Please enter path to ssh key file (By default: ~/.ssh/id_rsa): ')

    if not key_filename:
        key_filename = _environment.get('KEY_FILENAME')

    env.user = user
    env.hosts = ['{host}:{port}'.format(host=_environment.get('HOST', ''), port=_environment.get('SSH_PORT', ''))]
    env.branch = _environment.get('GIT_BRANCH')
    env.key_filename = key_filename
    env.settings_module = _environment.get('SETTINGS_MODULE')
    env.is_production = _environment.get('IS_PRODUCTION')
    env.is_certbot_cert = _environment.get('IS_CERTBOT_CERT')
    env.steepshotbot_domain = _environment.get('STEEPSHOTBOT_DOMAIN')


def _get_systemd_service_path(service_name):
    if not service_name.endswith(('.service', '.unit')):
        service_name += '.service'
    return '/etc/systemd/system/{}'.format(service_name)


def _is_systemd_service_running(service_name):
    with settings(warn_only=True):
        status_reply = sudo('systemctl --no-pager --full status %s'
                            % service_name)
        return 'inactive' not in status_reply


def _restart_systemd_service(service_name):
    with settings(warn_only=True):
        if _is_systemd_service_running(service_name):
            sudo('systemctl stop %s' % service_name, user='root')
        sudo('systemctl start %s' % service_name, user='root')


def _install_service(service_name, context):
    logger.info('Copying systemd services "{service_name}"'.format(service_name=service_name))
    remote_service = _get_systemd_service_path(service_name)
    local_template = os.path.join(LOCAL_CONF_DIR, service_name)
    if not os.path.exists(local_template):
        logger.error('Template "{local_template}" does not exist.'.format(local_template=local_template))
        raise ValueError()

    upload_template(local_template,
                    remote_service,
                    context=context,
                    use_sudo=True,
                    backup=False)

    sudo('chown root:root {remote_service}'.format(remote_service=remote_service))
    sudo('systemctl daemon-reload')
    sudo('systemctl enable {}'.format(service_name))

@task
def create_non_priveledged_user():
    require('user')
    logger.info('Creating non priveledged user: {user}'.format(user=DEPLOYMENT_USER))

    with settings(warn_only=True):
        sudo('adduser --disabled-login --gecos os {deployment_user}'.format(deployment_user=DEPLOYMENT_USER))
        sudo('addgroup {deployment_group}'.format(deployment_group=DEPLOYMENT_GROUP))
        sudo('adduser {user} {group}'.format(user=DEPLOYMENT_USER, group=DEPLOYMENT_GROUP))


@task
def install_system_packages():
    require('user')
    logger.info('Installing system packages...')

    with settings(warn_only=True):
        sudo('add-apt-repository ppa:fkrull/deadsnakes -y')

        if env.is_certbot_cert:
            sudo('add-apt-repository ppa:certbot/certbot -y')

        sudo('wget -q https://www.postgresql.org/media/keys/ACCC4CF8.asc -O - | sudo apt-key add -')
        sudo("""sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" > /etc/apt/sources.list.d/pgdg.list'""")

        sudo('apt-get update')
        sudo('apt-get -y --no-upgrade install %s' % ' '.join(UBUNTU_PACKAGES))


@task
def prepare_virtualenv():
    require('user')
    logger.info("Setting up the virtual environment.")

    with settings(warn_only=True):
        sudo('pip install virtualenv')
        sudo('pip install virtualenvwrapper')

    _add_virtualenv_settings_to_profile(USER_PROFILE_FILE)


@task
def create_postgresdb():
    """
    Create postgres database and dedicated user
    """
    logger.info("Setting the database.")

    with settings(warn_only=True):
        # Create database user
        with prefix("export PGPASSWORD=%s" % DB_PASSWORD):
            sudo('psql -c "CREATE ROLE %s WITH CREATEDB CREATEUSER LOGIN ENCRYPTED PASSWORD \'%s\';"' % (DB_USER,
                                                                                                         DB_PASSWORD),
                 user='postgres')
            sudo('psql -c "CREATE DATABASE %s WITH OWNER %s"' % (DB_NAME, DB_USER),
                 user='postgres')


@task
def clearing_project_directory():
    require('is_production')

    with cd(REMOTE_DEPLOY_DIR), settings(warn_only=True):
        if exists(PROJECT_NAME, use_sudo=True):
            sudo('rm -rf {project_dir}'.format(project_dir=PROJECT_NAME))


@task
def checkout_repository():
    require('is_production')

    with cd(REMOTE_DEPLOY_DIR), settings(sudo_user=DEPLOYMENT_USER):
        if not exists(PROJECT_NAME, use_sudo=True):
            sudo('git clone %s %s' % (REPOSITORY, PROJECT_NAME))
            sudo('chown -R {user}:{group} {dir}'.format(
                user=DEPLOYMENT_USER,
                group=DEPLOYMENT_GROUP,
                dir=PROJECT_NAME
            ))


@task
def create_deploy_dirs(remote_conf_path):
    with cd(DEPLOY_DIR):
        sudo('mkdir -p logs', user=DEPLOYMENT_USER)
        sudo('chown -R {user}:{group} logs/'.format(user=DEPLOYMENT_USER,
                                                    group=DEPLOYMENT_GROUP))

        sudo('mkdir -p {remote_conf_path}'.format(remote_conf_path=remote_conf_path),
             user=DEPLOYMENT_USER)
        sudo('chown -R {user}:{group} {remote_conf_path}'.format(user=DEPLOYMENT_USER,
                                                                 group=DEPLOYMENT_GROUP,
                                                                 remote_conf_path=remote_conf_path))


@task
def deploy_files():
    require('branch')

    with cd(DEPLOY_DIR), settings(sudo_user=DEPLOYMENT_USER):
        sudo('git fetch')
        sudo('git reset --hard')
        sudo('git checkout {}'.format(env.branch))
        sudo('git pull origin {}'.format(env.branch))


@task
def config_nginx():

    if exists('/etc/nginx/sites-available/default'):
        with settings(warn_only=True):
            sudo('rm /etc/nginx/sites-available/default')

    remote_sa_path = '/etc/nginx/sites-available/{project_name}.conf'.format(project_name=PROJECT_NAME)

    context = {
        'HOST': HOST,
        'CURRENT_HOST': CURRENT_HOST,
        'DEPLOY_DIR': DEPLOY_DIR,
        'GUNI_HOST': GUNI_HOST,
        'GUNI_PORT': GUNI_PORT
    }

    upload_template(template_dir=LOCAL_CONF_DIR,
                    filename='nginx.conf.j2',
                    destination=remote_sa_path,
                    context=context,
                    backup=False,
                    mode=0o0644,
                    use_sudo=True,
                    use_jinja=True)

    sudo('chown root:root {remote_sa_path}'.format(remote_sa_path=remote_sa_path))
    sudo('ln -sf %s /etc/nginx/sites-enabled' % remote_sa_path)


@task
def config_gunicorn(remote_conf_path):
    context = {
        'DEPLOY_DIR': DEPLOY_DIR,
        'ENV_PATH': ENVIRONMENT_PATH,
        'GUNI_HOST': GUNI_HOST,
        'GUNI_PORT': GUNI_PORT,
        'GUNI_WORKERS': GUNI_WORKERS,
        'GUNI_TIMEOUT': GUNI_TIMEOUT,
        'GUNI_GRACEFUL_TIMEOUT': GUNI_GRACEFUL_TIMEOUT,
        'USER': DEPLOYMENT_USER,
        'GROUP': DEPLOYMENT_GROUP
    }

    upload_template(os.path.join(LOCAL_CONF_DIR, 'gunicorn.sh'),
                    remote_conf_path,
                    context=context,
                    backup=False,
                    mode=0o0750,
                    use_sudo=True)

    sudo('chown {user}:{group} {remote_conf_path}/gunicorn.sh'.format(user=DEPLOYMENT_USER,
                                                                      group=DEPLOYMENT_GROUP,
                                                                      remote_conf_path=remote_conf_path))


@task
def install_systemd_services():
    services = [STEEPSHOTBOT_SERVICE]

    common_context = {
        'PROJECT_NAME': PROJECT_NAME,
        'USER': DEPLOYMENT_USER,
        'GROUP': DEPLOYMENT_GROUP,
        'DEPLOY_DIR': DEPLOY_DIR
    }
    for service in services:
        _install_service(service, common_context)


@task
def install_virtualenv():
    logger.info("Creating clean virtual environment.")

    with prefix('source {profile}'.format(profile=USER_PROFILE_FILE)):
        with settings(warn_only=True), cd(REMOTE_DEPLOY_DIR):
            logger.info('Deleting old virtualenv.')
            sudo('rmvirtualenv {virtualenv_name}'.format(virtualenv_name=ENVIRONMENT_NAME),
                 user=DEPLOYMENT_USER)

            logger.info("Creating a new virtualenv.")
            sudo('mkvirtualenv {environment_name} -p /usr/bin/python3.5'.format(environment_name=ENVIRONMENT_NAME),
                 user=DEPLOYMENT_USER)


@task
def config_virtualenv():

    remote_postactivate_path = os.path.join(WORKON_HOME,
                                            ENVIRONMENT_NAME,
                                            'bin/postactivate')

    postactivate_context = {
        'DATABASE_URL': 'postgres://%s:%s@%s:%s/%s' % (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME),
        'IS_PRODUCTION': env.is_production,
        'IS_CERTBOT_CERT': env.is_certbot_cert,
        'STEEPSHOTBOT_DOMAIN': env.steepshotbot_domain,
        'FLASK_APP': FLASK_APP,
        'DEPLOY_DIR': DEPLOY_DIR,
        'TELEGRAM_BOT_TOKEN': input('Please enter your token: ')
    }

    upload_template(os.path.join(LOCAL_CONF_DIR, 'postactivate'),
                    remote_postactivate_path, context=postactivate_context,
                    backup=False, use_sudo=True)

    sudo('chown {user}:{group} {remote_postactivate_path}'.format(user=DEPLOYMENT_USER,
                                                                  group=DEPLOYMENT_GROUP,
                                                                  remote_postactivate_path=remote_postactivate_path))


@task
def install_req():
    logger.info("Installing python requirements.")

    with cd(DEPLOY_DIR), prefix('source %s' % VENV_ACTIVATE):
        with settings(sudo_user=DEPLOYMENT_USER):
            sudo('pip install --upgrade pip')
            # Parameter --upgrade allows install a new packages
            # from requirements.txt. For example: golosdata>=0.0.4 was set in requirement.txt,
            # if a new version of golosdata appear into pypi repository the package will be upgrade
            sudo('pip install --no-cache-dir --upgrade -r {req_file}'
                 .format(req_file='requirements.txt'))


@task
def clean_pyc():
    logger.info("Cleaning .pyc files.")

    with cd(DEPLOY_DIR):
        sudo("find . -name '*.pyc'")
        sudo('find . -name \*.pyc -delete')


@task
def check_nginx_service():
    sudo('systemctl --no-pager --full status {service_name}'.format(service_name=NGINX_SERVICE))


@task
def check_steepshotbot_service():
    sudo('systemctl --no-pager --full status {service_name}'.format(service_name=STEEPSHOTBOT_SERVICE))


@task
def check_statuses():
    with settings(warn_only=True):
        services_to_check = [NGINX_SERVICE,
                             STEEPSHOTBOT_SERVICE]
        for service in services_to_check:
            sudo('systemctl --no-pager --full status {service_name}'.format(service_name=service))


@task
def restart_nginx_service():
    sudo('systemctl stop {service_name}'.format(service_name=NGINX_SERVICE))
    sudo('systemctl start {service_name}'.format(service_name=NGINX_SERVICE))


@task
def restart_steepshotbot_service():
    sudo('systemctl stop {service_name}'.format(service_name=STEEPSHOTBOT_SERVICE))
    sudo('systemctl start {service_name}'.format(service_name=STEEPSHOTBOT_SERVICE))


@task
def restart():
    services_to_restart = [NGINX_SERVICE,
                           STEEPSHOTBOT_SERVICE]

    for service_name in services_to_restart:
        _restart_systemd_service(service_name)


@task
def production():
    _load_environment('PRODUCTION')


@task
def first_time_deploy():
    if not exists(REMOTE_DEPLOY_DIR):
        create_non_priveledged_user()
    install_system_packages()
    prepare_virtualenv()
    create_postgresdb()
    deploy()


@task
def deploy():
    remote_conf_path = '%s/conf' % DEPLOY_DIR

    clearing_project_directory()
    checkout_repository()
    create_deploy_dirs(remote_conf_path)
    deploy_files()

    config_nginx()
    config_gunicorn(remote_conf_path)

    install_systemd_services()

    install_virtualenv()

    config_virtualenv()

    install_req()

    clean_pyc()

    restart()
