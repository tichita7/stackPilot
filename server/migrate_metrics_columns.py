"""
Migration Script: Add duration_ms and success columns to sessions table.

This script is explicit, idempotent, and standalone.
It is NOT executed automatically on startup.
To run this migration manually in deployment environments:
    python server/migrate_metrics_columns.py
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load server environment variables
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SERVER_DIR, ".env"))


def run_migration():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    print("Connecting to PostgreSQL database...")
    conn = None
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()

        print("Executing migration: Adding duration_ms and success columns to sessions...")
        cur.execute("""
            ALTER TABLE sessions
            ADD COLUMN IF NOT EXISTS duration_ms INT DEFAULT NULL;

            ALTER TABLE sessions
            ADD COLUMN IF NOT EXISTS success BOOLEAN DEFAULT NULL;
        """)
        conn.commit()

        # Verification step
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'sessions' AND column_name IN ('duration_ms', 'success');
        """)
        verified = {row[0]: (row[1], row[2]) for row in cur.fetchall()}
        cur.close()

        if "duration_ms" in verified and "success" in verified:
            print(f"SUCCESS: Verified columns in sessions table: {verified}")
            print("Migration completed successfully.")
        else:
            print(f"WARNING: Verification incomplete. Found columns: {list(verified.keys())}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"ERROR: Migration failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    run_migration()
