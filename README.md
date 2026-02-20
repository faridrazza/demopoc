# AI Language Coach - Microservices POC

A microservices based language learning platform with AI-powered speech recognition and pronunciation feedback.

## 🏗️ Architecture

This project demonstrates a **true microservices architecture** with:

- **3 Independent Services** (Auth, User, AI)
- **Database per Service** (PostgreSQL)
- **Service-to-Service Communication** (REST APIs)
- **JWT Authentication**
- **OpenAI Integration** (GPT-3.5 + Whisper)
- **Audio File Storage** (Filesystem with Docker volumes)
- **Docker Containerization**

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend)
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

### 4. Start Frontend

```bash
cd frontend/ai-language-coach
npm install
npm run dev
```

Frontend runs on: http://localhost:8080

### 5. Access the Application

Open http://localhost:8080 in your browser.

## 📦 Project Structure

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

## 🔧 Services

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

**Endpoints:**
- `POST /ai/generate-sentence` - Generate practice sentence
- `POST /ai/submit-audio` - Upload audio file for transcription and analysis
- `POST /ai/chat` - Chat with AI
- `GET /ai/history` - Get practice history

## 🐳 Docker Commands

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


## 🚢 Deployment

### Local Development
```bash
docker-compose up -d
```

### Production Deployment Options

#### Option 1: Render (Recommended - Easiest)
- ✅ Free tier available
- ✅ Deploy directly from GitHub
- ✅ Automatic HTTPS
- ✅ Free PostgreSQL (90 days)

**Quick Deploy:**
1. Push code to GitHub
2. Connect repo to Render
3. Deploy 3 services + 3 databases
4. Add environment variables

#### Option 2: Google Cloud Run
- ✅ Free tier available
- ✅ Serverless, auto-scaling
- ✅ Pay per use
- Use Cloud SQL for databases

**Deploy Command:**
```bash
gcloud run deploy SERVICE_NAME --source . --region us-central1
```

#### Option 3: Railway
- ✅ Free tier available
- ✅ Easy deployment
- ✅ Free PostgreSQL

### Production Best Practices
- Use managed PostgreSQL (Cloud SQL, Supabase, Railway)
- Enable HTTPS/TLS (automatic on most platforms)
- Set up monitoring and logging
- Use environment variables for secrets
- Configure auto-scaling
- Regular backups

