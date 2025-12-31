from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from database.db import engine

Base = declarative_base()

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True)
    skills = Column(String)
    experience = Column(Integer)
    score = Column(Integer)
    status = Column(String)

Base.metadata.create_all(engine)
