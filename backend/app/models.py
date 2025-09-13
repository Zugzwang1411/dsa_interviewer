from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class PerformanceEntry(Base):
    __tablename__ = 'performance_entries'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(36), nullable=False)
    question_id = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    score = Column(Integer, nullable=False)
    normalized_score = Column(Float, nullable=False)
    concepts_covered = Column(Text)
    missing_concepts = Column(Text)
    quality = Column(String(20))
    depth = Column(String(20))
    detailed_analysis = Column(Text)
    feedback = Column(Text)
    is_followup = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

def get_database_url():
    return os.getenv('DATABASE_URL', 'sqlite:///dsa_interviewer.db')

def create_database_engine():
    try:
        engine = create_engine(get_database_url())
        Base.metadata.create_all(engine)
        return engine
    except Exception as e:
        print(f"Database initialization failed: {e}")
        return None

def get_session_maker():
    engine = create_database_engine()
    if engine:
        return sessionmaker(bind=engine)
    return None
