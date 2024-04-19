# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provides persistence for runner tokens."""

import os

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    """Base class for ORM models."""


class OneTimeToken(Base):
    """Stores one time tokens.

    Attributes:
        vaue: The token.
    """

    __tablename__ = "one_time_token"

    value: Mapped[str] = mapped_column(sa.String(30), primary_key=True)


db_connect_str = os.getenv("POSTGRESQL_DB_CONNECT_STRING")
engine: sa.Engine
if db_connect_str:
    engine = create_engine(db_connect_str)
else:
    # Using sqlite means that this app can only be used with a single worker. This reduces deployment
    # complexity as a database would otherwise be required.
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)


def add_token(token: str) -> None:
    """Add a new token.

    Args:
        token: The token to add.
    """
    with Session(engine) as session:
        token = OneTimeToken(value=token)
        session.add(token)
        session.commit()


def check_token(token: str) -> bool:
    """Check whether a token is valid.

    Args:
        token: The token to check.

    Returns:
        Whether the token is valid.
    """
    with Session(engine) as session:
        token_in_db = session.query(OneTimeToken.value).filter_by(value=token).first() is not None

        if not token_in_db:
            return False

        session.query(OneTimeToken).filter_by(value=token).delete()
        session.commit()

    return True
