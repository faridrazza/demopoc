# Microservices POC

A microservices based language learning platform with AI powered speech recognition and pronunciation feedback.

## Architecture

This project demonstrates a **true microservices architecture** with:

- **3 Independent Services** (Auth, User, AI)
- **Database per Service** (PostgreSQL)
- **Service-to-Service Communication** (REST APIs)
- **JWT Authentication**
- **OpenAI Integration** (GPT-3.5 + Whisper)
- **Audio File Storage** (Filesystem with Docker volumes)
- **Docker Containerization**

### Mono-Repo vs Poly Repo

**Current Setup: Mono-Repo (Single Repository)**

For this simple POC, all services are organized in a single repository to simplify setup, development, and demonstration. However, each service is completely isolated:

- **Independent Deployment**: Each service has its own Dockerfile and can be deployed separately
- **Isolated Databases**: Each service owns its database (no shared data)
- **Independent Scaling**: Scale auth-service to 10 instances while user-service runs 2 instances
- **No Shared Code**: Services communicate only via REST APIs
- **Separate Ports**: Each service runs on its own port (8000, 8001, 8002)
- **Fault Isolation**: If AI service crashes, auth and user services continue running

**Production Recommendation: Poly-Repo (Multiple Repositories)**

For larger production-grade applications, each microservice should have its own repository:

- **Independent CI/CD**: Each service has its own build pipeline and deployment schedule
- **Team Ownership**: Different teams can own different services without conflicts
- **Version Control**: Services can have independent versioning (auth-service v2.0, user-service v1.5)
- **Security**: Restrict access per service (frontend team can't access payment service code)
- **Faster Builds**: Only rebuild the service that changed, not the entire monorepo

**Why Mono Repo for This POC:**
- Easier to clone and run (`git clone` once, `docker-compose up` and done)
- Simpler for demos and presentations
- Faster local development and testing
- All documentation in one place

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API Key

### 1. Clone and Setup

```bash
git clone <repository-url>
cd demoPoc
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Start Backend Services

```bash
docker-compose up -d
```

This starts:
- Auth Service (Port 8001)
- User Service (Port 8000)
- AI Service (Port 8002)
- 3 PostgreSQL databases

### 4. Test the Services

**Health checks:**
```bash
curl http://localhost:8001/health
curl http://localhost:8000/health
curl http://localhost:8002/health
```

**API Documentation:**
- Auth Service: http://localhost:8001/docs
- User Service: http://localhost:8000/docs
- AI Service: http://localhost:8002/docs

## Project Structure

```
demoPoc/
├── auth-service/          # Authentication & JWT
│   ├── app/
│   ├── alembic/
│   ├── Dockerfile
│   └── requirements.txt
├── user-service/          # User management
│   ├── app/
│   ├── alembic/
│   ├── Dockerfile
│   └── requirements.txt
├── ai-service/            # AI language learning
│   ├── app/
│   ├── alembic/
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml     # Local development
├── .env.example           # Environment template
└── README.md
```

## Services

### Auth Service (Port 8001)
- User authentication
- JWT token generation & verification
- Password hashing with bcrypt

**Endpoints:**
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT
- `GET /auth/verify` - Verify JWT token
- `GET /auth/me` - Get current user info

### User Service (Port 8000)
- User profile management
- User data storage

**Endpoints:**
- `GET /users/profile` - Get user profile
- `PUT /users/profile` - Update profile
- `GET /users/by-email/{email}` - Get user by email (internal)

### AI Service (Port 8002)
- Sentence generation (OpenAI GPT-3.5)
- Speech-to-text transcription (OpenAI Whisper)
- Pronunciation accuracy scoring
- AI avatar video conversations (Tavus AI + Daily.co)

**Endpoints:**
- `POST /ai/generate-sentence` - Generate practice sentence
- `POST /ai/submit-audio` - Upload audio file for transcription and analysis
- `POST /ai/chat` - Chat with AI
- `POST /ai/create-avatar-conversation` - Create real-time video conversation with AI avatar
- `GET /ai/history` - Get practice history

## Docker Commands

**Start all services:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f
```

**Check status:**
```bash
docker-compose ps
```

**Stop services:**
```bash
docker-compose down
```

**Rebuild after code changes:**
```bash
docker-compose up --build -d
```

**Clean restart (removes volumes):**
```bash
docker-compose down -v
docker-compose up -d
```

## Features

### 1. Speaking Practice
- Generate sentences in 8+ languages
- Record your pronunciation
- Get AI-powered accuracy feedback
- Track practice history

### 2. AI Chat
- Text-based conversation with AI tutor
- Get language learning tips
- Ask questions about grammar and vocabulary

### 3. Talk to Luna (AI Avatar)
- Real-time video conversation with Luna, your AI English tutor
- Full-screen face-to-face practice
- AI can see and hear you in real-time
- Natural conversation with instant feedback
- Powered by Tavus AI + Daily.co WebRTC streaming

**Setup:**
1. Sign up at [https://tavus.io](https://tavus.io)
2. Create a persona in Tavus Dashboard (or use existing)
3. Get your API key, Persona ID, and Replica ID
4. Add to `.env`:
   ```
   TAVUS_API_KEY=your_api_key
   TAVUS_PERSONA_ID=your_persona_id
   TAVUS_REPLICA_ID=your_replica_id
   ```
5. Rebuild: `docker-compose up --build -d`

**Usage:**
- Click "Talk to Luna" tab in Dashboard
- Click "Start Video Call with Luna"
- Allow camera/microphone permissions
- Start practicing English!

**Note:** Feature is optional. Other features work without Tavus configuration.

## API Keys Required

### OpenAI (Required for core features)
- Sentence generation (GPT-3.5)
- Speech transcription (Whisper)
- Accuracy evaluation
- Get from: https://platform.openai.com/api-keys

### Tavus AI (Optional - for Luna avatar feature)
- Real-time video conversations with AI avatar
- WebRTC streaming via Daily.co
- Get from: https://tavus.io (Developer Portal)
- Requires: API Key, Persona ID, Replica ID
- Leave empty if not using avatar feature

## Environment Variables

Create a `.env` file in the root directory:

```bash
# JWT Secret (Required)
JWT_SECRET_KEY=your-secret-key-change-in-production

# OpenAI API Key (Required)
OPENAI_API_KEY=your-openai-api-key

# Tavus AI (Optional - for Luna avatar)
TAVUS_API_KEY=your-tavus-api-key
TAVUS_PERSONA_ID=your-persona-id
TAVUS_REPLICA_ID=your-replica-id
```


## Deployment

### Local Development
```bash
docker-compose up -d
```

