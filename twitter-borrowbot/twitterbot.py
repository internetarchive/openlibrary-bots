#-*- encoding: utf-8 -*-
import os
import time
import tweepy
from dotenv import load_dotenv

from services import InternetArchive, ISBNFinder, Logger

ACTIONS = ('read', 'borrow', 'preview')
READ_OPTIONS = dict(zip(InternetArchive.MODES, ACTIONS))
BOT_NAME = "@borrowbot"
STATE_FILE = 'last_seen_id.txt'

LOGGER = Logger("./logs/tweet_logs.txt", "./logs/error_logs.txt")

load_dotenv()

# Authenticate
auth = tweepy.OAuthHandler(
    os.environ.get('CONSUMER_KEY'),
    os.environ.get('CONSUMER_SECRET')
)
auth.set_access_token(
    os.environ.get('ACCESS_TOKEN'),
    os.environ.get('ACCESS_TOKEN_SECRET')
)
api = tweepy.API(auth, wait_on_rate_limit=True)

class Tweet:
    @staticmethod
    def _tweet(mention, message, debug=False):
        msg = "Hi 👋 @%s %s" % (mention.user.screen_name, message)
        if not debug:
            api.update_status(
                msg,
                in_reply_to_status_id=mention.id,
                auto_populate_reply_metadata=True
            )
        else:
            print(msg)
        LOGGER.log_tweet(msg)

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
        cls._tweet(
            mention,
            "sorry, I was unable to spot any books! " +
            "Learn more about how I work here: " +
            "https://github.com/internetarchive/openlibrary-bots"
        )

    @classmethod
    def internal_error(cls, mention):
        cls._tweet(
            mention,
            "Woops, something broke over here! " +
            "Learn more about how I work here: " +
            "https://github.com/internetarchive/openlibrary-bots" +
            "\nAn ISBN, Amazon or Goodreads url are required."
        )

def get_last_seen_id():
    with open(STATE_FILE, 'r') as fin:
        return int(fin.read().strip())


def set_last_seen_id(mention):
    with open(STATE_FILE, 'w') as fout:
        fout.write(str(mention.id))

def get_parent_tweet_of(mention):
    return api.get_status(
        mention.in_reply_to_status_id,
        tweet_mode="extended")


def get_latest_mentions(since=None):
    since = since or get_last_seen_id()
    try:
        return api.mentions_timeline(since, tweet_mode="extended")
    except Exception as e:
        print("Exception: %s" % e)
        return None

def is_reply_to_me(mention):
    return mention.in_reply_to_status_id is api.me().id

def handle_isbn(mention, isbn):
    edition = InternetArchive.get_edition(isbn)
    if edition:
        if edition.get("availability"):
            return Tweet.edition_available(mention, edition)

        work = InternetArchive.find_available_work(edition)
        if work:
            return Tweet.work_available(mention, work)
        return Tweet.edition_unavailable(mention, edition)

def reply_to_tweets():
    try:
        mentions = get_latest_mentions()
    except Exception as err:
        LOGGER.log_error("Failed to get mentions: %s" % err)
        return
    
    for mention in reversed(mentions):
        print(str(mention.id) + ': ' + mention.full_text)

        try:
            set_last_seen_id(mention)
        except Exception as err:
            LOGGER.log_error("Failed to set last seen id: %s" % err)
            continue 
        
        # I think I can remove this line. get_latest_mentions should handle
        if BOT_NAME in mention.full_text:
            try:
                isbns = ISBNFinder.find_isbns(mention.full_text)
                # no isbn found in tweet. Check the parent tweet
                if not isbns and mention.in_reply_to_status_id:
                    parent_mention = get_parent_tweet_of(mention)
                    isbns = ISBNFinder.find_isbns(parent_mention.full_text)
                    # Reply to me
                    if not isbns and parent_mention.user.id == api.me().id:
                        print("is reply to me")
                        continue
                if isbns:
                    for isbn in isbns:
                        handle_isbn(mention, isbn)
                    continue
                Tweet.edition_not_found(mention)
            except Exception as err:
                LOGGER.log_error("Failed to handle mention: %s" % err)
                try:
                    Tweet.internal_error(mention)
                except:
                    LOGGER.log_error("Failed to send internal error tweet: %s" % err)
                continue


if __name__ == "__main__":
    while True:
        try:
            reply_to_tweets()
            time.sleep(15)
        except Exception as err:
            LOGGER.log_error("Failed in main: %s" % err)
