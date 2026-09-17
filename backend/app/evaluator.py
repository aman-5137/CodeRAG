def evaluate_retrieval(rag):
    cases = [
        {
            "question": "Where is user authentication implemented?",
            "relevant_files": {"services/auth.py"},
        },
        {
            "question": "How does create_user work?",
            "relevant_files": {"services/user_service.py"},
        },
        {
            "question": "What handles database access?",
            "relevant_files": {"db.py", "services/user_service.py"},
        },
        {
            "question": "Where is the API application created?",
            "relevant_files": {"api.py"},
        },
    ]

    rows = []
    for case in cases:
        retrieved = rag.retrieve(case["question"], 5)
        files = [d["file"] for d in retrieved]
        relevant = case["relevant_files"]
        hits = sum(1 for f in files if f in relevant)
        precision = hits / max(1, len(files))
        recall = hits / max(1, len(relevant))

        rr = 0.0
        for rank, f in enumerate(files, 1):
            if f in relevant:
                rr = 1 / rank
                break

        rows.append({
            "question": case["question"],
            "precision_at_5": round(precision, 3),
            "recall_at_5": round(recall, 3),
            "mrr": round(rr, 3),
            "retrieved_files": files,
        })

    n = len(rows)
    return {
        "architecture": "Hybrid TF-IDF + lexical retrieval + weighted reranking",
        "cases": rows,
        "mean_precision_at_5": round(sum(r["precision_at_5"] for r in rows) / n, 3),
        "mean_recall_at_5": round(sum(r["recall_at_5"] for r in rows) / n, 3),
        "mean_mrr": round(sum(r["mrr"] for r in rows) / n, 3),
        "faithfulness_note": "Demo faithfulness is citation-grounded: generated responses expose the retrieved source chunks. Replace with LLM-as-judge for production evaluation.",
    }

