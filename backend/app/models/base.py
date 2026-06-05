"""
SQLAlchemy Declarative Base

This module defines the declarative base for all SQLAlchemy ORM models
"""

from sqlalchemy import Column, DateTime, func, text
from sqlalchemy.orm import declarative_base, Mapped
from sqlalchemy.types import Uuid
import uuid

class BaseModel:
    pass

Base = declarative_base(cls=BaseModel)
