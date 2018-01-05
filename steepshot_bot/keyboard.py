import telebot

LOG_IN_BTN = 'Log in'
FEED_BTN = 'Feed'
NEW_BTN = 'New'
HOT_BTN = 'Hot'
TOP_BTN = 'Top'
SETTINGS_BTN = 'Settings'
BACK_BTN = 'Back'
LOG_OUT_BTN = 'Log out'


class Keyboard(object):
    @staticmethod
    def login():
        markup = telebot.types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )
        markup.add(LOG_IN_BTN)
        return markup

    @staticmethod
    def main():
        markup = telebot.types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )
        markup.add(FEED_BTN, NEW_BTN)
        markup.add(HOT_BTN, TOP_BTN)
        markup.add(SETTINGS_BTN)
        return markup

    @staticmethod
    def settings():
        markup = telebot.types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )
        markup.add(BACK_BTN, LOG_OUT_BTN)
        return markup

    @staticmethod
    def remove():
        return telebot.types.ReplyKeyboardRemove(selective=False)
