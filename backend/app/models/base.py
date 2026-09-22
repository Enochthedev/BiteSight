"""Declarative base and shared column helpers for all ORM models."""

import uuid

from sqlalchemy import Column, DateTime, func
from sqlalchemy import Uuid as _Uuid
from sqlalchemy.orm import declarative_base
from sqlalchemy.types import TypeDecorator

Base = declarative_base()


class UUID(TypeDecorator):
    """UUID column that also accepts string ids (e.g. a JWT "sub").

    Native UUID on Postgres, CHAR(32) on SQLite (used by the test suite).
    """

    impl = _Uuid
    cache_ok = True

    def __init__(self, as_uuid: bool = True):
        super().__init__(as_uuid=as_uuid)

    def process_bind_param(self, value, dialect):
        if value is None or isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


def uuid_pk() -> Column:
    """UUID primary key, generated in Python so it works on Postgres and SQLite."""
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    """created_at / updated_at columns matching the Alembic migrations."""

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
