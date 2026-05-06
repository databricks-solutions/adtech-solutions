from sqlalchemy import Column, Integer, String

from .base import Base


class ConfigKV(Base):
    __tablename__ = 'config_kv'

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)


