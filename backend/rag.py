from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

class RAGEngine:
    def __init__(self, indexer):
        self.indexer = indexer
        self._fit()

    def _fit(self):
        self.docs = self.indexer.search_documents()
        corpus = [d["text"] for d in self.docs] or [""]
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            token_pattern=r"(?u)\b[A-Za-z_][A-Za-z0-9_]*\b",
            ngram_range=(1, 2),
        )
        self.matrix = self.vectorizer.fit_transform(corpus)

    