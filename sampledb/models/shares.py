# coding: utf-8
"""

"""

import typing
import datetime

from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship

from .. import db
from .components import Component
from .objects import Objects


class ObjectShare(db.Model):  # type: ignore
    __tablename__ = 'object_shares'

    object_id = db.Column(db.Integer, db.ForeignKey(Objects.object_id_column), nullable=False, primary_key=True)
    component_id = db.Column(db.Integer, db.ForeignKey(Component.id), nullable=False, primary_key=True)
    policy = db.Column(postgresql.JSONB, nullable=False)
    utc_datetime = db.Column(db.DateTime, nullable=False)
    component = relationship('Component')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = relationship('User')
    import_status = db.Column(postgresql.JSONB)

    def __init__(
            self,
            object_id: int,
            component_id: int,
            policy: typing.Dict[str, typing.Any],
            utc_datetime: typing.Optional[datetime.datetime] = None,
            user_id: typing.Optional[int] = None
    ) -> None:
        self.object_id = object_id
        self.component_id = component_id
        self.policy = policy
        if utc_datetime is None:
            self.utc_datetime = datetime.datetime.utcnow()
        self.user_id = user_id

    def __repr__(self) -> str:
        return f'<{type(self).__name__}(object_id={self.object_id}, component_id={self.component_id}, policy={self.policy}, utc_datetime={self.utc_datetime})>'
