import React, { useEffect, useState } from "react"
import { createRoot } from "react-dom/client"
import axios from "axios"
import "./styles.css"

const api = axios.create({ baseURL: "http://127.0.0.1:8000" })

const examples = [
  "Where is user authentication implemented?",
  "How does create_user work?",
  "What files could be affected if UserService changes?",
  "Where is the API application created?"
]

function App() {
  const [tab, setTab] = useState("chat")
  const [question, setQuestion] = useState(examples[0])
  const [result, setResult] = useState(null)
  const [repo, setRepo] = useState(null)
  const [impact, setImpact] = useState(null)
  const [evaluation, setEvaluation] = useState(null)
  const [loading, setLoading] = useState(false)

  const loadRepo = async () => {
    const { data } = await api.get("/api/repository")
    setRepo(data)
  }

  useEffect(() => { loadRepo().catch(console.error) }, [])

  const ask = async () => {
    setLoading(true)
    try {
      const { data } = await api.post("/api/query", { question, top_k: 5 })
      setResult(data)
    } catch (e) {
      setResult({ answer: "Backend is not running. Start FastAPI first.", sources: [] })
    } finally {
      setLoading(false)
    }
  }

  const runImpact = async () => {
    const target = question.match(/([A-Za-z_][A-Za-z0-9_]*)/)?.[1] || "UserService"
    const { data } = await api.post("/api/impact", { target })
    setImpact(data)
  }

  const runEvaluation = async () => {
    const { data } = await api.get("/api/evaluate")
    setEvaluation(data)
  }

  return (
    <div className="app">
      <aside>
        <div className="brand">
          <div className="logo">CR</div>
          <div><b>CodeRAG</b><span>Codebase Intelligence</span></div>
        </div>
        <nav>
          {[
            ["chat", "⌘", "Ask Codebase"],
            ["graph", "◈", "Repository Graph"],
            ["impact", "↗", "Impact Analysis"],
            ["eval", "◎", "RAG Evaluation"]
          ].map(([id, icon, label]) =>
            <button className={tab === id ? "active" : ""} onClick={() => setTab(id)} key={id}>
              <i>{icon}</i>{label}
            </button>
          )}
        </nav>
        <div className="sideCard">
          <small>INDEX STATUS</small>
          <strong>● Ready</strong>
          <span>{repo?.files?.length || 0} files · {repo?.chunks || 0} chunks</span>
        </div>
      </aside>

      <main>
        <header>
          <div>
            <p className="eyebrow">AI-POWERED CODEBASE INTELLIGENCE</p>
            <h1>{tab === "chat" ? "Ask your codebase." :
              tab === "graph" ? "Repository Graph." :
              tab === "impact" ? "Change Impact Analysis." : "RAG Evaluation."}</h1>
            <p className="subtitle">
              {tab === "chat" ? "Understand code through retrieval, AST analysis and grounded answers." :
               tab === "graph" ? "Explore files, modules and detected dependency relationships." :
               tab === "impact" ? "Find likely files affected by changing a symbol or module." :
               "Measure retrieval quality with reproducible test questions."}
            </p>
          </div>
          <div className="badge">LOCAL DEMO</div>
        </header>

        {tab === "chat" && <section>
          <div className="queryBox">
            <textarea value={question} onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) ask() }}
              placeholder="Ask something about the repository..." />
            <div className="queryBottom">
              <div className="chips">
                {examples.slice(0,3).map(x => <button onClick={() => setQuestion(x)} key={x}>{x}</button>)}
              </div>
              <button className="primary" onClick={ask}>{loading ? "Searching..." : "Run RAG →"}</button>
            </div>
          </div>

          {result && <div className="answerGrid">
            <article className="panel answer">
              <div className="panelHead"><span>GENERATED ANSWER</span><em>grounded</em></div>
              <p>{result.answer}</p>
            </article>
            <article className="panel">
              <div className="panelHead"><span>SOURCE REFERENCES</span><em>{result.sources.length} chunks</em></div>
              {result.sources.map((s, i) =>
                <div className="source" key={i}>
                  <div className="fileIcon">{s.kind === "class" ? "C" : "ƒ"}</div>
                  <div><b>{s.symbol}</b><span>{s.file}:{s.lines}</span></div>
                  <strong>{s.score}</strong>
                </div>
              )}
            </article>
          </div>}
        </section>}

        {tab === "graph" && <section className="panel graph">
          <div className="panelHead"><span>DEPENDENCY GRAPH</span><em>{repo?.graph?.edges?.length || 0} edges</em></div>
          <div className="nodes">
            {repo?.graph?.nodes?.filter(n => n.type === "file").map(n => <div className="node" key={n.id}>{n.id}</div>)}
          </div>
          <div className="edges">
            {repo?.graph?.edges?.map((e,i) => <div className="edge" key={i}><b>{e.source}</b><span>→ {e.type} →</span><b>{e.target}</b></div>)}
          </div>
        </section>}

        {tab === "impact" && <section>
          <div className="queryBox compact">
            <input value={question} onChange={e => setQuestion(e.target.value)} placeholder="Try: UserService, create_user, auth.py" />
            <button className="primary" onClick={runImpact}>Analyze Impact →</button>
          </div>
          {impact && <div className="panel">
            <div className="panelHead"><span>MATCHED SYMBOLS</span><em>{impact.matched_symbols.length}</em></div>
            {impact.matched_symbols.map((s,i) => <div className="impactRow" key={i}><b>{s.name}</b><span>{s.kind} · {s.file}:{s.line}</span></div>)}
            <div className="panelHead second"><span>AFFECTED FILES</span><em>{impact.count}</em></div>
            {impact.affected_files.map((x,i) => <div className="impactRow" key={i}><b>{x.file}</b><span>{x.reason}</span></div>)}
          </div>}
        </section>}

        {tab === "eval" && <section>
          <button className="primary runEval" onClick={runEvaluation}>Run Evaluation →</button>
          {evaluation && <>
            <div className="metrics">
              <div><span>Mean Precision@5</span><b>{evaluation.mean_precision_at_5}</b></div>
              <div><span>Mean Recall@5</span><b>{evaluation.mean_recall_at_5}</b></div>
              <div><span>Mean MRR</span><b>{evaluation.mean_mrr}</b></div>
            </div>
            <div className="panel">
              <div className="panelHead"><span>TEST CASES</span><em>{evaluation.cases.length}</em></div>
              {evaluation.cases.map((c,i) => <div className="evalRow" key={i}>
                <b>{c.question}</b>
                <span>P@5 {c.precision_at_5} · R@5 {c.recall_at_5} · MRR {c.mrr}</span>
              </div>)}
              <p className="note">{evaluation.faithfulness_note}</p>
            </div>
          </>}
        </section>}
      </main>
    </div>
  )
}

createRoot(document.getElementById("root")).render(<App />)
