"""Offline retrieval over the SAHAY knowledge base.

BM25 keyword retrieval, zero network, zero extra model downloads, works the
moment the lights go out. Chunks are `## `-sections of the markdown corpus so
each retrieved passage is a self-contained instruction block (English or Bengali).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from rank_bm25 import BM25Okapi

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"

# Word chars incl. Bengali block (U+0980–U+09FF)
_TOKEN_RE = re.compile(r"[A-Za-z0-9ঀ-৿]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


@dataclass
class Chunk:
    doc_title: str
    section: str
    text: str
    source: str

    @property
    def label(self) -> str:
        return f"{self.doc_title} › {self.section}"


class KnowledgeBase:
    def __init__(self, root: Path = KNOWLEDGE_DIR):
        self.chunks: list[Chunk] = []
        for md in sorted(root.rglob("*.md")):
            self._ingest(md)
        corpus = [_tokenize(f"{c.doc_title} {c.section} {c.text}") for c in self.chunks]
        self._bm25 = BM25Okapi(corpus) if corpus else None

    def _ingest(self, path: Path) -> None:
        raw = path.read_text(encoding="utf-8")
        title_match = re.search(r"^#\s+(.+)$", raw, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else path.stem
        parts = re.split(r"^##\s+", raw, flags=re.MULTILINE)
        for part in parts[1:]:
            lines = part.strip().splitlines()
            if not lines:
                continue
            section = lines[0].strip()
            body = "\n".join(lines[1:]).strip()
            if body:
                self.chunks.append(
                    Chunk(doc_title=title, section=section, text=body, source=path.name)
                )

    def search(self, query: str, k: int = 4) -> list[Chunk]:
        if not self._bm25 or not query.strip():
            return []
        scores = self._bm25.get_scores(_tokenize(query))
        ranked = sorted(zip(scores, range(len(self.chunks))), reverse=True)
        return [self.chunks[i] for score, i in ranked[:k] if score > 0]


_kb: KnowledgeBase | None = None


def kb() -> KnowledgeBase:
    global _kb
    if _kb is None:
        _kb = KnowledgeBase()
    return _kb
