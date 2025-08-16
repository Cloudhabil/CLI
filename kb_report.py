import os
import datetime as dt
from pathlib import Path
from kb import _connect
from integrations.drive_client import upload_file

SECTIONS = {
    'Finance': ['CFO', 'finance'],
    'Ops/HR': ['COO', 'CHRO', 'ops', 'hr'],
    'Technology': ['CTO', 'CIO', 'tech'],
    'Marketing/Product': ['CMO', 'CPO', 'marketing', 'product'],
    'Policy/Admin': ['policy', 'admin', 'memo']
}


def load_entries():
    conn = _connect()
    cur = conn.cursor()
    week_ago = dt.datetime.utcnow().timestamp() - 7*86400
    cur.execute('SELECT ts, kind, topic, data FROM entries WHERE ts>? ORDER BY ts', (week_ago,))
    rows = cur.fetchall()
    conn.close()
    return rows


def group_entries(rows):
    groups = {k: [] for k in SECTIONS}
    for ts, kind, topic, data in rows:
        added = False
        for section, keys in SECTIONS.items():
            if topic and any(k.lower() in topic.lower() for k in keys):
                groups[section].append((ts, topic, data))
                added = True
                break
        if not added:
            groups['Policy/Admin'].append((ts, topic, data))
    return groups


def write_report(groups):
    now = dt.datetime.utcnow()
    week = now.strftime('%Y-%W')
    path = Path('reports')
    path.mkdir(parents=True, exist_ok=True)
    file = path / f'{week}.md'
    with open(file, 'w', encoding='utf-8') as f:
        for section, items in groups.items():
            f.write(f"## {section}\n")
            for ts, topic, data in items:
                f.write(f"- {dt.datetime.fromtimestamp(ts).isoformat()} | {topic} | {data}\n")
            f.write('\n')
    return file


def main():
    rows = load_entries()
    groups = group_entries(rows)
    file = write_report(groups)
    parent = os.environ.get('GDRIVE_PARENT_FOLDER_ID')
    if parent:
        upload_file(str(file), parent)
    print(file)

if __name__ == '__main__':
    main()
