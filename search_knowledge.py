#!/usr/bin/env python3
"""
MCPT Project Knowledge Search Tool
Usage:
  python3 search_knowledge.py "DSL file generation"
  python3 search_knowledge.py --category api-contract
  python3 search_knowledge.py --recent 10
  python3 search_knowledge.py --categories
  python3 search_knowledge.py --number 5
"""
import sqlite3
import sys
import os
import argparse

DB_PATH = os.path.join(os.path.dirname(__file__), 'project_knowledge.db')

def get_db():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Knowledge DB not found at {DB_PATH}")
        print("Run: python3 build_knowledge_db.py")
        sys.exit(1)
    return sqlite3.connect(DB_PATH)

def search_text(query):
    conn = get_db()
    rows = conn.execute("""
        SELECT k.id, k.category, k.title, k.content, k.tags
        FROM knowledge_fts f
        JOIN knowledge k ON k.id = f.rowid
        WHERE knowledge_fts MATCH ?
        ORDER BY rank
        LIMIT 20
    """, (query,)).fetchall()
    conn.close()
    if not rows:
        print(f"No results for: {query}")
        return
    for id_, cat, title, content, tags in rows:
        print(f"\n{'='*70}")
        print(f"[#{id_}] [{cat}] {title}")
        if tags:
            print(f"Tags: {tags}")
        print(f"{'-'*70}")
        print(content[:800] + ('...' if len(content) > 800 else ''))

def list_categories():
    conn = get_db()
    rows = conn.execute("""
        SELECT category, COUNT(*) as cnt
        FROM knowledge
        GROUP BY category
        ORDER BY cnt DESC
    """).fetchall()
    conn.close()
    print(f"\n{'Category':<30} {'Entries':>7}")
    print('-' * 40)
    for cat, cnt in rows:
        print(f"  {cat:<28} {cnt:>7}")

def by_category(cat):
    conn = get_db()
    rows = conn.execute("""
        SELECT id, title, content
        FROM knowledge
        WHERE LOWER(category) = LOWER(?)
        ORDER BY id
    """, (cat,)).fetchall()
    conn.close()
    if not rows:
        print(f"No entries for category: {cat}")
        return
    print(f"\n=== Category: {cat} ({len(rows)} entries) ===")
    for id_, title, content in rows:
        print(f"\n  #{id_}: {title}")
        print(f"  {content[:300]}{'...' if len(content) > 300 else ''}")

def by_number(n):
    conn = get_db()
    row = conn.execute("SELECT * FROM knowledge WHERE id = ?", (n,)).fetchone()
    conn.close()
    if not row:
        print(f"No entry #{n}")
        return
    id_, cat, title, content, tags, source, created = row
    print(f"\n{'='*70}")
    print(f"[#{id_}] [{cat}] {title}")
    print(f"Source: {source} | Created: {created}")
    if tags: print(f"Tags: {tags}")
    print(f"{'-'*70}")
    print(content)

def recent(n):
    conn = get_db()
    rows = conn.execute("""
        SELECT id, category, title, created_at
        FROM knowledge
        ORDER BY id DESC
        LIMIT ?
    """, (n,)).fetchall()
    conn.close()
    print(f"\n=== Last {n} entries ===")
    for id_, cat, title, created in rows:
        print(f"  #{id_:3} [{cat:<20}] {title[:55]}")

def main():
    parser = argparse.ArgumentParser(description='Search MCPT knowledge base')
    parser.add_argument('query', nargs='?', help='Full-text search query')
    parser.add_argument('--category', '-c', help='Filter by category')
    parser.add_argument('--number', '-n', type=int, help='Get entry by number')
    parser.add_argument('--recent', '-r', type=int, metavar='N', help='Show last N entries')
    parser.add_argument('--categories', action='store_true', help='List all categories')
    args = parser.parse_args()

    if args.categories:
        list_categories()
    elif args.category:
        by_category(args.category)
    elif args.number:
        by_number(args.number)
    elif args.recent:
        recent(args.recent)
    elif args.query:
        search_text(args.query)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
