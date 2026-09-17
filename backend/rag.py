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

    def retrieve(self, question, top_k=5):
            if len(self.docs) == 0:
                return []
            q = self.vectorizer.transform([question])
            semantic = cosine_similarity(q, self.matrix)[0]
            q_terms = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", question.lower()))
    
            scored = []
            for i, doc in enumerate(self.docs):
                doc_terms = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", doc["text"].lower()))
                lexical = len(q_terms & doc_terms) / max(1, len(q_terms))
                # Hybrid retrieval + reranking.
                score = 0.65 * float(semantic[i]) + 0.35 * lexical
                scored.append((score, doc))
    
            scored.sort(key=lambda x: x[0], reverse=True)
            result = []
            for score, doc in scored[:top_k]:
                item = dict(doc)
                item["score"] = round(score, 4)
                result.append(item)
            return result
    
    def answer(self, question, top_k=5):
        retrieved = self.retrieve(question, top_k)
        if not retrieved:
            return {"answer": "No code chunks are indexed.", "sources": [], "retrieval": []}

        q = question.lower()
        if "impact" in q or "affected" in q or "depend" in q:
            target = self._guess_target(question)
            impact = self.indexer.impact_analysis(target)
            answer = self._format_impact(target, impact)
        else:
            answer = self._generate_local_answer(question, retrieved)

        return {
            "answer": answer,
            "sources": [
                {
                    "file": d["file"],
                    "symbol": d["symbol"],
                    "lines": f"{d['start_line']}-{d['end_line']}",
                    "score": d["score"],
                    "kind": d["kind"],
                }
                for d in retrieved
            ],
            "retrieval": retrieved,
        }

    def _guess_target(self, question):
        symbols = [s["name"] for s in self.indexer.symbols]
        for symbol in sorted(symbols, key=len, reverse=True):
            if symbol.lower() in question.lower():
                return symbol
        return question

    def _generate_local_answer(self, question, docs):
        q = question.lower()
        lead = docs[0]
        if "how" in q or "what does" in q or "where" in q:
            return (
                f"The most relevant implementation is `{lead['symbol']}` in "
                f"`{lead['file']}` (lines {lead['start_line']}-{lead['end_line']}). "
                f"The indexed AST identifies it as a {lead['kind']}. "
                f"I retrieved {len(docs)} relevant code chunks and ranked them using "
                f"a hybrid lexical + TF-IDF similarity score. See the source references below."
            )
        return (
            f"Based on the indexed repository, the strongest match is `{lead['symbol']}` "
            f"in `{lead['file']}`. The answer is grounded in {len(docs)} retrieved code chunks."
        )

    def _format_impact(self, target, impact):
        if not impact["affected_files"]:
            return f"No dependent files were detected for `{target}` in the indexed repository."
        names = ", ".join(sorted({x["file"] for x in impact["affected_files"]}))
        return (
            f"Changing `{target}` may affect {len(set(x['file'] for x in impact['affected_files']))} "
            f"file(s): {names}. The dependency graph combines AST import relationships with "
            f"lightweight symbol-reference analysis."
        )
