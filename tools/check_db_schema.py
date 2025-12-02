import re
import mysql.connector
import argparse
from typing import Dict, List

# Simple parser for database_schema.sql to extract tables and column names

def parse_schema_sql(file_path: str) -> Dict[str, List[str]]:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    tables = {}
    # Robust scan for CREATE TABLE ... ( ... ) blocks by scanning parentheses
    pos = 0
    content_upper = content.upper()
    while True:
        idx = content_upper.find('CREATE TABLE', pos)
        if idx == -1:
            break
        # find table name
        # move past 'CREATE TABLE'
        idx_name_start = idx + len('CREATE TABLE')
        # skip whitespace
        while idx_name_start < len(content) and content[idx_name_start].isspace():
            idx_name_start += 1
        # read table name (may be backquoted)
        name_start = idx_name_start
        while name_start < len(content) and content[name_start] in ('`', ' '):
            name_start += 1
        name_end = name_start
        while name_end < len(content) and (content[name_end].isalnum() or content[name_end] in ('_', '`')):
            name_end += 1
        table_name = content[name_start:name_end].strip('`')
        # find opening parenthesis '('
        open_idx = content.find('(', name_end)
        if open_idx == -1:
            pos = name_end
            continue
        # find matching closing parenthesis
        depth = 0
        i = open_idx
        while i < len(content):
            if content[i] == '(':
                depth += 1
            elif content[i] == ')':
                depth -= 1
                if depth == 0:
                    close_idx = i
                    break
            i += 1
        else:
            pos = open_idx + 1
            continue
        body = content[open_idx+1:close_idx]
        cols = []
        for line in body.split('\n'):
            line = line.strip()
            if not line:
                continue
            # strip trailing comma/; and comments
            if '--' in line:
                line = line.split('--', 1)[0].strip()
            if line.endswith(','):
                line = line[:-1].rstrip()
            if not line:
                continue
            # skip index/constraint lines
            if line.upper().startswith(('PRIMARY KEY', 'UNIQUE KEY', 'KEY', 'INDEX', 'FOREIGN KEY', 'CONSTRAINT')):
                continue
            # take first token as column name if it looks like a column def
            parts = line.split()
            if not parts:
                continue
            potential_name = parts[0].strip('`').strip()
            # avoid lines like `ENGINE=` etc
            if potential_name.upper().startswith(('ENGINE', 'COMMENT')):
                continue
            # if the definition looks like `column_name TYPE` then accept
            if len(parts) >= 2 and re.match(r'^[a-zA-Z0-9_]+$', potential_name):
                cols.append(potential_name)
        tables[table_name] = cols
        pos = close_idx + 1
    return tables


def parse_views_sql(file_path: str) -> List[str]:
    """Parse CREATE VIEW statements and return a list of view names."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    view_names = []
    # basic regex to find CREATE VIEW <name> or CREATE OR REPLACE VIEW <name>
    rv = re.compile(r"CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+([a-zA-Z0-9_]+)", re.I)
    for m in rv.finditer(content):
        view_names.append(m.group(1))
    return view_names


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='203.255.78.58')
    parser.add_argument('--port', default=9003, type=int)
    parser.add_argument('--user', default='user29')
    parser.add_argument('--password', default='123')
    parser.add_argument('--database', default='graduation_system')
    parser.add_argument('--schema-sql', default='../database_schema.sql')
    args = parser.parse_args()

    expected = parse_schema_sql(args.schema_sql)
    expected_views = parse_views_sql(args.schema_sql)
    # Add any views into the expected dict as well so views are not reported as extra tables
    for v in expected_views:
        if v not in expected:
            expected[v] = []

    print('Parsed expected tables from', args.schema_sql)
    for t, cols in expected.items():
        print(f'  {t}: {len(cols)} columns')

    conn = mysql.connector.connect(host=args.host, port=args.port, user=args.user, password=args.password, database=args.database)
    cur = conn.cursor()

    cur.execute('SHOW TABLES')
    actual_tables = [row[0] for row in cur.fetchall()]

    print('\nFound tables in DB:', len(actual_tables))
    for t in actual_tables:
        print(' -', t)

    # Compare expected vs actual
    missing_tables = [t for t in expected.keys() if t not in actual_tables]
    extra_tables = [t for t in actual_tables if t not in expected.keys()]

    print('\nMissing tables (in expected but not in DB):', len(missing_tables))
    for t in missing_tables:
        print(' *', t)

    print('\nExtra tables (in DB but not in expected):', len(extra_tables))
    for t in extra_tables:
        print(' -', t)

    expected_views_set = set(expected_views)
    # For tables present in both, check columns (skip views)
    for t in expected.keys():
        if t not in actual_tables:
            continue
        if t in expected_views_set:
            # skip column check for views
            continue
        cur.execute(f"SHOW COLUMNS FROM {t}")
        actual_cols = [r[0] for r in cur.fetchall()]
        expected_cols = expected[t]
        missing_cols = [c for c in expected_cols if c not in actual_cols]
        extra_cols = [c for c in actual_cols if c not in expected_cols]

        if missing_cols or extra_cols:
            print(f"\nTable '{t}' schema mismatch:")
            if missing_cols:
                print(' Missing columns:', missing_cols)
            if extra_cols:
                print(' Extra columns:', extra_cols)

    cur.close()
    conn.close()

    print('\nDone.')
