import sqlite3
import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATHS = [
    os.path.join(BASE, 'expenses.db'),
    os.path.join(BASE, 'instance', 'expenses.db'),
]

def inspect(db_path):
    db_path = os.path.abspath(db_path)
    print('DB file:', db_path)
    if not os.path.exists(db_path):
        print('Database file not found')
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') ORDER BY name;")
    rows = cur.fetchall()
    tables = [r[0] for r in rows if r[0] != 'sqlite_sequence']
    print('\nFound tables/views:')
    for t in tables:
        print('-', t)

    for t in tables:
        print(f"\nSchema for {t}:")
        cur.execute(f"PRAGMA table_info('{t}')")
        cols = cur.fetchall()
        if not cols:
            print('  (no columns)')
            continue
        for c in cols:
            cid, name, ctype, notnull, dflt_value, pk = c
            print(f"  - {name} {ctype} notnull={bool(notnull)} pk={bool(pk)} default={dflt_value}")

        try:
            cur.execute(f"SELECT COUNT(*) FROM '{t}'")
            cnt = cur.fetchone()[0]
        except Exception as e:
            cnt = f'error: {e}'
        print('  Row count:', cnt)

    conn.close()

if __name__ == '__main__':
    for p in DB_PATHS:
        if os.path.exists(p):
            inspect(p)
            break
    else:
        print('No database found in any expected locations:')
        for p in DB_PATHS:
            print(' -', p)
