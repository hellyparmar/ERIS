"""
SQLAlchemy Declarative Base

This module defines the declarative base for all SQLAlchemy ORM models
"""

from sqlalchemy.orm import declarative_base

class BaseModel:
    pass

Base = declarative_base(cls=BaseModel)
