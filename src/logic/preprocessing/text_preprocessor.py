import re
from lib.spacy_wrapper import SpacyWrapper


class TextPreprocessor():
    _regex_multiple_spaces = re.compile(r'\s+')
    _regex_special_chars = re.compile(r'[^a-zA-Z]')

    # Clean the sentence and lematize it

    @classmethod
    def clean(cls, sentence):
        sentence = sentence.lower()
        sentence = cls._remove_special_chars(sentence)
        sentence = cls._remove_stopwords(sentence)
        sentence = cls._remove_multiple_spaces(sentence)
        sentence = cls._trim(sentence)
        sentence = cls._lemmatize(sentence)
        return sentence

    @classmethod
    def _remove_special_chars(cls, sentence):
        return re.sub(cls._regex_special_chars, ' ', sentence)

    @classmethod
    def _remove_multiple_spaces(cls, sentence):
        return re.sub(cls._regex_multiple_spaces, ' ', sentence)

    @classmethod
    def _trim(cls, sentence):
        return sentence.strip()

    @classmethod
    def _remove_stopwords(cls, sentence):
        words = [token.text for token in SpacyWrapper.nlp()(sentence) if not token.is_stop]
        return ' '.join(words)

    @classmethod
    def _lemmatize(cls, sentence):
        return ' '.join([token.lemma_ for token in SpacyWrapper.nlp()(sentence)])
