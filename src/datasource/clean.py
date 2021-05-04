import re


_regex_multiple_spaces = re.compile(r'\s+')
_regex_special_chars = re.compile(r'[^a-zA-Z]')


# Clean the sentence and lematize it
def clean(nlp):
    def _clean(sentence):
        sentence = sentence.lower()
        sentence = _remove_special_chars(sentence)
        sentence = _remove_stopwords(sentence, nlp=nlp)
        sentence = _remove_multiple_spaces(sentence)
        sentence = _trim(sentence)
        sentence = _lemmatize(sentence, nlp=nlp)
        return sentence

    return _clean


def _remove_special_chars(sentence):
    return re.sub(_regex_special_chars, ' ', sentence)


def _remove_multiple_spaces(sentence):
    return re.sub(_regex_multiple_spaces, ' ', sentence)


def _trim(sentence):
    return sentence.strip()


def _remove_stopwords(sentence, nlp):
    if nlp is None:
        raise Exception('NLP not defined')
    words = sentence.split(' ')
    words = [word for word in words if word not in nlp.Defaults.stop_words]
    return ' '.join(words)


def _lemmatize(sentence, nlp):
    if nlp is None:
        raise Exception('Lemmatizer is not defined')
    words = sentence.split(' ')
    return ' '.join([nlp(word)[0].lemma_ for word in words])
