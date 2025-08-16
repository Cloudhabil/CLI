from __future__ import annotations
from typing import List, Callable

try:
    import tiktoken  # type: ignore
except Exception:  # pragma: no cover
    tiktoken = None  # type: ignore[assignment]


def _token_count(text: str, model: str | None = None) -> int:
    if tiktoken:
        try:
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            pass
    w = max(1, len(text.split()))
    return int(w / 0.75)


class DynamicChunker:
    """H-Net style dynamic chunking with soft overlap and budget awareness."""

    def __init__(self, max_tokens: int = 800, overlap_tokens: int = 80):
        if overlap_tokens >= max_tokens:
            raise ValueError("overlap_tokens must be < max_tokens")
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def chunk(self, text: str) -> List[str]:
        import re

        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        chunks: List[str] = []
        cur: List[str] = []
        cur_tokens = 0
        for s in sentences:
            t = _token_count(s)
            if t > self.max_tokens:
                chunks.extend(self._split_long_sentence(s))
                continue
            if cur_tokens + t <= self.max_tokens:
                cur.append(s)
                cur_tokens += t
            else:
                if cur:
                    chunks.append(" ".join(cur))
                    overlap = self._take_tail_tokens(cur, self.overlap_tokens)
                    cur = overlap + [s]
                    cur_tokens = _token_count(" ".join(cur))
                else:
                    chunks.append(s)
                    cur = []
                    cur_tokens = 0
        if cur:
            chunks.append(" ".join(cur))
        return chunks

    def _split_long_sentence(self, s: str) -> List[str]:
        words = s.split()
        out, cur = [], []
        for w in words:
            cur.append(w)
            if _token_count(" ".join(cur)) >= self.max_tokens:
                out.append(" ".join(cur))
                cur = []
        if cur:
            out.append(" ".join(cur))
        return out

    def _take_tail_tokens(self, parts: List[str], budget: int) -> List[str]:
        out: List[str] = []
        for s in reversed(parts):
            out.insert(0, s)
            if _token_count(" ".join(out)) >= budget:
                break
        return out


def summarize_long_text(
    text: str,
    summarize: Callable[[str], str],
    max_tokens: int = 800,
    overlap_tokens: int = 80,
) -> str:
    """Dynamic chunk then summarize with provided callback."""
    ch = DynamicChunker(max_tokens=max_tokens, overlap_tokens=overlap_tokens)
    summaries = [summarize(c) for c in ch.chunk(text)]
    joined = "\n".join(summaries)
    if _token_count(joined) > max_tokens:
        return summarize(joined)
    return joined
