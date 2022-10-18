# coding: utf-8
"""
Add the admin_only column to the actions table.
"""

import os

MIGRATION_INDEX = 120
MIGRATION_NAME, _ = os.path.splitext(os.path.basename(__file__))


def run(db):
    client_column_names = db.session.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'actions'
    """).fetchall()
    if ('admin_only',) in client_column_names:
        return False

    # Perform migration
    db.session.execute("""
        ALTER TABLE actions
        ADD admin_only boolean NOT NULL DEFAULT(FALSE)
    """)
    return True