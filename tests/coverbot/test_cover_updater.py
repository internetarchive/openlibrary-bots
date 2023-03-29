import unittest
from random import randint

from coverbot.cover_updater import AddInternetArchiveCoverJob as job


class AddInternetArchiveCoverJob(unittest.TestCase):
    def test_valid_covers(self):
        self.assertFalse(job.valid_covers([]))
        self.assertFalse(job.valid_covers([-1]))
        self.assertFalse(job.valid_covers([None]))
        self.assertFalse(job.valid_covers([-1, None]))
        self.assertFalse(job.valid_covers([None, -1]))
        self.assertTrue(job.valid_covers([randint(1000000, 9999999)]))
        rand_covers = [randint(1000000, 9999999), randint(1000000, 9999999)]
        self.assertTrue(job.valid_covers(rand_covers))
