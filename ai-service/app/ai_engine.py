import openai
import os
from typing import Dict

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_sentence_with_ai(language: str) -> Dict[str, str]:
    """
    Generate a random sentence in the specified language using OpenAI API
    
    Args:
        language: Target language (e.g., "Hindi", "Spanish", "French")
    
    Returns:
        Dict with 'sentence' and 'english_translation'
    """
    try:
        # Create prompt for OpenAI
        prompt = f"""Generate a simple, everyday sentence in {language} that a language learner could practice speaking.
The sentence should be:
- Natural and commonly used
- Not too long (5-15 words)
- Appropriate for beginners to intermediate learners

Provide the response in this exact format:
Sentence: [sentence in {language}]
Translation: [English translation]"""

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a language learning assistant that generates practice sentences."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,  # Add some randomness for variety
            max_tokens=150
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse the response
        lines = content.split('\n')
        sentence = ""
        translation = ""
        
        for line in lines:
            if line.startswith("Sentence:"):
                sentence = line.replace("Sentence:", "").strip()
            elif line.startswith("Translation:"):
                translation = line.replace("Translation:", "").strip()
        
        if not sentence or not translation:
            raise ValueError("Failed to parse AI response")
        
        return {
            "sentence": sentence,
            "english_translation": translation
        }
    
    except Exception as e:
        # Fallback to predefined sentences if OpenAI fails
        print(f"OpenAI API error: {str(e)}")
        return get_fallback_sentence(language)


def get_fallback_sentence(language: str) -> Dict[str, str]:
    """
    Fallback sentences if OpenAI API is not available or fails
    """
    fallback_sentences = {
        "Hindi": {
            "sentence": "मैं आज बाजार जा रहा हूं",
            "english_translation": "I am going to the market today"
        },
        "Spanish": {
            "sentence": "Me gusta mucho la música",
            "english_translation": "I really like music"
        },
        "French": {
            "sentence": "Je voudrais un café s'il vous plaît",
            "english_translation": "I would like a coffee please"
        },
        "German": {
            "sentence": "Ich lerne Deutsch seit einem Jahr",
            "english_translation": "I have been learning German for a year"
        },
        "Italian": {
            "sentence": "Dove si trova la stazione?",
            "english_translation": "Where is the station?"
        },
        "Japanese": {
            "sentence": "今日はいい天気ですね",
            "english_translation": "The weather is nice today, isn't it?"
        },
        "Chinese": {
            "sentence": "我喜欢学习新的语言",
            "english_translation": "I like learning new languages"
        },
        "Portuguese": {
            "sentence": "Eu gosto de viajar pelo mundo",
            "english_translation": "I like to travel around the world"
        }
    }
    
    return fallback_sentences.get(
        language,
        {
            "sentence": "Hello, how are you?",
            "english_translation": "Hello, how are you?"
        }
    )


def chat_with_openai(message: str) -> str:
    """
    Chat with OpenAI for language learning assistance
    
    Args:
        message: User's message
    
    Returns:
        AI's response
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a friendly language learning assistant. Help users practice languages, answer questions about grammar, vocabulary, and provide encouragement."},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"OpenAI chat error: {str(e)}")
        # Fallback response
        return f"I received your message! I'm here to help you with language learning. You can ask me to generate sentences in different languages or practice speaking."
