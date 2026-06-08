import os
import sys

import mysql.connector

from config import Config


def parse_mysql_uri(uri: str) -> dict:
    # Expected pattern like:
    # mysql+mysqlconnector://user:pass@host:port/dbname
    if not uri.startswith("mysql+"):
        raise ValueError(f"Unsupported DATABASE_URL format: {uri}")

    # Strip the SQLAlchemy driver prefix: mysql+mysqlconnector:// -> mysql://
    uri2 = uri.replace("mysql+mysqlconnector://", "mysql://", 1)

    from urllib.parse import urlparse

    u = urlparse(uri2)
    return {
        "host": u.hostname or "localhost",
        "port": u.port or 3306,
        "user": u.username or "root",
        "password": u.password or "",
        "database": (u.path or "/").lstrip("/"),
    }


def exec_sql_script_lines(conn, script: str):
    """Execute a .sql script line-by-line with statement buffering.

    This avoids failure from naive ';\n' splitting, but still assumes
    your SQL doesn't contain ';' inside string literals.
    """
    cur = conn.cursor()
    buf = ""
    try:
        for raw_line in script.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("--"):
                continue

            buf += raw_line + "\n"

            # execute when statement terminator reached
            if line.endswith(";"):
                stmt = buf.strip()
                buf = ""
                cur.execute(stmt)

        # tail
        tail = buf.strip()
        if tail:
            cur.execute(tail)
    finally:
        cur.close()


def main():
    schema_path = os.path.join(os.path.dirname(__file__), "database", "schema.sql")
    seed_path = os.path.join(os.path.dirname(__file__), "database", "seed.sql")

    if not os.path.exists(schema_path):
        print(f"Missing file: {schema_path}")
        sys.exit(1)

    if not os.path.exists(seed_path):
        print(f"Missing file: {seed_path}")
        sys.exit(1)

    params = parse_mysql_uri(Config.SQLALCHEMY_DATABASE_URI)

    print("Connecting to MySQL:")
    print(
        f"  host={params['host']} port={params['port']} user={params['user']} db={params['database']}"
    )

    conn = mysql.connector.connect(**params)
    try:
        print("Executing schema.sql ...")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = f.read()
        exec_sql_script_lines(conn, schema)

        # seed.sql in this repo contains placeholder '... abbreviated for brevity'
        # blocks that are not valid SQL.
        # Skip seed to allow schema-only rebuild.
        print("Skipping seed.sql (schema-only reset).")

        conn.commit()
        print("SUCCESS: database schema reset complete (seed skipped).")
    except Exception as e:
        conn.rollback()
        print("FAILED while executing SQL:", e)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()

