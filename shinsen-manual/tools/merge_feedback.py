#!/usr/bin/env python3
"""Merge tryout CSV files (downloaded from the manual's "ดาวน์โหลดผล") into feedback.js.

Usage: python3 tools/merge_feedback.py file1.csv [file2.csv ...]
A "Solution" (or "คำตอบจากทีม") column becomes the team reply shown under the comment.
Rows are keyed by (round, tester, topic number); a newer export of the same tester
replaces that tester's earlier row for the topic, so re-sent files never duplicate.
"""
import csv, json, re, sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / 'feedback.js'
PREFIX, SUFFIX = 'window.SHINSEN_FEEDBACK = ', ';\n'

def load():
    if not OUT.exists():
        return []
    s = OUT.read_text(encoding='utf-8').strip()
    s = s[s.index('['):s.rindex(']') + 1]
    return json.loads(s)

def rows(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            topic = (r.get('หัวข้อ') or '').strip()
            m = re.match(r'(\d+(?:\.\d+)*)\s+(.*)', topic, re.S)
            if not m:
                continue
            yield {
                'round': (r.get('รอบ') or '').strip(),
                'name': (r.get('ชื่อผู้ทดลอง') or '').strip().rstrip('.'),
                'n': m.group(1), 'title': m.group(2).strip(),
                'status': (r.get('สถานะ') or '').strip(),
                'comment': (r.get('ความเห็น') or '').replace('\r', '').strip(),
                'at': (r.get('เวลาที่บันทึก') or '').strip(),
                'reply': (r.get('Solution') or r.get('คำตอบจากทีม') or '').replace('\r', '').strip(),
            }

def main(files):
    data = {(x['round'], x['name'], x['n']): x for x in load()}
    added = 0
    for f in files:
        for r in rows(f):
            k = (r['round'], r['name'], r['n'])
            if k not in data:
                added += 1
            elif not r['reply'] and data[k].get('reply'):
                r['reply'] = data[k]['reply']  # keep the team's earlier answer
            if not r['reply']:
                r.pop('reply')
            data[k] = r
    def key(x):
        return ([int(p) for p in x['n'].split('.')], x['round'], x['name'])
    out = sorted(data.values(), key=key)
    OUT.write_text(PREFIX + json.dumps(out, ensure_ascii=False, indent=1) + SUFFIX, encoding='utf-8')
    print(f'{len(out)} rows ({added} new) -> {OUT}')

if __name__ == '__main__':
    main(sys.argv[1:])
