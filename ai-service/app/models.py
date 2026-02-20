from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from .database import Base

class PracticeSession(Base):
    """Store user practice sessions for history/analytics"""
    __tablename__ = "practice_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    language = Column(String, nullable=False)
    expected_sentence = Column(Text, nullable=False)
    english_translation = Column(Text, nullable=False)
    transcription = Column(Text)
    accuracy_score = Column(Float)
    is_correct = Column(String)  # "correct" or "incorrect"
    audio_file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
