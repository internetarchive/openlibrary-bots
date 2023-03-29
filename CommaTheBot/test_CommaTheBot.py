import unittest

from CommaTheBot import CommaTheBotJob

commaTheBot = CommaTheBotJob()


class TestCommaTheBot(unittest.TestCase):
    def test_no_title(self):
        title = ""
        needs_fixing = commaTheBot.needs_fixing(title)
        assert needs_fixing is False

    def test_no_fixing(self):
        title = "The Foo"
        needs_fixing = commaTheBot.needs_fixing(title)
        assert needs_fixing is False

    def test_needs_fixing(self):
        title = "Foo, The"
        needs_fixing = commaTheBot.needs_fixing(title)
        assert needs_fixing is True

    def test_fix(self):
        title = "Foo, The"
        fixed_title = commaTheBot.fix_title(title)
        assert fixed_title == "The Foo"

    def test_pattern_match(self):
        # case of article is kept, with and without space
        title = "Foo, The"
        assert commaTheBot.fix_title(title) == "The Foo"
        title = "Foo, the"
        assert commaTheBot.fix_title(title) == "the Foo"
        title = "Foo,The"
        assert commaTheBot.fix_title(title) == "The Foo"
        title = "Foo,the"
        assert commaTheBot.fix_title(title) == "the Foo"

        # convoluted title
        title = "Foo 1234 asf__bdf, the cool, the"
        assert commaTheBot.fix_title(title) == "the Foo 1234 asf__bdf, the cool"

    def test_pattern_no_match(self):
        title = "Foo, The blah"
        assert commaTheBot.needs_fixing(title) is False

        # no title
        title = ", The"
        assert commaTheBot.needs_fixing(title) is False
        title = "The"
        assert commaTheBot.needs_fixing(title) is False

        # article not at end of line
        title = "Foo, The "
        assert commaTheBot.needs_fixing(title) is False

        # maybe support for these should be added
        title = "Foo (bar), The"
        assert commaTheBot.needs_fixing(title) is False
        title = "Foo., The"
        assert commaTheBot.needs_fixing(title) is False
        title = "foo-bar, The"
        assert commaTheBot.needs_fixing(title) is False
