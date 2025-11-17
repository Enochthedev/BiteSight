# BiteSight Backend API

FastAPI-based backend for Nigerian food nutrition analysis with AI-powered food recognition.

## 🏗️ Architecture

### Core Services
- **API Gateway**: Main FastAPI application (`app/main.py`)
- **AI Service**: MobileNetV2 food recognition (`app/services/ai_service.py`)
- **Image Service**: Upload, preprocessing, storage (`app/services/image_service.py`)
- **Feedback Service**: Nutritional recommendations (`app/services/feedback_service.py`)
- **User Service**: Authentication & user management (`app/services/user_service.py`)
- **History Service**: Meal history & insights (`app/services/history_service.py`)

### Database Architecture
- **PostgreSQL**: Primary database (port 5433)
- **Redis**: Caching & session management (port 6379)
- **SQLAlchemy ORM**: Database models and migrations
- **Alembic**: Database migration management

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 15
- Redis 7
- Docker & Docker Compose (recommended)

### 1. Start Database Services

```bash
# Start PostgreSQL and Redis using Docker
docker-compose up postgres redis -d

# Verify services are running
docker ps | grep nutrition
```

**Database Connection:**
- **Host**: 127.0.0.1
- **Port**: 5433 (mapped to avoid conflicts with local PostgreSQL)
- **Database**: nutrition_feedback
- **User**: nutrition_user
- **Password**: nutrition_pass

**Redis Connection:**
- **Host**: localhost
- **Port**: 6379

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

The backend uses `app/core/config.py` for configuration. Key settings:

```python
# Database
DATABASE_URL = "postgresql://nutrition_user:nutrition_pass@127.0.0.1:5433/nutrition_feedback"

# Redis
REDIS_URL = "redis://localhost:6379"

# AI Model
MODEL_PATH = "models/best_model.pth"
FOOD_MAPPING_PATH = "dataset/metadata/nigerian_foods.json"
```

**Optional**: Create `.env` file to override defaults:
```bash
DATABASE_URL=postgresql://nutrition_user:nutrition_pass@127.0.0.1:5433/nutrition_feedback
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### 4. Run Database Migrations

```bash
# Run migrations to create tables
python -m alembic upgrade head

# Verify tables were created
docker exec nutrition-postgres psql -U nutrition_user -d nutrition_feedback -c "\dt"
```

**Database Schema:**
- `students` - User accounts
- `meals` - Meal records with images
- `detected_foods` - AI-detected food items
- `feedback_records` - Nutritional feedback
- `weekly_insights` - Weekly nutrition analysis
- `nigerian_foods` - Food database
- `nutrition_rules` - Feedback rules
- `image_metadata` - Image processing metadata
- `consent_records` - Privacy consent tracking
- `admin_users` - Admin accounts

### 5. Start Backend Server

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Server will start on:** http://localhost:8000

### 6. Verify Installation

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "ai": "healthy",
    "api": "healthy"
  }
}
```

---

## 📊 Database Connection Details

### Connection Flow

```
FastAPI App (app/main.py)
    ↓
Database Config (app/core/database.py)
    ↓
SQLAlchemy Engine
    ↓
PostgreSQL (127.0.0.1:5433)
```

### Database Configuration (`app/core/database.py`)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # Verify connections before using
    pool_recycle=300,        # Recycle connections every 5 minutes
    echo=False               # Set True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency injection for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Using Database in Endpoints

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

@router.get("/example")
async def example_endpoint(db: Session = Depends(get_db)):
    # Database session is automatically managed
    result = db.query(Model).all()
    return result
```

### Database Models Location

All models are in `app/models/`:
- `base.py` - Base model with UUID and timestamps
- `user.py` - Student/User models
- `meal.py` - Meal and DetectedFood models
- `feedback.py` - FeedbackRecord and NutritionRule models
- `history.py` - WeeklyInsight model
- `image_metadata.py` - ImageMetadata model

---

## 🤖 AI Model Setup

### Model Files
- **Model**: `models/best_model.pth` (11.43 MB)
- **Food Mapping**: `dataset/metadata/nigerian_foods.json` (104 foods)
- **Class Names**: `dataset/metadata/class_names.txt`

### AI Service Initialization

The AI service is initialized on app startup in `app/main.py`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from app.services.ai_service import initialize_ai_service
    initialize_ai_service()  # Loads model and food mapper
    
    yield
    
    # Shutdown
    from app.services.ai_service import cleanup_ai_service
    cleanup_ai_service()
```

### AI Integration Flow

```
Image Upload (POST /meals/upload)
    ↓
Save Image (image_service.py)
    ↓
AI Analysis (ai_service.py)
    ↓
Model Inference (model_server.py)
    ↓
MobileNetV2 Model (best_model.pth)
    ↓
Food Detection Results
    ↓
Nutritional Analysis
    ↓
Response to Client
```

---

## 🔌 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login (returns JWT token)
- `GET /api/v1/auth/me` - Get current user profile
- `PUT /api/v1/auth/me` - Update profile
- `DELETE /api/v1/auth/me` - Delete account

### Meals
- `POST /api/v1/meals/upload` - Upload meal image (includes AI analysis)
- `GET /api/v1/meals/{meal_id}/analysis` - Get meal analysis
- `GET /api/v1/meals/{meal_id}/feedback` - Get nutritional feedback
- `GET /api/v1/meals/history` - Get meal history (paginated)
- `GET /api/v1/meals/{meal_id}/image` - Get meal image
- `DELETE /api/v1/meals/{meal_id}` - Delete meal

### Insights
- `GET /api/v1/insights/weekly` - Get weekly nutrition insights

### Health
- `GET /health` - System health check (includes AI status)

### Documentation
- `GET /api/v1/docs` - Interactive API documentation (Swagger UI)
- `GET /api/v1/redoc` - Alternative API documentation (ReDoc)

---

## 🧪 Testing

### Run Integration Tests

```bash
# Complete mobile app integration test
python test_mobile_integration_manual.py

# Unit tests
pytest tests/ -v

# Specific test file
pytest tests/test_auth.py -v

# With coverage
pytest --cov=app tests/
```

### Manual API Testing

```bash
# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test User","password":"Test123!"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'

# Upload meal (replace TOKEN)
curl -X POST http://localhost:8000/api/v1/meals/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@meal_image.jpg"

# Get meal history
curl http://localhost:8000/api/v1/meals/history \
  -H "Authorization: Bearer TOKEN"
```

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/      # API route handlers
│   │       │   ├── auth.py
│   │       │   ├── meals.py
│   │       │   └── insights.py
│   │       └── router.py       # Main API router
│   ├── core/
│   │   ├── config.py          # Configuration settings
│   │   ├── database.py        # Database connection ⭐
│   │   ├── auth.py            # JWT authentication
│   │   ├── redis_client.py    # Redis connection
│   │   └── middleware.py      # Request/response middleware
│   ├── models/
│   │   ├── base.py            # Base model with UUID
│   │   ├── user.py            # User/Student models
│   │   ├── meal.py            # Meal models
│   │   ├── feedback.py        # Feedback models
│   │   └── history.py         # History models
│   ├── services/
│   │   ├── ai_service.py      # AI integration ⭐
│   │   ├── user_service.py    # User management
│   │   ├── image_service.py   # Image processing
│   │   ├── feedback_service.py
│   │   └── history_service.py
│   ├── ml/                    # Machine learning
│   │   ├── models/            # Model architectures
│   │   ├── inference/         # Inference engine
│   │   ├── serving/           # Model serving
│   │   └── dataset/           # Data utilities
│   └── main.py               # FastAPI app entry point ⭐
├── alembic/
│   ├── versions/             # Database migrations
│   └── env.py               # Alembic configuration
├── dataset/
│   ├── metadata/
│   │   ├── nigerian_foods.json  # Food database ⭐
│   │   └── class_names.txt
│   └── images/              # Training images (empty)
├── models/
│   └── best_model.pth       # Pre-trained model ⭐
├── tests/                   # Test files
├── uploads/                 # Uploaded images
├── docker-compose.yml       # Docker services ⭐
├── alembic.ini             # Alembic config
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file in backend directory:

```bash
# Database
DATABASE_URL=postgresql://nutrition_user:nutrition_pass@127.0.0.1:5433/nutrition_feedback

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=11520  # 8 days

# AI Model
MODEL_PATH=models/best_model.pth
FOOD_MAPPING_PATH=dataset/metadata/nigerian_foods.json
INFERENCE_DEVICE=auto  # auto, cpu, or cuda
CONFIDENCE_THRESHOLD=0.1

# File Upload
MAX_UPLOAD_SIZE=10485760  # 10MB
UPLOAD_DIR=uploads

# Environment
DEBUG=True
ENVIRONMENT=development
```

### Docker Compose Configuration

The `docker-compose.yml` defines all services:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    ports:
      - "5433:5432"  # External:Internal
    environment:
      POSTGRES_DB: nutrition_feedback
      POSTGRES_USER: nutrition_user
      POSTGRES_PASSWORD: nutrition_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
```

---

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check connection
docker exec nutrition-postgres psql -U nutrition_user -d nutrition_feedback -c "SELECT 1"

# View logs
docker logs nutrition-postgres

# Restart database
docker-compose restart postgres
```

### Redis Connection Issues

```bash
# Check if Redis is running
docker ps | grep redis

# Test connection
docker exec nutrition-redis redis-cli ping

# View logs
docker logs nutrition-redis
```

### AI Service Issues

```bash
# Check if model file exists
ls -lh models/best_model.pth

# Check food mapping
cat dataset/metadata/nigerian_foods.json | python -m json.tool | head

# Check AI status
curl http://localhost:8000/health | grep ai

# View AI logs
tail -f logs/app.log | grep ai_service
```

### Migration Issues

```bash
# Check current migration version
python -m alembic current

# View migration history
python -m alembic history

# Rollback one migration
python -m alembic downgrade -1

# Reset and reapply all migrations
python -m alembic downgrade base
python -m alembic upgrade head
```

---

## 📚 Additional Documentation

- **AI Setup**: See `AI_SETUP_SUMMARY.md`
- **Training Guide**: See `TRAINING_GUIDE.md`
- **Dataset Guide**: See `dataset/README.md`
- **Integration Status**: See `AI_INTEGRATION_COMPLETE.md`
- **Mobile Testing**: See `MOBILE_INTEGRATION_TESTING.md`

---

## 🚀 Deployment

### Production Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Set `DEBUG=False`
- [ ] Use strong database password
- [ ] Configure CORS origins
- [ ] Set up SSL/TLS
- [ ] Configure proper logging
- [ ] Set up monitoring
- [ ] Configure backup strategy
- [ ] Train real AI model
- [ ] Set up CDN for images

### Production Database

```bash
# Use production PostgreSQL (not Docker)
DATABASE_URL=postgresql://user:password@production-host:5432/nutrition_feedback

# Run migrations
python -m alembic upgrade head

# Create admin user
python scripts/create_super_admin.py
```

---

## 📞 Support

### Logs Location
- Application logs: `logs/app.log`
- Error logs: `logs/error.log`
- Docker logs: `docker logs nutrition-postgres` / `docker logs nutrition-redis`

### Common Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Restart backend
# (auto-reloads if using --reload flag)

# Check database
docker exec -it nutrition-postgres psql -U nutrition_user -d nutrition_feedback

# Check Redis
docker exec -it nutrition-redis redis-cli
```

---

**Backend is ready! All services connected and working.** 🚀