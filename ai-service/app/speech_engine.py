import openai
import difflib
import os
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcribe_audio(audio_file_path: str, language: str = None) -> str:
    """
    Transcribe audio file using OpenAI Whisper API
    Fast, accurate, and no heavy downloads needed!
    """
    try:
        # Verify API key exists
        if not os.getenv("OPENAI_API_KEY"):
            raise Exception("OPENAI_API_KEY not configured")
        
        # Verify file exists
        if not os.path.exists(audio_file_path):
            raise Exception(f"Audio file not found: {audio_file_path}")
        
        # Open audio file
        with open(audio_file_path, "rb") as audio_file:
            # Call OpenAI Whisper API with language hint
            params = {
                "model": "whisper-1",
                "file": audio_file,
                "response_format": "text"
            }
            
            # Add language hint if provided (helps with accuracy)
            if language:
                language_codes = {
                    "hindi": "hi",
                    "spanish": "es",
                    "french": "fr",
                    "german": "de",
                    "japanese": "ja",
                    "portuguese": "pt",
                    "arabic": "ar",
                    "chinese": "zh"
                }
                lang_code = language_codes.get(language.lower())
                if lang_code:
                    params["language"] = lang_code
            
            transcript = client.audio.transcriptions.create(**params)
        
        # Handle both string and object responses
        if isinstance(transcript, str):
            return transcript.strip()
        else:
            return str(transcript).strip()
    
    except Exception as e:
        print(f"Transcription error: {str(e)}")
        raise Exception(f"Transcription failed: {str(e)}")


def calculate_accuracy_with_ai(transcription: str, expected_sentence: str, language: str) -> dict:
    """
    Use OpenAI GPT to intelligently evaluate pronunciation accuracy
    Considers language context, phonetics, and meaning
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a language pronunciation expert. Evaluate how accurately the user spoke a {language} sentence.
                    
Consider:
1. Phonetic similarity (sounds alike even if spelling differs)
2. Language-specific pronunciation rules
3. Common pronunciation mistakes
4. Meaning preservation

Return a JSON object with:
- accuracy_score: number 0-100
- is_correct: "correct" if score >= 80, else "incorrect"
- feedback: brief encouraging feedback
- phonetic_match: true/false if it sounds similar"""
                },
                {
                    "role": "user",
                    "content": f"""Expected sentence ({language}): {expected_sentence}
User said: {transcription}

Evaluate the pronunciation accuracy."""
                }
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        print(f"AI evaluation error: {str(e)}, falling back to simple matching")
        # Fallback to simple matching
        return calculate_accuracy_simple(transcription, expected_sentence)


def calculate_accuracy_simple(transcription: str, expected_sentence: str) -> dict:
    """
    Simple accuracy calculation using sequence matching
    Fallback when AI evaluation fails
    """
    # Normalize both strings
    transcription_clean = transcription.lower().strip()
    expected_clean = expected_sentence.lower().strip()
    
    # Use SequenceMatcher for similarity ratio
    similarity = difflib.SequenceMatcher(None, transcription_clean, expected_clean).ratio()
    
    # Convert to percentage
    accuracy_percentage = round(similarity * 100, 2)
    
    # Determine if correct (threshold: 80%)
    is_correct = "correct" if accuracy_percentage >= 80 else "incorrect"
    
    # Generate feedback
    if is_correct == "correct":
        feedback = "🎉 Excellent! Your pronunciation is great!"
    elif accuracy_percentage >= 60:
        feedback = "Good effort! Try to pronounce more clearly."
    else:
        feedback = "Keep practicing! Listen to the correct pronunciation and try again."
    
    return {
        "accuracy_score": accuracy_percentage,
        "is_correct": is_correct,
        "feedback": feedback,
        "phonetic_match": False
    }


def analyze_speech(audio_file_path: str, expected_sentence: str, language: str = "english") -> dict:
    """
    Complete speech analysis: transcribe and calculate accuracy
    Uses OpenAI Whisper API for transcription and GPT for intelligent evaluation
    """
    # Transcribe audio using OpenAI Whisper API with language hint
    transcription = transcribe_audio(audio_file_path, language)
    
    # Use AI to evaluate accuracy (considers phonetics and language context)
    ai_result = calculate_accuracy_with_ai(transcription, expected_sentence, language)
    
    return {
        "transcription": transcription,
        "accuracy_score": ai_result.get("accuracy_score", 0),
        "is_correct": ai_result.get("is_correct", "incorrect"),
        "feedback": ai_result.get("feedback", "Keep practicing!"),
        "phonetic_match": ai_result.get("phonetic_match", False)
    }
