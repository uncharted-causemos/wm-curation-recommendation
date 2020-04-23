from services.word_embeddings import WordEmbeddings
from spacy.lemmatizer import Lemmatizer

class FactorEmbeddingService:
    client = None;
    lemmatizer = Lemmatizer(nlp.vocab.lookups)

    def __init__(self):
        self.client = Elasticsearch(
            ['localhost'], #TODO LATER: change to read from .env
            http_auth=('', ''), #TODO LATER: add authentication
            scheme="https",
            port=443,
        )
    
    def compute_vector(sentence):
        return WordEmbeddings.get_vector(sentence)

    def clean(sentence):
        sentence = sentence.lower()
        sentence = remove_special_chars(sentence)
        sentence = remove_stopwords(sentence)
        sentence = remove_multiple_spaces(sentence)
        sentence = trim(sentence)
        sentence = lemmatize(sentence)
        return sentence

    def remove_special_chars(sentence):
        return re.sub('[^a-zA-Z]', " ", sentence)

    def remove_multiple_spaces(sentence):
        return re.sub('\s+', ' ', sentence)

    def trim(sentence):
        return sentence.strip()

    def remove_stopwords(sentence):
        return " ".join([word for word in sentence.split(" ") if word not in nlp.Defaults.stop_words])

    def lemmatize(sentence):
        return " ".join([lemmatizer.lookup(word) for word in sentence.split(' ')])

    def clean(sentence):
        sentence = sentence.lower()
        sentence = remove_special_chars(sentence)
        sentence = remove_stopwords(sentence)
        sentence = remove_multiple_spaces(sentence)
        sentence = trim(sentence)
        sentence = lemmatize(sentence)
        return sentence
    
