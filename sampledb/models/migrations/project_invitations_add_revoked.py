# coding: utf-8
"""
Add revoked columns to project_invitations table.
"""

import flask_sqlalchemy

from .utils import table_has_column


def run(db: flask_sqlalchemy.SQLAlchemy) -> bool:
    # Skip migration by condition
    if table_has_column('project_invitations', 'revoked'):
        return False

    # Perform migration
    db.session.execute(db.text("""
        ALTER TABLE project_invitations
        ADD revoked BOOLEAN DEFAULT FALSE NOT NULL
    """))
    return True
