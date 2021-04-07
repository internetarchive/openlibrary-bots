#-*- encoding: utf-8 -*-
import os
import re
import time
import requests
import tweepy

from services import InternetArchive, ISBNFinder
from dotenv import load_dotenv

ACTIONS = ('read', 'borrow', 'preview')
READ_OPTIONS = dict(zip(InternetArchive.MODES, ACTIONS))
BOT_NAME = "@borrowbot"
STATE_FILE = 'last_seen_id.txt'


load_dotenv()

auth = tweepy.OAuthHandler(
    os.environ.get('CONSUMER_KEY'),
    os.environ.get('CONSUMER_SECRET')
)
auth.set_access_token(
    os.environ.get('ACCESS_TOKEN'),
    os.environ.get('ACCESS_TOKEN_SECRET')
)
api = tweepy.API(auth, wait_on_rate_limit=True)


def get_last_seen_id():
    with open(STATE_FILE, 'r') as fin:
        return int(fin.read().strip())


def set_last_seen_id(mention):
    with open(STATE_FILE, 'w') as fout:
        fout.write(str(mention.id))

def get_parent_tweet_of(mention):
    if mention.in_reply_to_status_id:
        return api.get_status(
            mention.in_reply_to_status_id,
            tweet_mode="extended")
    return []


def get_latest_mentions(since=None):
    since = since or get_last_seen_id()
    try:
        return api.mentions_timeline(since, tweet_mode="extended")
    except Exception as e:
        print("Exception: %s" % e)
        return None


class Tweet:

    @staticmethod
    def _tweet(mention, message, debug=False):
        msg = "Hi 👋 @%s %s" % (mention.user.screen_name, message)
        print(msg)
        if not debug:
            api.update_status(
                msg,
                in_reply_to_status_id=mention.id,
                auto_populate_reply_metadata=True
            )

    @classmethod
    def edition_available(cls, mention, edition):
        action = READ_OPTIONS[edition.get("availability")]
        print('Replying: Edition %sable' % action)
        cls._tweet(
            mention,
            "you're in luck. " +
            "This book appears to be %sable " % action +
            "on @openlibrary: " +
            "%s/isbn/%s" % (InternetArchive.OL_URL, edition.get("isbn"))
        )

    @classmethod
    def work_available(cls, mention, work):
        cls._tweet(
            mention,
            "this exact edition doesn't appear to be available, "
            "however it seems a similar edition may be: " +
            "https://openlibrary.org/work/" + work.get('openlibrary_work')
        )

    @classmethod
    def edition_unavailable(cls, mention, edition):
        cls._tweet(
            mention,
            "this book doesn't appear to have a readable option yet, " +
            "however you can still add it to your " +
            "Want To Read list here: " +
            "%s/isbn/%s" % (InternetArchive.OL_URL, edition.get("isbn"))
        )

    @classmethod
    def edition_not_found(cls, mention):
        print('Replying: Book Not found')
        cls._tweet(
            mention,
            "sorry, I was unable to spot any books! " +
            "Learn more about how I work here: " +
            "https://github.com/internetarchive/openlibrary-bots"
        )


def reply_to_tweets():
    mentions = get_latest_mentions()
    for mention in reversed(mentions):
        print(str(mention.id) + ': ' + mention.full_text)
        set_last_seen_id(mention)

        if BOT_NAME in mention.full_text:
            isbns = ISBNFinder.find_isbns(mention.full_text)
            if not isbns:
                # fetch tweet's parent (TODO: or siblings) & check for isbns
                mention = get_parent_tweet_of(mention)
                isbns = ISBNFinder.find_isbns(mention.full_text)

            for isbn in isbns:
                edition = InternetArchive.get_edition(isbn)
                if edition:
                    if edition.get("availability"):
                        return Tweet.edition_available(mention, edition)

                    work = InternetArchive.find_available_work(edition)
                    if work:
                        return Tweet.work_available(mention, work)
                    return Tweet.edition_unavailable(mention, edition)
        return Tweet.edition_not_found(mention)


if __name__ == "__main__":
    while True:
        reply_to_tweets()
        time.sleep(15)
