#!/usr/bin/env python3
"""
blog 레포지토리의 마크다운 파일에 front matter를 자동으로 추가/보완합니다.

처리 규칙:
- front matter가 아예 없으면 → title/date/layout/permalink 전부 자동 생성
- front matter가 있지만 permalink 없으면 → permalink만 추가
- permalink가 이미 있으면 → 스킵

title  : 파일 내 첫 번째 '# 제목' 줄에서 추출 (없으면 파일명 사용)
date   : 파일명 앞 YYYY-MM-DD 패턴에서 추출 (없으면 오늘 날짜)
permalink: /blog/YYYYMMDD-{파일명 md5 앞 6자리}/
"""

import os
import re
import hashlib
from datetime import date as today_date

REPORT_DIR = "."
PERMALINK_PREFIX = "/blog/"


# ── 헬퍼 ──────────────────────────────────────────────

def extract_title_from_body(content):
    """본문의 첫 번째 # 제목 줄에서 텍스트 추출."""
    for line in content.splitlines():
        m = re.match(r'^#\s+(.+)', line)
        if m:
            return m.group(1).strip()
    return None


def extract_date_from_filename(filename):
    """파일명 앞부분의 YYYY-MM-DD 패턴 추출."""
    m = re.match(r'(\d{4}-\d{2}-\d{2})', filename)
    return m.group(1) if m else str(today_date.today())


def make_permalink(filename):
    """파일명 → /blog/YYYYMMDD-{hash6}/"""
    m = re.match(r'(\d{4}-\d{2}-\d{2})', filename)
    date_str = m.group(1).replace('-', '') if m else 'report'
    h = hashlib.md5(filename.encode('utf-8')).hexdigest()[:6]
    return f"{PERMALINK_PREFIX}{date_str}-{h}/"


def build_frontmatter(title, date_str, permalink):
    return (
        f"---\n"
        f"layout: report\n"
        f"title: \"{title}\"\n"
        f"permalink: {permalink}\n"
        f"date: {date_str}\n"
        f"---\n"
    )


# ── front matter 파싱 ─────────────────────────────────

def split_frontmatter(content):
    """(frontmatter_str | None, body_str) 반환."""
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            fm = content[3:end]
            body = content[end + 3:]
            return fm, body
    return None, content


def has_key(fm, key):
    return bool(re.search(rf'^\s*{key}\s*:', fm, re.MULTILINE))


def inject_key(fm, key, value):
    """front matter 문자열에 key: value 줄 추가 (layout: 바로 다음)."""
    lines = fm.split('\n')
    insert_idx = 1
    for i, line in enumerate(lines):
        if line.strip().startswith('layout:'):
            insert_idx = i + 1
            break
    lines.insert(insert_idx, f"{key}: {value}")
    return '\n'.join(lines)


# ── 파일 처리 ─────────────────────────────────────────

def process_file(filepath):
    filename = os.path.basename(filepath)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    fm, body = split_frontmatter(content)

    # ── Case 1: front matter 자체가 없음 ──────────────
    if fm is None:
        title = extract_title_from_body(body) or filename.replace('.md', '')
        date_str = extract_date_from_filename(filename)
        permalink = make_permalink(filename)
        new_content = build_frontmatter(title, date_str, permalink) + body
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  CREATED front matter → {filename} (permalink: {permalink})")
        return True

    # ── Case 2: front matter 있음, permalink 없음 ─────
    if not has_key(fm, 'permalink'):
        permalink = make_permalink(filename)
        new_fm = inject_key(fm, 'permalink', permalink)
        new_content = f"---{new_fm}---{body}"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ADDED permalink {permalink} → {filename}")
        return True

    # ── Case 3: 이미 permalink 있음 ───────────────────
    print(f"  SKIP (already complete): {filename}")
    return False


def main():
    changed = False
    for filename in sorted(os.listdir(REPORT_DIR)):
        if not filename.endswith('.md'):
            continue
        if filename == 'index.md':
            continue
        filepath = os.path.join(REPORT_DIR, filename)
        if process_file(filepath):
            changed = True

    print()
    print("✅ 완료 — 변경 있음." if changed else "✅ 완료 — 변경 없음.")


if __name__ == "__main__":
    main()
