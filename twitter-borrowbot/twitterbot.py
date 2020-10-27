import os
import re
import time
import requests
import tweepy
import isbnlib

from dotenv import load_dotenv
load_dotenv()

auth = tweepy.OAuthHandler(os.environ.get(
    'CONSUMER_KEY'), os.environ.get('CONSUMER_SECRET'))
auth.set_access_token(os.environ.get('ACCESS_TOKEN'),
                      os.environ.get('ACCESS_TOKEN_SECRET'))
api = tweepy.API(auth, wait_on_rate_limit=True)

FILE_NAME = 'last_seen_id.txt'


def retrieve_last_seen_id(file_name):
    with open(file_name, 'r') as f_read:
        return int(f_read.read().strip())


def store_last_seen_id(last_seen_id, file_name):
    with open(file_name, 'w') as f_write:
        f_write.write(str(last_seen_id))


def check_tweet(tweet, parent=False):
    if parent:
        print("In parent")
        print(tweet.full_text)
        print(tweet.in_reply_to_status_id)
        if tweet.in_reply_to_status_id:
            tweet = api.get_status(tweet.in_reply_to_status_id, tweet_mode="extended")
            print(tweet.full_text)
        else:
            return []
    
    text = tweet.full_text
    words = text.split()
    isbnlike = isbnlib.get_isbnlike(text, level='normal')

    print(isbnlike)
    print(words)

    for word in words:
        if word.startswith(("http", "https")):
            print(word)
            resp = requests.head(word)
            location = resp.headers["Location"]
            print(location)
            if "amazon" in location and "/dp/" in location:
                amazon_text = isbnlib.get_isbnlike(location, level='normal')
                amazon_text = list(dict.fromkeys(amazon_text))
                for item in amazon_text:
                    if isbnlib.is_isbn10(item) or isbnlib.is_isbn13(item):
                        isbnlike.append(item)

    print(isbnlike)
    return isbnlike


def reply_to_tweets():
    last_seen_id = retrieve_last_seen_id(FILE_NAME)

    try:
        mentions = api.mentions_timeline(last_seen_id, tweet_mode="extended")
    except Exception as e:
        print("Exception: {}".format(e))
        return

    for mention in reversed(mentions):
        print('{}- {}'.format(mention.id, mention.full_text))
        last_seen_id = mention.id
        store_last_seen_id(last_seen_id, FILE_NAME)
        isbnlike = check_tweet(mention, False)
        if len(isbnlike) == 0:
            isbnlike = check_tweet(mention, True)
        if len(isbnlike) == 0:
            print('Responding back ...')
            print("sorry, we couldn't find a book ID to look for, learn how I work here: <github README url>")
            try:
                api.update_status('Hi 👋 @' + mention.user.screen_name + " Sorry, we couldn't find a book ID to look for, learn how I work here: https://github.com/internetarchive/openlibrary-bots", in_reply_to_status_id=mention.id, auto_populate_reply_metadata=True)
            except: 
                pass
            return
        for isbn in isbnlike:
            isbn = isbnlib.canonical(isbn)
            reply_text = ""
            if isbnlib.is_isbn10(isbn) or isbnlib.is_isbn13(isbn):
                try:
                    resp = requests.get("http://openlibrary.org/isbn/"+isbn+".json").json()
                except:
                    print("Error in response continuing")
                    continue
                if resp.__contains__("ocaid"):
                    try:
                        resp_archive = requests.get("https://archive.org/services/loans/loan/?&action=availability&identifier="+resp["ocaid"]).json()
                    except:
                        print("Error in response continuing")
                        continue
                    if resp_archive and resp_archive['lending_status']['is_readable']:
                        reply_text = '@' + mention.user.screen_name + " you're in luck. This book appears to be available to read for free from @openlibrary: https://openlibrary.org/isbn/" + isbn
                    elif resp_archive and resp_archive['lending_status']['is_lendable']:
                        reply_text = '@' + mention.user.screen_name + " you're in luck. This book appears to be available to borrow for free from @openlibrary: https://openlibrary.org/isbn/" + isbn
                    elif resp_archive and resp_archive['lending_status']['is_printdisabled']:
                        reply_text = '@' + mention.user.screen_name + " you're in luck. This book appears to be available to preview for free from @openlibrary: https://openlibrary.org/isbn/" + isbn
                    else:
                        reply_text = '@' + mention.user.screen_name + " This title doesn't appear to have a free read option yet, however you can add it to your Want To Read list here: https://openlibrary.org/isbn/" + isbn
                else:
                    try:
                        resp_advanced = requests.get("https://archive.org/advancedsearch.php?q=openlibrary_work:"+resp["works"][0]['key'].split("/")[-1]+"&fl[]=identifier&sort[]=&sort[]=&sort[]=&rows=50&page=1&output=json").json()
                    except Exception as e:
                        print("Error in response continuing: {}".format(e))
                        continue
                    if resp_advanced and resp_advanced["response"]["numFound"] > 1:
                        reply_text = '@' + mention.user.screen_name + " This edition doesn't appear to be available, however I've identified "+str(resp_advanced["response"]["numFound"])+" other editions which may be available here -> https://openlibrary.org" + resp["works"][0]['key']
                    else:
                        reply_text = '@' + mention.user.screen_name + " This title doesn't appear to have a free read option yet, however you can add it to your Want To Read list here: https://openlibrary.org/isbn/" + isbn

                print('Responding back ...')
                print(reply_text)
                try:
                    api.update_status('Hi 👋 ' + reply_text, in_reply_to_status_id=mention.id, auto_populate_reply_metadata=True)
                except:
                    pass
        # -------------------- To get all replies for the tweet --------------------------------
        # replies=[]
        # print("Replies: \n\n")
        # for tweet in tweepy.Cursor(api.search,q='to:'+'@' + mention.user.screen_name,result_type='recent',timeout=999999).items(1000):
        #     if hasattr(tweet, 'in_reply_to_status_id_str'):
        #         # print("has attributed:",str(tweet.in_reply_to_status_id_str))
        #         # print(mention.id)
        #         if str(tweet.in_reply_to_status_id_str) == str(mention.id):
        #             # print("reply appended")
        #             text = tweet.text
        #             words = text.split()
        #             print(words)
        #             replies.append(tweet.text)
        # for elements in replies:
        #     print("Replies :",elements)
        # -------------------------------------------------------------------------------------

while True:
    reply_to_tweets()
    time.sleep(15)
