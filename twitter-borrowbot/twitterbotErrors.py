class Error(Exception):
    pass


class TweepyAuthenticationError(Error):
    def __init__(self, error=None):
        self.error = error

    def __str__(self):
        return f"{type(self).__name__}: Failed to Authenticate with Twitter through Tweepy >> {self.error}"


class FileIOError(Error):
    def __init__(self, filename=None, data=None, error="Error not provided"):
        self.filename = filename
        self.data = data
        self.error = error

    def __str__(self):
        if self.write:
            return f"{type(self).__name__}: Failed to write '{self.data}' to file '{self.filename}' >> {self.error}"
        return f"{type(self).__name__}: Failed to read from file '{self.filename}' >> {self.error}"


class LastSeenIDError(Error):
    def __init__(self, filename=None, last_seen_id=None):
        self.filename = filename
        self.last_seen_id = last_seen_id

    def __str__(self):
        return f"{type(self).__name__}: The following ID '{self.last_seen_id}' from file '{self.filename}' is either too short or is not numeric"


class GetMentionsError(Error):
    def __init__(self, since=None, error=None):
        self.since = since
        self.error = error

    def __str__(self):
        return f"{type(self).__name__}: Tweepy failed to get the latest mentions since '{self.since}' >> {self.error}"


class TooManyMentionsError(Error):
    def __init__(self, since=None, mention_count=None, mention_limit=None):
        self.since = since
        self.mention_count = mention_count
        self.mention_limit = mention_limit

    def __str__(self):
        return f"{type(self).__name__}: At '{self.since}', Tweepy pulled '{self.mention_count}' mentions when the limit is '{self.mention_limit}' >> {(self.mention_count - self.mention_limit)} too many mentions"


class GoodreadsError(Error):
    def __init__(self, url=None, error=None):
        self.url = url
        self.error = error

    def __str__(self):
        return (
            f"{type(self).__name__}: Failed to scrape url '{self.url}' >> {self.error}"
        )


class AmazonError(Error):
    def __init__(self, url=None, error=None):
        self.url = url
        self.error = error

    def __str__(self):
        return (
            f"{type(self).__name__}: Failed to scrape url '{self.url}' >> {self.error}"
        )


class FindISBNError(Error):
    def __init__(self, text=None, error=None):
        self.text = text
        self.error = error

    def __str__(self):
        return f"{type(self).__name__}: text='{self.text}' >> {self.error}"


class GetTweetError(Error):
    def __init__(self, tweet_id=None, error=None):
        self.tweet_id = tweet_id
        self.error = error

    def __str__(self):
        return f"{type(self).__name__}: Failed to get tweet with ID '{self.tweet_id}' >> {self.error}"


class GetEditionError(Error):
    def __init__(self, isbn=None, error=None):
        self.isbn = isbn
        self.error = error

    def __str__(self):
        return f"{type(self).__name__}: Failed to get edition with isbn '{self.isbn}' >> {self.error}"


class GetAvailabilityError(Error):
    def __init__(self, identifier=None, error=None):
        self.identifier = identifier
        self.error = error

    def __str__(self):
        return f"{type(self).__name__}: Failed to get availability with identifier '{self.identifier}' >> {self.error}"


class FindAvailableWorkError(Error):
    def __init__(self, book=None, error=None):
        self.book = book
        self.error = error

    def __str__(self):
        return (
            f"{type(self).__name__}: Failed to get book '{self.book}' >> {self.error}"
        )


class SendTweetError(Error):
    def __init__(self, mention=None, message=None, error=None):
        self.mention = mention
        self.message = message
        self.error = error

    def __str__(self):
        if not self.mention.user.screen_name or not self.mention.id:
            return f"{type(self).__name__}: {self.error}"
        return f"{type(self).__name__}: Failed to send tweet '{self.message}' with mention id '{self.mention.id}' >> {self.error}"
