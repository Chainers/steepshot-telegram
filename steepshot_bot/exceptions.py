class SteepshotBotError(Exception):
    msg = {}

    def get_msg(self, locale: str = 'en') -> str:
        return self.msg.get(locale, self.msg.get('en', 'Some error occurred: ')) + str(self)


class SteepshotServerError(SteepshotBotError):
    msg = {
        'en': 'Some Steepshot error occurred: '
    }


class SteemError(SteepshotBotError):
    msg = {
        'en': 'Some Steem error occurred: '
    }


class PostNotFound(SteepshotBotError):
    msg = {
        'en': 'This post was not found: '
    }


class VotedSimilarily(SteepshotBotError):
    msg = {
        'en': 'You have already voted in a similar way: '
    }
