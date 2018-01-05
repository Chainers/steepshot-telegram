_messages = {
    'en': {
        'welcome': 'Hello!\n'
                   'This is *Steepshot* Telegram bot. Here you can post photos directly to Steem blockchain.\n'
                   'First you need to do is authorize.',
        'username': 'What\'s your Steem username?',
        'wif': 'Please enter yout private posting key _(we don\'t store it, '
               'you can delete your message later and bot won\'t be able to interact with your account)_.',
        'error': 'Ooops, something went wrong!',
        'user_not_found': 'This user wasn\'t found, please check your username and enter it again.',
        'wrong_key': 'Failed to authenticate with this key. Please double check it and try to auth again.',
        'auth_required': 'You are not authenticated. Please authenticate.',
        'user_info': 'You are logged in as "{username}", your posting key is written above. You can click on it and then delete the message'
                     ', but don\'t forget to set checkbox _"Delete for SteepshotBot"_ '
                     'if you want bot to forget your key.',
        'logged_in': 'You have been successfully logged into you Steem account!',
        'post_added': 'Your post has been successfully added!',
        'post_not_added': 'Something went wrong. Please, try to add post later.',
        'fail_post_validate': 'There are some errors: {error}.',
        'title_required': 'Please enter the title of the post. You can write tags with #.',
        'upvoted': 'Post has been upvoted.',
        'commented': 'Your comment has been successfully added.',
        'no_photos': 'There is no photos to show in {source}.',
        'info': 'You can post photo by sending image to the bot (but don\'t forget to set checkbox _"Compressed"_.\n'
                'You also can watch your feed and new/hot/top posts.',
        'already_authorized': 'You are already authorized.',
        'logged_out': 'You has been logged out. You can remove the message with your private posting key now.'
    }
}


def get_message(key, locale='en', default=''):
    return _messages.get(locale, _messages['en']).get(key, default)
