"""
Simplified Organization and Store models.
NOTE: These tables do not exist in the current database schema.
"""

from sqlalchemy import Column, Integer, String, Boolean
from .base import Base

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))

class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
