from pathlib import Path
import ast
import re
from dataclasses import dataclass, asdict

@dataclass
class Chunk:
    id: str
    file: str
    start_line: int
    end_line: int
    kind: str
    symbol: str
    text: str

class CodeIndexer:
    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir
        self.chunks = []
        self.files = []
        self.symbols = []
        self.graph = {"nodes": [], "edges": []}
        self.file_texts = {}

    def build(self):
        self.chunks = []
        self.files = []
        self.symbols = []
        self.graph = {"nodes": [], "edges": []}
        self.file_texts = {}

        paths = sorted(self.repo_dir.rglob("*.py"))
        for path in paths:
            rel = path.relative_to(self.repo_dir).as_posix()
            text = path.read_text(encoding="utf-8")
            self.files.append(rel)
            self.file_texts[rel] = text
            self._parse_file(rel, text)

        self._build_edges()

    def _parse_file(self, rel, text):
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return

        self.graph["nodes"].append({"id": rel, "type": "file"})

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                kind = "class" if isinstance(node, ast.ClassDef) else "function"
                symbol = node.name
                start = getattr(node, "lineno", 1)
                end = getattr(node, "end_lineno", start)
                lines = text.splitlines()
                body = "\n".join(lines[start-1:end])
                chunk_id = f"{rel}:{start}-{end}"
                self.chunks.append(Chunk(
                    chunk_id, rel, start, end, kind, symbol,
                    f"{kind} {symbol} in {rel}\n{body}"
                ))
                self.symbols.append({"name": symbol, "kind": kind, "file": rel, "line": start})
                self.graph["nodes"].append({
                    "id": f"{rel}:{symbol}", "type": kind, "file": rel
                })

    def _build_edges(self):
        # Import edges
        for rel, text in self.file_texts.items():
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        target = self._resolve_module(alias.name)
                        if target:
                            self.graph["edges"].append({"source": rel, "target": target, "type": "imports"})
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        target = self._resolve_module(node.module)
                        if target:
                            self.graph["edges"].append({"source": rel, "target": target, "type": "imports"})

        # Lightweight symbol reference edges.
        names = {s["name"]: s["file"] for s in self.symbols}
        for rel, text in self.file_texts.items():
            for name, target_file in names.items():
                if target_file != rel and re.search(rf"\b{re.escape(name)}\b", text):
                    self.graph["edges"].append({
                        "source": rel, "target": target_file, "type": "references", "symbol": name
                    })

    def _resolve_module(self, module):
        candidates = [
            f"{module.replace('.', '/')}.py",
            f"{module.replace('.', '/')}/__init__.py",
        ]
        for c in candidates:
            if c in self.files:
                return c
        return None

    def search_documents(self):
        return [asdict(c) for c in self.chunks]

    def impact_analysis(self, target):
        matches = []
        target_lower = target.lower()
        for s in self.symbols:
            if target_lower in s["name"].lower() or target_lower in s["file"].lower():
                matches.append(s)

        affected = []
        for m in matches:
            file = m["file"]
            for edge in self.graph["edges"]:
                if edge["target"] == file:
                    affected.append({
                        "file": edge["source"],
                        "reason": f"{edge['type']} dependency on {m['name']}",
                        "symbol": m["name"]
                    })

        # Also search direct textual references.
        for m in matches:
            for file, text in self.file_texts.items():
                if file != m["file"] and re.search(rf"\b{re.escape(m['name'])}\b", text):
                    item = {"file": file, "reason": f"textual reference to {m['name']}", "symbol": m["name"]}
                    if item not in affected:
                        affected.append(item)

        return {
            "target": target,
            "matched_symbols": matches,
            "affected_files": affected,
            "count": len(affected),
        }
