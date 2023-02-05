# -*- encoding: utf-8 -*-
import logging
import os
import time

import tweepy
import twitterbotErrors
from dotenv import load_dotenv
from services import InternetArchive, ISBNFinder

ACTIONS = ("read", "borrow", "preview")
READ_OPTIONS = dict(zip(InternetArchive.MODES, ACTIONS))
BOT_NAME = "@borrowbot"
STATE_FILE = "last_seen_id.txt"

LOG_FILE = "twitterbot.log"

API = None
MENTION_LIMIT = 100
LAST_SEEN_ID_LEN = 19

load_dotenv()
if (
    not os.environ.get("CONSUMER_KEY")
    or not os.environ.get("CONSUMER_SECRET")
    or not os.environ.get("ACCESS_TOKEN")
    or not os.environ.get("ACCESS_TOKEN_SECRET")
):
    raise twitterbotErrors.TweepyAuthenticationError(
        error="Missing .env file or missing necessary keys for authentication"
    )

# Authenticate
auth = tweepy.OAuthHandler(
    os.environ.get("CONSUMER_KEY"), os.environ.get("CONSUMER_SECRET")
)
auth.set_access_token(
    os.environ.get("ACCESS_TOKEN"), os.environ.get("ACCESS_TOKEN_SECRET")
)
API = tweepy.API(auth, wait_on_rate_limit=True)


class Tweet:
    @staticmethod
    def _tweet(mention, message, debug=False):
        if not mention.user.screen_name or not mention.id:
            raise twitterbotErrors.SendTweetError(
                mention=mention,
                error="Given mention is missing either a screen name or a status ID",
            )
        msg = "Hi 👋 @%s %s" % (mention.user.screen_name, message)
        if not debug:
            try:
                API.update_status(
                    msg,
                    in_reply_to_status_id=mention.id,
                    auto_populate_reply_metadata=True,
                )
            except Exception as e:
                raise twitterbotErrors.SendTweetError(
                    mention=mention, message=msg, error=e
                )
        else:
            logging.info("RESPONSE: " + msg.replace("\n", " "))

    @classmethod
    def edition_available(cls, mention, edition):
        action = READ_OPTIONS[edition.get("availability")]
        print("Replying: Edition %sable" % action)
        cls._tweet(
            mention,
            "you're in luck. "
            + "This book appears to be %sable " % action
            + "on @openlibrary: "
            + "%s/isbn/%s" % (InternetArchive.OL_URL, edition.get("isbn")),
        )

    @classmethod
    def work_available(cls, mention, work):
        cls._tweet(
            mention,
            "this exact edition doesn't appear to be available, "
            "however it seems a similar edition may be: "
            + "https://openlibrary.org/work/"
            + work.get("openlibrary_work"),
        )

    @classmethod
    def edition_unavailable(cls, mention, edition):
        cls._tweet(
            mention,
            "this book doesn't appear to have a readable option yet, "
            + "however you can still add it to your "
            + "Want To Read list here: "
            + "%s/isbn/%s" % (InternetArchive.OL_URL, edition.get("isbn")),
        )

    @classmethod
    def edition_not_found(cls, mention):
        cls._tweet(
            mention,
            "sorry, I was unable to spot any books! "
            + "Learn more about how I work here: "
            + "https://github.com/internetarchive/openlibrary-bots",
        )

    @classmethod
    def internal_error(cls, mention):
        cls._tweet(
            mention,
            "Woops, something broke over here! "
            + "Learn more about how I work here: "
            + "https://github.com/internetarchive/openlibrary-bots"
            + "\nAn ISBN, Amazon or Goodreads url are required.",
        )


def get_last_seen_id():
    try:
        with open(STATE_FILE, "r") as fin:
            last_seen_id = fin.read().strip()
    except Exception as e:
        raise twitterbotErrors.FileIOError(filename=STATE_FILE, error=e)
    else:
        if len(last_seen_id) < LAST_SEEN_ID_LEN or not last_seen_id.isdecimal():
            raise twitterbotErrors.LastSeenIDError(
                filename=STATE_FILE, last_seen_id=last_seen_id
            )
        return int(last_seen_id)


def set_last_seen_id(mention):
    try:
        with open(STATE_FILE, "w") as fout:
            fout.write(str(mention.id))
    except Exception as e:
        raise twitterbotErrors.FileIOError(
            filename=STATE_FILE, data=mention.id, error=e
        )


def get_parent_tweet_of(mention):
    try:
        return API.get_status(mention.in_reply_to_status_id, tweet_mode="extended")
    except Exception as e:
        raise twitterbotErrors.GetTweetError(
            tweet_id=mention.in_reply_to_status_id, error=e
        )


def get_latest_mentions(since=None):
    try:
        since = since or get_last_seen_id()
        mentions = API.mentions_timeline(since, tweet_mode="extended")
        if len(mentions) >= MENTION_LIMIT:
            raise twitterbotErrors.TooManyMentionsError(
                since=since, mention_count=len(mentions), mention_limit=MENTION_LIMIT
            )
        return mentions
    except twitterbotErrors.TooManyMentionsError as e:
        logging.warning(e)
        return mentions[
            MENTION_LIMIT:
        ]  # MIGHT BE mentions[MENTION_LIMIT:] FIFO vs LIFO
    except Exception as e:
        raise twitterbotErrors.GetMentionsError(since=since, error=e)


def is_reply_to_me(mention):
    return mention.in_reply_to_status_id is API.me().id


def handle_isbn(mention, isbn):
    try:
        edition = InternetArchive.get_edition(isbn)
    except (
        twitterbotErrors.GetEditionError,
        twitterbotErrors.GetAvailabilityError,
    ) as e:
        logging.critical(e)
        return Tweet.internal_error(mention)

    if edition:
        if edition.get("availability"):
            return Tweet.edition_available(mention, edition)

        try:
            work = InternetArchive.find_available_work(edition)
        except twitterbotErrors.FindAvailableWorkError as e:
            logging.critical(e)
            return Tweet.internal_error(mention)

        if work:
            return Tweet.work_available(mention, work)
        return Tweet.edition_unavailable(mention, edition)


def reply_to_tweets():
    try:
        mentions = get_latest_mentions()
    except twitterbotErrors.GetMentionsError as e:
        logging.critical(e)
        return

    for mention in reversed(mentions):
        logging.info(
            "MENTION FROM: "
            + mention.user.screen_name
            + " | ID: "
            + str(mention.id)
            + " --> "
            + mention.full_text.replace("\n", " ")
        )

        try:
            set_last_seen_id(mention)
        except twitterbotErrors.FileIOError as e:
            logging.critical(e)
            return

        try:
            isbns = ISBNFinder.find_isbns(mention.full_text)
        except twitterbotErrors.FindISBNError as e:
            logging.warning(e)
            continue

        # no isbn found in tweet. Check the parent tweet
        if not isbns and mention.in_reply_to_status_id:
            try:
                parent_mention = get_parent_tweet_of(mention)
                isbns = ISBNFinder.find_isbns(parent_mention.full_text)
            except (
                twitterbotErrors.GetTweetError,
                twitterbotErrors.FindISBNError,
            ) as e:
                logging.warning(e)
                Tweet.internal_error(mention)
                continue

            # Reply to me
            if not isbns and parent_mention.user.id == API.me().id:
                logging.info(f"IS REPLY TO ME")
                continue
        if isbns:
            for isbn in isbns:
                try:
                    handle_isbn(mention, isbn)
                except twitterbotErrors.SendTweetError as e:
                    logging.critical(e)
        else:
            Tweet.edition_not_found(mention)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        filename=LOG_FILE,
        filemode="a",
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    while True:
        try:
            reply_to_tweets()
        except Exception as e:
            logging.critical(f"Failed in main loop: {e}")
        finally:
            time.sleep(15)
