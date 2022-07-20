import unittest

from services import InternetArchive, ISBNFinder
from twitterbot import Tweet

twitterized_url = "https://t.co/cKlQ9xJC1W?amp=1"
goodreads_url = (
    "https://www.goodreads.com/book/show/5544.Surely_You_re_Joking_Mr_Feynman_"
)
amazon_product_url = "https://www.amazon.com/gp/product/0393316041/ref=x_gr_w_bb_glide_sin?ie=UTF8&tag=x_gr_w_bb_glide_sin-20&linkCode=as2&camp=1789&creative=9325&creativeASIN=0393316041&SubscriptionId=1MGPYB6YW3HWK55XCGG2"
amazon_dp_url = (
    "https://www.amazon.com/Surely-Youre-Joking-Feynman-Adventures/dp/009917331X"
)


class TestBorrowBot(unittest.TestCase):
    def test_goodreads_to_isbn(self):
        tweet = "Hey @borrowbot, what about %s" % goodreads_url
        isbns = list(ISBNFinder.find_isbns(tweet))
        assert isbns == ["9780393316049"]

    def test_twitterized_to_isbn(self):
        tweet = "Hey @borrowbot, what about %s" % twitterized_url
        isbns = list(ISBNFinder.find_isbns(tweet))
        assert isbns == ["1798434520"]

    def test_amazon_to_isbn(self):
        tweet = "Hey @borrowbot, what about %s" % amazon_product_url
        isbns = list(ISBNFinder.find_isbns(tweet))
        assert isbns == ["0393316041"]

        tweet = "Hey @borrowbot, what about %s" % amazon_dp_url
        isbns = list(ISBNFinder.find_isbns(tweet))
        assert isbns == ["009917331X"]

    def test_isbns(self):
        isbn = "9780393316049"
        multiple_isbns = ["9780393316049", "9780393019216"]

        tweet = "Hey @borrowbot, what about %s" % isbn
        print(tweet)
        isbns = list(ISBNFinder.find_isbns(tweet))
        print(isbns)
        assert isbns == [isbn]

        tweet = "Hey @borrowbot, what about %s" % multiple_isbns
        print(tweet)
        isbns = list(ISBNFinder.find_isbns(tweet))
        assert isbns == multiple_isbns

    def test_get_book(self):
        isbn = '0399143904'
        tweet = "Hey @borrowbot, what about %s" % isbn
        isbn = list(ISBNFinder.find_isbns(tweet))[0]
        edition = InternetArchive.get_edition(isbn)
        assert edition
