import json
from pathlib import Path

import kb


def test_kb_entry_logging(tmp_path):
    """Persist and query knowledge-base entries."""
    data_file = Path(__file__).parent / "data" / "kb_entries.json"
    entries = json.loads(data_file.read_text())
    kb.DB_PATH = tmp_path / "kb.db"
    for entry in entries:
        kb.add_entry(**entry)
    last_entries = kb.last(2)
    assert len(last_entries) == 2
    search_entries = kb.search("hello")
    assert any("hello" in r["data"] for r in search_entries)
    first_id = last_entries[0]["id"]
    entry = kb.get(first_id)
    assert entry["id"] == first_id
