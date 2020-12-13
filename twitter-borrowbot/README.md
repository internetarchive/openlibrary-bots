
# Purpose

@borrowbot https://twitter.com/borrowbot is a python twitter bot which lets patrons check whether a book is available to read, borrow, or catalog on Open Library.

# Installation

Installation will require API keys in order to run

```
virtualenv -p python3 borrowbot-venv
source borrowbot-venv/bin/activate
git clone https://github.com/internetarchive/openlibrary-bots.git
cd twitter-borrowbot
pip install -r requirements.txt
```

In order to run the bot, we must add the correct API keys to a new file called `.env` within the repo:
```
CONSUMER_KEY = ""
CONSUMER_SECRET = ""
ACCESS_TOKEN = ""
ACCESS_TOKEN_SECRET = ""
```

We then create a file called `last_seen_id.txt` with a twitter timestamp of the last tweet processed (or today's date by default), e.g.
```
1337668472549982208
```

As a final step, run:
```
python twitterbot.py
```
