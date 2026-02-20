# Architecture Documentation - DEMO POC

## System Overview

This is a **simple, focused microservices POC** that demonstrates:
- Independent service deployment
- Service-to-service communication
- AI-powered prononciation Practice
- Speech recognition and analysis

## Core Principles

### 1. Simplicity First
- Only 3 services (not 5 or 10)
- Each service has clear, single responsibility
- No unnecessary complexity

### 2. Database per Service
- Each service owns its data
- No cross-database queries
- Complete data isolation

### 3. HTTP-based Communication
- Services communicate via REST APIs
- No shared memory or code
- Timeout handling for resilience

## Architecture Diagram

```
                    ┌─────────────────┐
                    │   Web Client    │
                    │        │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│Auth Service  │    │User Service  │    │ AI Service   │
│   :8001      │◄───┤   :8000      │    │   :8002      │
│              │    │              │    │              │
│- Login       │    │- Register    │◄───┤- Generate    │
│- JWT Gen     │    │- Profile     │    │  Sentence    │
│- Verify      │    │              │    │- Analyze     │
│              │    │              │    │  Speech      │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                    │
       ▼                   ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  auth_db     │    │  user_db     │    │   ai_db      │
│ (PostgreSQL) │    │ (PostgreSQL) │    │ (PostgreSQL) │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Service Breakdown

### 1. Auth Service (Port 8001)

**Responsibility**: Authentication & Authorization

**Technology**:
- FastAPI
- SQLAlchemy
- PostgreSQL
- python-jose (JWT)
- bcrypt (password hashing)

**Database**: `auth_db`
- Currently minimal (ready for refresh tokens if needed)

**Endpoints**:
- `POST /login` - User login, returns JWT
- `GET /verify` - Verify JWT token (internal use)

**Dependencies**: None (most independent service)

**Called by**: User Service, AI Service (for token verification)

---

### 2. User Service (Port 8000)

**Responsibility**: User Management

**Technology**:
- FastAPI
- SQLAlchemy
- PostgreSQL
- httpx (for calling Auth Service)

**Database**: `user_db`
```sql
users
  - id (PK)
  - name
  - email (unique)
  - hashed_password
  - created_at
```

**Endpoints**:
- `POST /users` - Register new user
- `GET /users/me` - Get current user profile (requires JWT)

**Dependencies**: Auth Service (for token verification)

**Called by**: Auth Service (during login to fetch user data)

---

### 3. AI Speaking Service (Port 8002)

**Responsibility**: AI-powered language learning

**Technology**:
- FastAPI
- SQLAlchemy
- PostgreSQL
- OpenAI GPT-3.5 (sentence generation)
- OpenAI Whisper (speech-to-text transcription)
- difflib (similarity matching)
- httpx (for calling Auth Service)

**Database**: `ai_db`
```sql
practice_sessions
  - id (PK)
  - user_id (FK)
  - language
  - expected_sentence
  - english_translation
  - transcription
  - accuracy_score
  - is_correct
  - audio_file_path (filesystem path, not binary data)
  - created_at
```

**Audio Storage**:
- Audio files stored on filesystem at `/app/audio_files`
- Database stores only the file path reference
- Persisted via Docker volume `ai-audio-files`

**Endpoints**:
- `POST /ai/generate-sentence` - Generate practice sentence
- `POST /ai/submit-audio` - Upload audio file for transcription and analysis
- `GET /ai/history` - Get practice history
- `GET /ai/stats` - Get practice statistics

**Dependencies**: Auth Service (for token verification)

**Called by**: Client directly

---

## Request Flow Examples

### Flow 1: User Registration & Login

```
1. Client → User Service
   POST /users
   Body: {name, email, password}
   
2. User Service
   - Hashes password
   - Saves to user_db
   - Returns user data

3. Client → Auth Service
   POST /login
   Body: {email, password}
   
4. Auth Service → User Service
   GET /users/by-email/{email}
   
5. User Service
   - Returns user with hashed_password
   
6. Auth Service
   - Verifies password
   - Generates JWT
   - Returns access_token
```

---

### Flow 2: Generate Practice Sentence

```
1. Client → AI Service
   POST /ai/generate-sentence
   Headers: Authorization: Bearer <token>
   Body: {language: "Spanish"}
   
2. AI Service → Auth Service
   GET /verify
   Headers: Authorization: Bearer <token>
   
3. Auth Service
   - Decodes JWT
   - Returns {user_id, email}
   
4. AI Service → OpenAI API
   - Sends prompt for Spanish sentence
   
5. OpenAI API
   - Returns sentence + translation
   
6. AI Service → Client
   Returns: {sentence, english_translation, language}
```

---

### Flow 3: Upload Audio for Analysis

```
1. Client → AI Service
   POST /ai/submit-audio
   Headers: Authorization: Bearer <token>
   Body: audio_file (multipart/form-data), expected_sentence, translation, language
   
2. AI Service → Auth Service
   GET /verify (token verification)
   
3. AI Service
   - Saves uploaded audio file to filesystem (/app/audio_files)
   - Generates unique filename (UUID)
   
4. AI Service → OpenAI Whisper API
   - Sends audio file for transcription
   - Receives text transcription
   
5. AI Service
   - Compares transcription with expected sentence
   - Calculates accuracy score (0-100%)
   - Determines correct/incorrect (threshold: 80%)
   - Generates feedback using GPT
   
6. AI Service → Database
   - Saves practice session metadata
   - Stores file path (not audio binary)
   
7. AI Service → Client
   Returns: {
     transcription,
     accuracy_score,
     is_correct,
     expected_sentence,
     english_translation,
     feedback
   }
```

---

## Data Flow

### User Data
```
User Service (owns) → Auth Service (reads during login)
```

### Practice Data
```
AI Service (owns) → No other service accesses
```

### Authentication Data
```
Auth Service (generates JWT) → All services (verify JWT)
```

---

## Security Architecture

### Authentication Flow

```
1. User Login
   ├─ Client sends email + password
   ├─ Auth Service fetches user from User Service
   ├─ Password verified with bcrypt
   └─ Returns JWT (30 min expiry)

2. Protected Request
   ├─ Client includes: Authorization: Bearer <token>
   ├─ Service calls Auth Service /verify
   ├─ Auth Service decodes JWT
   └─ Returns user_id, email
```

### Security Measures

1. **Password Security**
   - Bcrypt hashing (cost factor 12)
   - Never stored in plain text
   - Never transmitted in responses

2. **Token Security**
   - JWT signed with HS256
   - 30-minute expiration
   - Verified on every protected request

3. **Network Security**
   - Services isolated in Docker network
   - No external access to databases
   - Service-to-service calls internal only

4. **Data Isolation**
   - Each user sees only their own data
   - Database per service
   - No cross-database queries

---

## Scalability Design

### Horizontal Scaling

Each service can scale independently:

```yaml
# Scale AI Service to handle more audio processing
docker-compose up --scale ai-service=3
```

### Stateless Design

All services are stateless:
- No session storage
- JWT contains all needed info
- Can add/remove instances freely

### Database Scaling

Each database can be:
- Replicated for read scaling
- Sharded for write scaling
- Backed up independently

---

## AI/ML Architecture

### Sentence Generation

```
Input: Language (e.g., "Spanish")
  ↓
OpenAI GPT-3.5 API
  ↓
Prompt: "Generate a simple sentence in Spanish..."
  ↓
Response: Sentence + Translation
  ↓
Fallback: Pre-defined sentences if API fails
```

### Speech-to-Text Transcription

```
Input: Uploaded audio file (WAV, MP3, M4A, etc.)
  ↓
Saved to filesystem: /app/audio_files/{uuid}.{ext}
  ↓
Sent to OpenAI Whisper API (whisper-1 model)
  ↓
Transcription: Text output
  ↓
AI-powered accuracy evaluation (GPT-3.5)
  ↓
Accuracy Score: 0-100%
  ↓
Threshold Check: ≥80% = correct
```

---

## Database Schema

### Auth Database
```sql
-- Currently minimal
-- Ready for refresh_tokens table if needed
```

### User Database
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

### AI Database
```sql
CREATE TABLE practice_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    language VARCHAR NOT NULL,
    expected_sentence TEXT NOT NULL,
    english_translation TEXT NOT NULL,
    transcription TEXT,
    accuracy_score FLOAT,
    is_correct VARCHAR,
    audio_file_path VARCHAR,  -- Filesystem path, not binary data
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_practice_sessions_user_id ON practice_sessions(user_id);
```

**Note**: Audio files are stored on the filesystem at `/app/audio_files/`, not in the database. The database only stores the file path reference.

---

## Deployment

### Development
```bash
docker-compose up --build
```


---


## Conclusion

This architecture provides:
-  Simple, focused design
-  Independent service deployment
-  Clear service boundaries
-  Scalable foundation
-  Production-ready patterns
-  AI/ML integration
-  Clean codebase

The POC successfully demonstrates microservices architecture with AI-powered language learning.
