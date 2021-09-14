import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from web.configuration import Config

'''
This abstraction is made since the Spacy library has a lot of functionality encompassed into it.

For example, you can lemmatize data and get a list of stop words, along with embedding.

To reduce circular dependencies and increase performance, this wrapper loads the library in one place,
and then subsequent classes can use it to load in the library and work with it for their use.
'''


class SpacyWrapper():
    _nlp = None
    _pipeline_components = ['tok2vec', 'tagger', 'parser', 'senter', 'ner', 'attribute_ruler', 'lemmatizer']
    _lemmatizer_disabled_components = ['tok2vec', 'parser', 'senter', 'ner']
    _tok2vec_disabled_components = ['tagger', 'parser', 'senter', 'ner', 'attribute_ruler', 'lemmatizer']

    @classmethod
    def _initialize(cls):
        if cls._nlp is None:
            cls._nlp = spacy.load(Config.NLP_FILE_PATH)

    @classmethod
    def nlp(cls):
        cls._initialize()
        return cls._nlp

    @classmethod
    def embed(cls, sentence):
        return cls.nlp()(sentence, disable=cls._tok2vec_disabled_components)

    @classmethod
    def stop_words(cls):
        return STOP_WORDS

    @classmethod
    def lemmatize(cls, sentence):
        tokens = cls.nlp()(sentence, disable=cls._lemmatizer_disabled_components)
        return ' '.join([token.lemma_ for token in tokens])
