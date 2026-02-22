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


@router.post("/ai/create-avatar-conversation", response_model=schemas.CreateAvatarConversationResponse)
async def create_avatar_conversation(
    request: schemas.CreateAvatarConversationRequest,
    token_data: dict = Depends(verify_token)
):
    """
    Create a Tavus AI avatar conversation for real-time video language practice
    
    Flow:
    1. User selects language and clicks "Talk to Avatar"
    2. Backend creates Tavus conversation using pre-configured persona
    3. Returns conversation URL (Daily.co room)
    4. Frontend embeds the video call
    5. User talks face-to-face with AI avatar (Luna) in real-time
    
    Technical Details:
    - Uses Tavus API to create conversations
    - Returns Daily.co WebRTC room URL (format: https://tavus.daily.co/xxxxx)
    - Daily.co handles the actual video streaming infrastructure
    - Tavus provides the AI avatar rendering and conversational intelligence
    
    Requirements:
    - TAVUS_API_KEY in environment variables
    - TAVUS_PERSONA_ID in environment variables (created in Tavus dashboard)
    - TAVUS_REPLICA_ID in environment variables (Luna avatar)
    """
    import requests
    
    tavus_api_key = os.getenv("TAVUS_API_KEY")
    tavus_persona_id = os.getenv("TAVUS_PERSONA_ID")
    tavus_replica_id = os.getenv("TAVUS_REPLICA_ID")
    
    # Validate configuration
    if not tavus_api_key:
        raise HTTPException(
            status_code=503,
            detail="Tavus AI is not configured. Please add TAVUS_API_KEY to environment variables."
        )
    
    if not tavus_persona_id:
        raise HTTPException(
            status_code=503,
            detail="Tavus Persona is not configured. Please add TAVUS_PERSONA_ID to environment variables."
        )
    
    if not tavus_replica_id:
        raise HTTPException(
            status_code=503,
            detail="Tavus Replica is not configured. Please add TAVUS_REPLICA_ID to environment variables."
        )
    
    try:
        headers = {
            "x-api-key": tavus_api_key,
            "Content-Type": "application/json"
        }
        
        # Create conversation with pre-configured persona
        conversation_url = "https://tavusapi.com/v2/conversations"
        conversation_payload = {
            "persona_id": tavus_persona_id,
            "replica_id": tavus_replica_id,
            "conversation_name": f"English Practice with Luna - {token_data.get('email', 'User')}",
            "conversational_context": f"The learner wants to practice English conversation. They selected '{request.language}' as their focus area. Adapt your teaching to their level and interests.",
            "properties": {
                "max_call_duration": 1800,  # 30 minutes
                "participant_left_timeout": 60,  # 1 minute after participant leaves
                "enable_recording": False  # Privacy: don't record by default
            }
        }
        
        conversation_response = requests.post(
            conversation_url, 
            json=conversation_payload, 
            headers=headers, 
            timeout=15
        )
        
        # Handle response
        if conversation_response.status_code in [200, 201]:
            data = conversation_response.json()
            
            return schemas.CreateAvatarConversationResponse(
                conversation_id=data.get("conversation_id", ""),
                conversation_url=data.get("conversation_url", ""),
                status=data.get("status", "active"),
                message=f"Connected to Luna! Video streaming powered by Daily.co. Practice {request.language} now!"
            )
        else:
            # Tavus API error
            error_detail = conversation_response.json() if conversation_response.content else {"error": "Unknown error"}
            raise HTTPException(
                status_code=conversation_response.status_code,
                detail=f"Tavus API error: {error_detail}"
            )
    
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Tavus API request timed out. Please try again."
        )
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to Tavus API: {str(e)}"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create avatar conversation: {str(e)}"
        )


@router.post("/ai/end-avatar-conversation")
async def end_avatar_conversation(
    request: schemas.EndAvatarConversationRequest,
    token_data: dict = Depends(verify_token)
):
    """
    End an active Tavus AI avatar conversation
    
    This endpoint properly closes the Daily.co room and ends the conversation.
    Important for:
    - Preventing unnecessary costs
    - Cleaning up resources
    - Proper session management
    
    Call this when:
    - User clicks "End Call" button
    - User navigates away from video page
    - Session timeout occurs
    """
    import requests
    
    tavus_api_key = os.getenv("TAVUS_API_KEY")
    
    if not tavus_api_key:
        raise HTTPException(
            status_code=503,
            detail="Tavus AI is not configured."
        )
    
    try:
        headers = {
            "x-api-key": tavus_api_key
        }
        
        end_url = f"https://tavusapi.com/v2/conversations/{request.conversation_id}/end"
        
        response = requests.post(end_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Conversation ended successfully",
                "conversation_id": request.conversation_id
            }
        else:
            error_detail = response.json() if response.content else {"error": "Unknown error"}
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to end conversation: {error_detail}"
            )
    
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Request timed out"
        )
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to Tavus API: {str(e)}"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to end conversation: {str(e)}"
        )
