from hnet.dynamic_chunker import DynamicChunker, summarize_long_text


def test_chunker_respects_budget():
    text = " ".join([f"Sentence {i}." for i in range(200)])
    ch = DynamicChunker(max_tokens=200, overlap_tokens=40)
    parts = ch.chunk(text)
    assert len(parts) >= 2
    assert all(len(p.split()) < 400 for p in parts)


def test_hierarchical_summarize_reduces_size():
    text = " ".join([f"This is a long sentence number {i}." for i in range(500)])
    s = summarize_long_text(text, summarize=lambda x: x[:120], max_tokens=300)
    assert len(s) <= 600
