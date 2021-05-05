import spacy
from web.configuration import Config

'''
This abstraction is made since the Spacy library has a lot of functionality encompassed into it.

For example, you can lemmatize data and get a list of stop words, along with embedding.

To reduce circular dependencies and increase performance, this wrapper loads the library in one place,
and then subsequent classes can use it to load in the library and work with it for their use.
'''


class SpacyWrapper():
    _nlp = None

    @classmethod
    def _initialize(cls):
        if cls._nlp is None:
            cls._nlp = spacy.load(Config.NLP_FILE_PATH)

    @classmethod
    def nlp(cls):
        cls._initialize()
        return cls._nlp
