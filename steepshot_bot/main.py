import datetime
import logging.config
import os
from functools import wraps

import telebot
from flask import Flask, request, abort
from peewee import DoesNotExist
from steepbase.exceptions import InvalidWifError
from werkzeug.contrib.fixers import ProxyFix

from steepshot_bot import keyboard as kb, settings, steem, steepshot_api, logic
from steepshot_bot.db import User, Post
from steepshot_bot.db import db
from steepshot_bot.exceptions import SteepshotBotError
from steepshot_bot.messages import get_message
from steepshot_bot.utils import resolve_identifier

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN)


def authenticated(func):
    @wraps(func)
    def wrapper(message: telebot.types.Message):
        if isinstance(message, telebot.types.CallbackQuery):
            chat_id = message.message.chat.id
        else:
            chat_id = message.chat.id
        try:
            user = User.get(User.id == message.from_user.id)
            if not steem.is_user_logged_in(user.name):
                msg = bot.reply_to(user.get_wif_msg(), 'Try to get your WIF key...')
                wif = msg.reply_to_message.text
                bot.delete_message(chat_id, msg.message_id)

                user.last_login_time = datetime.datetime.now()

                steem.login(user.name, wif)
            user.last_action_time = datetime.datetime.now()
            user.save()
            return func(user, message)
        except DoesNotExist as e:
            logger.error('Not authenticated. User not found: %s', e)
            bot.send_message(
                chat_id,
                get_message('auth_required'),
                parse_mode='markdown',
                reply_markup=kb.Keyboard.login()
            )
            return
        except InvalidWifError as e:
            logger.error('Failed to authenticate user: "%s"', e)
            bot.send_message(
                chat_id,
                get_message('wrong_key', default='Wrong posting key'),
                parse_mode='markdown',
                reply_markup=kb.Keyboard.login()
            )
            return

    return wrapper


@bot.message_handler(commands=['start'])
def handle_start(message: telebot.types.Message):
    lang = message.from_user.language_code
    logger.info('Receive message from user "{name}", id: {id}'.format(name=message.chat.first_name, id=message.chat.id))
    bot.send_message(
        message.chat.id,
        get_message('welcome', locale=lang),
        parse_mode='markdown',
        reply_markup=kb.Keyboard.main() if logic.is_authenticated(message.from_user.id) else kb.Keyboard.login()
    )


@bot.message_handler(regexp=kb.LOG_IN_BTN)
def handle_auth(message: telebot.types.Message):
    lang = message.from_user.language_code
    logger.info('Steem auth request. Telegram user_id: %s', message.from_user.id)

    if logic.is_authenticated(message.from_user.id):
        bot.reply_to(
            message,
            get_message('already_authorized', locale=lang),
            parse_mode='markdown',
            reply_markup=kb.Keyboard.main()
        )
        return

    msg = bot.reply_to(
        message,
        get_message('username', locale=lang),
        parse_mode='markdown',
        reply_markup=kb.Keyboard.remove()
    )
    bot.register_next_step_handler(msg, process_steem_username)


def process_steem_username(message: telebot.types.Message):
    lang = message.from_user.language_code
    steem_username = message.text
    logger.info('Try to authenticate Steem user: "%s"', steem_username)
    if not steem.account_exists(steem_username):
        logger.info('Steem acoount "%s" does not exists.', steem_username)
        msg = bot.reply_to(message, get_message('user_not_found', locale=lang), parse_mode='markdown')
        bot.register_next_step_handler(msg, process_steem_username)
        return

    try:
        chat_id = message.chat.id
        user, created = User.get_or_create(id=message.from_user.id)
        user.name = steem_username
        user.chat_id = chat_id
        user.save()
        if created:
            logger.info('New user added to db: id=%s, name="%s"', message.from_user.id, steem_username)
        else:
            logger.info('user updated in db: id=%s, name="%s"', message.from_user.id, steem_username)
        msg = bot.reply_to(message, get_message('wif', locale=lang), parse_mode='markdown')
        bot.register_next_step_handler(msg, process_private_wif)
    except Exception as e:
        logger.error('Failed to process Steem username: %s', e)
        bot.reply_to(message, get_message('error', locale=lang))


def process_private_wif(message: telebot.types.Message):
    lang = message.from_user.language_code

    try:
        chat_id = message.chat.id
        user = User.get(User.id == message.from_user.id, User.chat_id == chat_id)
        logger.info('Request WIF for user: "%s"', user.name)

        steem.login(user.name, message.text)

        user.wif_message_id = message.message_id
        user.save()

        logger.info('User has been successfully registered and logged in: "%s"', user.name)
        bot.send_message(
            chat_id,
            get_message('logged_in', locale=lang),
            parse_mode='markdown',
            reply_markup=kb.Keyboard.main()
        )
        bot.send_message(
            chat_id,
            get_message('info', locale=lang),
            parse_mode='markdown',
            reply_markup=kb.Keyboard.main()
        )
    except InvalidWifError as e:
        logger.error('Failed to authenticate user: "%s"', e)
        bot.reply_to(
            message,
            get_message('wrong_key', locale=lang),
            parse_mode='markdown',
            reply_markup=kb.Keyboard.login()
        )
    except Exception as e:
        logger.error('Failed to process WIF key: %s', e)
        bot.reply_to(message, get_message('error', locale=lang))


@bot.message_handler(func=lambda msg: msg.content_type == 'text' and msg.text in [kb.FEED_BTN,
                                                                                  kb.NEW_BTN,
                                                                                  kb.HOT_BTN,
                                                                                  kb.TOP_BTN])
@authenticated
def show_posts(user: User, message: telebot.types.Message):
    logger.info('Request posts for user: "%s"', user.name)
    lang = message.from_user.language_code

    get_posts = {
        kb.FEED_BTN: steepshot_api.get_recent_posts,
        kb.NEW_BTN: steepshot_api.get_new_posts,
        kb.HOT_BTN: steepshot_api.get_hot_posts,
        kb.TOP_BTN: steepshot_api.get_top_posts
    }[message.text]
    posts = get_posts(user.name)
    if not posts:
        bot.send_message(
            message.chat.id,
            get_message('no_photos', locale=lang).format(source=message.text),
            parse_mode='markdown'
        )
        return
    for post in posts[:5]:
        keyboard = telebot.types.InlineKeyboardMarkup()
        like_button = telebot.types.InlineKeyboardButton(text=b'\xE2\x9D\xA4', callback_data='upvote')
        url_button = telebot.types.InlineKeyboardButton(text='open', url=settings.POST_BASE_URL + post['url'])
        comment_button = telebot.types.InlineKeyboardButton(text='comment', callback_data='comment')
        keyboard.add(like_button, url_button, comment_button)
        msg = bot.send_photo(
            message.chat.id,
            post['body'],
            caption='{}: {}'.format(post['author'], post['title']),
            reply_markup=keyboard
        )
        Post.create(chat_id=msg.chat.id, message_id=msg.message_id, identifier=resolve_identifier(post['url']))


@bot.callback_query_handler(lambda call: call.data == 'comment')
@authenticated
def comment_callback(user: User, call: telebot.types.CallbackQuery):
    lang = call.message.from_user.language_code
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    def request_comment_text(message: telebot.types.Message):
        try:
            post = Post.get(Post.chat_id == chat_id, Post.message_id == message_id)
            steem.add_comment(post.identifier, user.name, message.text)
            bot.send_message(chat_id,
                             get_message('commented', locale=lang),
                             parse_mode='markdown',
                             reply_markup=kb.Keyboard.main())
        except SteepshotBotError as e:
            logger.error('Failed to get post to comment: %s', e)
            bot.answer_callback_query(call.id, e.get_msg(locale=lang), show_alert=True)

    msg = bot.send_message(chat_id, 'Enter your comment to this post', reply_markup=telebot.types.ReplyKeyboardRemove())

    bot.register_next_step_handler(msg, request_comment_text)


@bot.callback_query_handler(lambda call: call.data == 'upvote')
@authenticated
def upvote_callback(user: User, call: telebot.types.CallbackQuery):
    lang = call.message.from_user.language_code
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    try:
        post = Post.get(Post.chat_id == chat_id, Post.message_id == message_id)
        logic.upvote(post.identifier, user.name)
        # TODO update post
        bot.answer_callback_query(call.id, get_message('upvoted', locale=lang), show_alert=False)
    except SteepshotBotError as e:
        logger.error('Failed to upvote post: %s', e)
        bot.answer_callback_query(call.id, e.get_msg(lang), show_alert=True)
    except DoesNotExist as e:
        logger.error('Failed to get post to upvote.')
        bot.answer_callback_query(call.id, 'Failed to get post to upvote.', show_alert=True)


@bot.message_handler(func=lambda msg: msg.content_type == 'text' and msg.text == kb.SETTINGS_BTN)
@authenticated
def user_settings(user: User, message: telebot.types.Message):
    lang = message.from_user.language_code

    logger.info('User requested personal info: "%s"', user.name)
    bot.reply_to(
        user.get_wif_msg(),
        get_message('user_info', locale=lang).format(username=user.name),
        parse_mode='markdown',
        reply_markup=kb.Keyboard.settings()
    )


@bot.message_handler(func=lambda msg: msg.content_type == 'text' and msg.text == kb.BACK_BTN)
@authenticated
def back_handler(user: User, message: telebot.types.Message):
    lang = message.from_user.language_code

    bot.send_message(
        message.chat.id,
        get_message('info', locale=lang),
        parse_mode='markdown',
        reply_markup=kb.Keyboard.main()
    )


@bot.message_handler(func=lambda msg: msg.content_type == 'text' and msg.text == kb.LOG_OUT_BTN)
@authenticated
def back_handler(user: User, message: telebot.types.Message):
    lang = message.from_user.language_code
    wif_msg = user.get_wif_msg()
    username = user.name
    steem.logout(user)
    logger.info('User %s has been successfully logged out.', username)

    bot.reply_to(
        wif_msg,
        get_message('logged_out', locale=lang),
        parse_mode='markdown',
        reply_markup=kb.Keyboard.login()
    )


@bot.message_handler(content_types=['photo'])
@authenticated
def post_image(user: User, message: telebot.types.Message):
    lang = message.from_user.language_code
    chat_id = message.chat.id
    title = message.caption
    photo_info = sorted(message.photo, key=lambda x: x.file_size, reverse=True)[0]
    file_info = bot.get_file(photo_info.file_id)
    image_bytes = bot.download_file(file_info.file_path)

    def post(msg: telebot.types.Message):
        photo_title = title or msg.text
        try:
            logic.post_to_steem(image_bytes, photo_title, user.name)
            bot.send_message(chat_id, get_message('post_added', locale=lang), parse_mode='markdown')
        except SteepshotBotError as e:
            logger.error('Failed to post photo: %s', e)
            bot.send_message(chat_id, e.get_msg(lang), parse_mode='markdown')

    if title:
        post(message)
    else:
        m = bot.reply_to(message, get_message('title_required'), parse_mode='markdown')
        bot.register_next_step_handler(m, post)


@app.route(settings.WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    data = request.get_json(silent=True)
    if not data:
        abort(403)
    bot.process_new_updates([telebot.types.Update.de_json(data)])
    return "!", 200


@app.route("/")
def index():
    return "!", 200


def main():
    logging.config.dictConfig(settings.LOGGER_CONF)

    if not os.path.exists(settings.DATA_PATH):
        try:
            os.makedirs(settings.DATA_PATH, exist_ok=True)
            logger.info('Path created: %s', settings.DATA_PATH)
        except OSError as e:
            logger.error('Failed to create path "%s", error: %s', settings.DATA_PATH, e)
            return e.errno

    if db:
        existing_tables = db.get_tables()
        models = [User, Post]
        for model in models:
            if model.__name__.lower() not in existing_tables:
                logger.info('Creating new table: "%s"', model.__name__.lower())
                model.create_table()

    return 0


main()

if __name__ == '__main__':
    logger.info('Start bot in local mode. Listening...')
    bot.polling(none_stop=True)
else:
    bot.remove_webhook()
    bot.set_webhook(url='{}{}'.format(settings.WEBHOOK_URL_BASE, settings.WEBHOOK_URL_PATH))
