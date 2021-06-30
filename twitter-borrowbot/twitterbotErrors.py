class Error(Exception):
    pass

class TweepyAuthenticationError(Error):
    def __init__(self, error=None):
        self.error = error

    def __str__(self):
        return "{0}: Failed to Authenticate with Twitter through Tweepy >> {1}".format(type(self).__name__, self.error)

class FileIOError(Error):
    def __init__(self, file=None, write=None, error="Error not provided"):
        self.file = file
        self.write = write
        self.error = error

    def __str__(self):
        if self.write:
            return "{0}: Failed to write '{1}' to file '{2}' >> {3}".format(type(self).__name__, self.write, self.file, self.error) 
        return "{0}: Failed to read from file '{1}' >> {2}".format(type(self).__name__, self.file, self.error)

    
class LastSeenIDError(Error):
    def __init__(self, file=None, id=None):
        self.file = file
        self.id = id

    def __str__(self):
        return "{0}: The folowing ID '{1}' from file '{2}' is either too short or is not numeric".format(type(self).__name__, self.id, self.file)


class GetMentionsError(Error):
    def __init__(self, since=None, error=None):
        self.since = since
        self.error = error

    def __str__(self):
        return "{0}: Tweepy failed to get the lastest mentions since '{1}' >> {2}".format(type(self).__name__, self.since, self.error)


class TooManyMentionsError(Error):
    def __init__(self, since=None, length=None, limit=None):
        self.since = since
        self.length = length
        self.limit = limit

    def __str__(self):
        return "{0}: At '{1}', Tweepy pulled '{2}' mentions when the limit is '{3}' >> {4} too many mentions".format(type(self).__name__, self.since, self.length, self.limit, (self.length - self.limit))


class GoodreadsError(Error):
    def __init__(self, url=None, error=None):
        self.url=url
        self.error=error

    def __str__(self):
        return "{0}: Failed to scrape url '{1}' >> {2}".format(type(self).__name__, self.url, self.error)


class AmazonError(Error):
    def __init__(self, url=None, error=None):
        self.url = url
        self.error = error

    def __str__(self):
        return "{0}: Failed to scrape url '{1}' >> {2}".format(type(self).__name__, self.url, self.error)


class FindISBNError(Error):
    def __init__(self, text=None, error=None):
        self.text = text
        self.error = error

    def __str__(self):
        return "{0}: text='{1}' >> {2}".format(type(self).__name__, self.text, self.error)


class GetTweetError(Error):
    def __init__(self, id=None, error=None):
        self.id = id
        self.error = error

    def __str__(self):
        return "{0}: Failed to get tweet with ID '{1}' >> {2}".format(type(self).__name__, self.id, self.error)


class GetEditionError(Error):
    def __init__(self, isbn=None, error=None):
        self.isbn = isbn
        self.error = error

    def __str__(self):
        return "{0}: Failed to get edition with isbn '{1}' >> {2}".format(type(self).__name__, self.isbn, self.error)


class GetAvailabilityError(Error):
    def __init__(self, identifier=None, error=None):
        self.identifier = identifier
        self.error = error

    def __str__(self):
        return "{0}: Failed to get availability with identifier '{1}' >> {2}".format(type(self).__name__, self.identifier, self.error)


class FindAvailableWorkError(Error):
    def __init__(self, book=None, error=None):
        self.book = book
        self.error = error

    def __str__(self):
        return "{0}: Failed to get book '{1}' >> {2}".format(type(self).__name__, self.book, self.error)


class SendTweetError(Error):
    def __init__(self, mention=None, message=None, error=None):
        self.mention = mention
        self.message = message
        self.error = error

    def __str__(self):
        if not self.mention.user.screen_name or not self.mention.id:
            return "{0}: {1}".format(type(self).__name__, self.error)
        return "{0}: Failed to send tweet '{1}' with mention id '{2}' >> {3}".format(type(self).__name__, self.message, self.mention.id, self.error)   