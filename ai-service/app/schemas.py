from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class GenerateSentenceRequest(BaseModel):
    language: str  # e.g., "Hindi", "Spanish", "French"

class GenerateSentenceResponse(BaseModel):
    sentence: str
    english_translation: str
    language: str

class ChatRequest(BaseModel):
    message: str

class SubmitAudioResponse(BaseModel):
    transcription: str
    accuracy_score: float
    is_correct: str  # "correct" or "incorrect"
    expected_sentence: str
    english_translation: str
    feedback: Optional[str] = None

class PracticeSessionResponse(BaseModel):
    id: int
    user_id: int
    language: str
    expected_sentence: str
    english_translation: str
    transcription: Optional[str]
    accuracy_score: Optional[float]
    is_correct: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
