import os
from setuptools import setup, find_packages


def readme():
    return open('README.rst').read() if os.path.exists('README.rst') else '<README IS MISSING>'


def license():
    return open('LICENSE').read() if os.path.exists('LICENSE') else 'MIT'


setup(
    name='steepshot-telegram',
    version='0.0.1',
    description='Telegram-bot for Steepshot',
    long_description=readme(),
    url='https://github.com/Chainers/steepshot-telegram',
    author='steepshot',
    author_email='steepshot.org@gmail.com',
    keywords='blockchain steepshot steem photo',
    license=license(),
    packages=find_packages(),
    zip_safe=False,
    classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5'
    ],
    entry_points={
        'console_scripts': [
            'steepshotbot=steepshot_bot.main:main',
        ]
    }
)
