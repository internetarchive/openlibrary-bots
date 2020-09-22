"""Reformat language keys in Editions"""

import copy
import gzip
import json
import requests

from olclient.bots import BaseBot


class LanguageBot(BaseBot):
    def __init__(self):
        self.VALID_ATTR_NAME = 'languages'
        self.INVALID_ATTR_NAME = 'language'
        self.VALID_LANGUAGE_DICTS = tuple(requests.get('https://openlibrary.org/query.json?type=/type/language&key=&limit=10000').json())
        self.VALID_LANGUAGE_CODES = list()
        for _lang_dicts in self.VALID_LANGUAGE_DICTS:
            self.VALID_LANGUAGE_CODES.append(_lang_dicts['key'].split('/')[-1])
        self.VALID_LANGUAGE_CODES = tuple(self.VALID_LANGUAGE_CODES)
        super(LanguageBot, self).__init__()

    def fix_languages(self, _attr_name:str, _languages) -> list:
        """
        Attempts to mends the language attribute of an Open Library Edition. Does nothing for non-trivial failure modes.
        :param _languages: dictionary containing the language attribute(s) of an Open Library Edition
        """
        failure_mode = self.get_failure_mode(_attr_name, _languages)
        if failure_mode == 'invalid_attr_name':
            return _languages
        elif failure_mode == 'string':
            if _languages in self.VALID_LANGUAGE_CODES:
                return [{'key': '/%s/%s' % (self.VALID_ATTR_NAME, _languages)}]
        return _languages

    def get_failure_mode(self, attr_name: str, language_attr) -> str:
        """
        Return human-readable failure mode. Returns 'valid' if the language attribute is well-formed
        :param attr_name: the name of the attribute on the Open Library Edition
        :param language_attr: The value of edition.languages where `edition` is an Open Library Edition
        """
        if attr_name != self.VALID_ATTR_NAME:
            return 'invalid_attr_name'
        if isinstance(language_attr, str):
            # i.e '"languages": "eng"'
            return 'string'
        if isinstance(language_attr, list):
            all_valid = True
            for lang in language_attr:
                if lang not in self.VALID_LANGUAGE_DICTS:
                    # i.e '"languages": [{"key": "/languages/foobar"}]'
                    all_valid = False
                    break
            if all_valid:
                return 'valid'
            return'invalid-lang-dict'
        return 'unknown'

    def get_languages(self, obj) -> dict:
        """
        Returns dict with values equal to the language attribute of an Open Library Edition.
        The dictionary key describes if the attribute name is correct.
        :param obj: A JSON dictionary or Open Library Edition
        """
        if isinstance(obj, dict):
            _language = {self.VALID_ATTR_NAME: obj.get(self.VALID_ATTR_NAME),
                         self.INVALID_ATTR_NAME: obj.get(self.INVALID_ATTR_NAME)}
        else:
            _language = {self.VALID_ATTR_NAME: getattr(obj, self.VALID_ATTR_NAME, None),
                         self.INVALID_ATTR_NAME: getattr(obj, self.INVALID_ATTR_NAME, None)}
        if self.VALID_ATTR_NAME in _language and self.INVALID_ATTR_NAME in _language:  # In theory an Open Library edition can have a `language` and a `languages` field.
            _language.pop(self.INVALID_ATTR_NAME)
        _language = {k: v for k, v in _language.items() if v is not None}  # don't bother storing non-existent attributes
        return _language

    def is_language_valid(self, _attr_name: str, language_attr) -> bool:
        """
        :param _attr_name: the name of the attribute on the Open Library Edition
        :param language_attr: The value of edition.languages where `edition` is an Open Library Edition
        """
        return self.get_failure_mode(_attr_name, language_attr) == 'valid'

    def run(self) -> None:
        """
        Properly format the language attribute. Proper format is '"languages": [{"key": "/languages/<language code>"}]'
        """
        if self.dry_run:
            self.logger.info('dry-run is TRUE. Script will run, but no modifications will be made')

        header = {'type': 0,
                  'key': 1,
                  'revision': 2,
                  'last_modified': 3,
                  'JSON': 4}
        comment = 'reformat language attribute'
        with gzip.open(self.args.file, 'rb') as fin:
            for row_num, row in enumerate(fin):
                print(row_num)
                row = row.decode().split('\t')
                json_data = json.loads(row[header['JSON']])
                languages = self.get_languages(json_data)
                if not languages: continue
                if any([True for attr_name, language in languages.items() if self.is_language_valid(attr_name, language)]): continue

                olid = json_data['key'].split('/')[-1]
                edition = self.ol.Edition.get(olid)
                languages = self.get_languages(edition)
                if not languages: continue
                if any([True for attr_name, language in languages.items() if self.is_language_valid(attr_name, language)]): continue

                old_attr_name = list(languages.keys())[0]
                old_lang_value = copy.deepcopy(getattr(edition, old_attr_name))

                fixed_langs = list(languages.values())[0]
                failure_mode = self.get_failure_mode(old_lang_value, fixed_langs)
                if failure_mode == 'string':
                    if fixed_langs in self.VALID_LANGUAGE_CODES:
                        fixed_langs = [{'key': '/%s/%s' % (self.VALID_ATTR_NAME, fixed_langs)}]

                if old_attr_name != self.VALID_ATTR_NAME and fixed_langs != old_lang_value:
                    setattr(edition, self.VALID_ATTR_NAME, fixed_langs)
                    self.logger.info('\t'.join([olid, '"%s": ' % old_attr_name + str(old_lang_value),
                                                '"%s": ' % self.VALID_ATTR_NAME + str(edition.languages)]))
                    self.save(lambda: edition.save(comment=comment))


if '__main__' == __name__:
    bot = LanguageBot()

    try:
        bot.run()
    except Exception as e:
        bot.logger.exception("")
        raise e
