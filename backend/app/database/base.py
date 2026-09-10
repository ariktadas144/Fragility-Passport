"""Declarative base shared by every SQLAlchemy model.

Importing this module (indirectly, via app.models) is what registers all
model classes on Base.metadata so create_all() picks them up.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
