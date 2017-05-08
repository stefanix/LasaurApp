import os, sys

class Translations(object):
    def __init__(self, language="en"):
        self.languages = []

        self.dictionary = {}

        self.current_language = language
        self.default_language = "en"
        sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

        for f in os.listdir(os.path.dirname(os.path.realpath(__file__))):
            lang_file = os.path.realpath(f)
            if lang_file.endswith(".py") and not lang_file.endswith("__init__.py"):
                lang = os.path.splitext(os.path.basename(lang_file))[0]
                self.languages.append(lang)
                self.dictionary[lang] = __import__(lang).dictionary

    def __getitem__(self, key):
        if self.dictionary[self.current_language].has_key(key):
            return self.dictionary[self.current_language][key]
        if self.dictionary[self.default_language].has_key(key):
            return self.dictionary[self.default_language][key]
        else:
            return key

    def __iter__(self):
        for each in self.dictionary[self.default_language].keys():
            yield [each, self.__getitem__(each)]
