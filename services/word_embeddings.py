import spacy

class WordEmbeddings:
    nlp = None
    
    ## TODO: Replace with same embeddings as used by 
    @staticmethod
    def _init(self):
        print("Loading word embeddings")
        nlp = spacy.load("en_core_web_lg")
        print("Finished loading word embeddings")
    
    @staticmethod
    def get_vector(word):
        if nlp is None:
            _init()
        
        return nlp(word).vector