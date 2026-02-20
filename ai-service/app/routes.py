from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import uuid
import os
from . import schemas, models
from .database import get_db
from .auth_utils import verify_token
from .ai_engine import generate_sentence_with_ai
from .speech_engine import analyze_speech

router = APIRouter()

AUDIO_FILES_DIR = "/app/audio_files"

@router.post("/ai/generate-sentence", response_model=schemas.GenerateSentenceResponse)
async def generate_sentence(
    request: schemas.GenerateSentenceRequest,
    token_data: dict = Depends(verify_token)
):
    """
    Generate a random practice sentence in the specified language using AI
    
    Flow:
    1. User selects language (Hindi, Spanish, etc.)
    2. AI generates a sentence in that language
    3. Returns sentence + English translation
    """
    try:
        # Generate sentence using OpenAI
        result = generate_sentence_with_ai(request.language)
        
        return schemas.GenerateSentenceResponse(
            sentence=result["sentence"],
            english_translation=result["english_translation"],
            language=request.language
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate sentence: {str(e)}"
        )


@router.post("/ai/submit-audio", response_model=schemas.SubmitAudioResponse)
async def submit_audio(
    audio_file: UploadFile = File(...),
    expected_sentence: str = Form(...),
    english_translation: str = Form(...),
    language: str = Form(...),
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Accept audio from user, transcribe it, and compare with expected sentence
    
    Flow:
    1. User speaks the sentence
    2. System converts speech to text (Whisper)
    3. Compares with expected sentence
    4. Returns: transcription, accuracy score, correct/incorrect, feedback
    """
    
    # Validate file type
    if not audio_file.content_type or not audio_file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be audio format")
    
    try:
        # Save audio file
        file_extension = audio_file.filename.split(".")[-1] if "." in audio_file.filename else "wav"
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(AUDIO_FILES_DIR, unique_filename)
        
        os.makedirs(AUDIO_FILES_DIR, exist_ok=True)
        
        with open(file_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)
        
        # Analyze speech (transcribe + calculate accuracy)
        analysis_result = analyze_speech(file_path, expected_sentence, language)
        
        # Save practice session to database
        practice_session = models.PracticeSession(
            user_id=token_data["user_id"],
            language=language,
            expected_sentence=expected_sentence,
            english_translation=english_translation,
            transcription=analysis_result["transcription"],
            accuracy_score=analysis_result["accuracy_score"],
            is_correct=analysis_result["is_correct"],
            audio_file_path=file_path
        )
        db.add(practice_session)
        db.commit()
        
        # Return result
        return schemas.SubmitAudioResponse(
            transcription=analysis_result["transcription"],
            accuracy_score=analysis_result["accuracy_score"],
            is_correct=analysis_result["is_correct"],
            expected_sentence=expected_sentence,
            english_translation=english_translation,
            feedback=analysis_result["feedback"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process audio: {str(e)}"
        )


@router.get("/ai/history", response_model=List[schemas.PracticeSessionResponse])
async def get_practice_history(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Get user's practice history
    """
    sessions = db.query(models.PracticeSession).filter(
        models.PracticeSession.user_id == token_data["user_id"]
    ).order_by(models.PracticeSession.created_at.desc()).limit(50).all()
    
    return sessions


@router.get("/ai/stats")
async def get_user_stats(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Get user's practice statistics
    """
    from sqlalchemy import func
    
    user_id = token_data["user_id"]
    
    # Total practices
    total_practices = db.query(func.count(models.PracticeSession.id)).filter(
        models.PracticeSession.user_id == user_id
    ).scalar()
    
    # Average accuracy
    avg_accuracy = db.query(func.avg(models.PracticeSession.accuracy_score)).filter(
        models.PracticeSession.user_id == user_id
    ).scalar()
    
    # Correct count
    correct_count = db.query(func.count(models.PracticeSession.id)).filter(
        models.PracticeSession.user_id == user_id,
        models.PracticeSession.is_correct == "correct"
    ).scalar()
    
    # Languages practiced
    languages = db.query(models.PracticeSession.language).filter(
        models.PracticeSession.user_id == user_id
    ).distinct().all()
    
    return {
        "total_practices": total_practices or 0,
        "average_accuracy": round(float(avg_accuracy or 0), 2),
        "correct_count": correct_count or 0,
        "languages_practiced": [lang[0] for lang in languages]
    }


@router.post("/ai/chat")
async def chat_with_ai(
    request: schemas.ChatRequest,
    token_data: dict = Depends(verify_token)
):
    """
    Chat with AI assistant for language learning
    """
    try:
        from .ai_engine import chat_with_openai
        
        response = chat_with_openai(request.message)
        
        return {
            "response": response,
            "message": response  # For compatibility
        }
    
    except Exception as e:
        # Fallback response if OpenAI fails
        return {
            "response": f"I received your message: '{request.message}'. I'm here to help you practice languages! Try asking me to generate a sentence in a specific language.",
            "message": f"I received your message: '{request.message}'. I'm here to help you practice languages!"
        }
