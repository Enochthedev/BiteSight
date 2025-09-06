# AI-Powered Visual Nutrition Feedback System

An intelligent mobile application designed to help Nigerian students develop healthier eating habits through instant, culturally relevant nutritional feedback using computer vision and AI.

## Project Structure

```
nutrition-feedback-system/
├── backend/                 # FastAPI backend service
│   ├── app/                # Application code
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Core configuration
│   │   ├── models/        # Database models
│   │   └── services/      # Business logic services
│   ├── alembic/           # Database migrations
│   ├── database/          # Database initialization
│   ├── Dockerfile         # Backend container config
│   └── requirements.txt   # Python dependencies
├── mobile/                 # React Native mobile app
│   ├── src/               # Source code
│   │   ├── components/    # Reusable UI components
│   │   ├── screens/       # Screen components
│   │   ├── services/      # API and utility services
│   │   ├── types/         # TypeScript type definitions
│   │   ├── utils/         # Utility functions
│   │   └── context/       # React context providers
│   ├── package.json       # Node.js dependencies
│   └── tsconfig.json      # TypeScript configuration
├── shared/                 # Shared utilities and types
│   └── types/             # Common TypeScript interfaces
├── nginx/                  # Nginx configuration
├── docker-compose.yml      # Multi-service container setup
└── .env.example           # Environment variables template
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 16+ (for mobile development)
- Python 3.11+ (for local backend development)

### Development Setup

1. **Clone and setup environment:**
   ```bash
   cd nutrition-feedback-system
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start services with Docker:**
   ```bash
   docker-compose up -d
   ```

3. **Setup mobile development:**
   ```bash
   cd mobile
   npm install
   ```

4. **Run mobile app:**
   ```bash
   # For Android
   npm run android
   
   # For iOS (macOS only)
   npm run ios
   ```

### Services

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Features

- 📸 **Image Capture**: Camera integration for meal photography
- 🤖 **AI Recognition**: Nigerian food identification using computer vision
- 📊 **Nutrition Analysis**: Rule-based nutritional feedback system
- 📱 **Mobile-First**: React Native app optimized for Android
- 🏥 **Cultural Relevance**: Feedback tailored to Nigerian cuisine
- 📈 **Progress Tracking**: Weekly insights and meal history
- 🔒 **Privacy-Focused**: Consent-based data storage with encryption

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Primary database
- **Redis**: Caching and session management
- **PyTorch**: AI model inference
- **SQLAlchemy**: Database ORM
- **Alembic**: Database migrations

### Mobile
- **React Native**: Cross-platform mobile development
- **TypeScript**: Type-safe JavaScript
- **React Navigation**: Navigation system
- **AsyncStorage**: Local data persistence
- **Axios**: HTTP client

### Infrastructure
- **Docker**: Containerization
- **Nginx**: Reverse proxy and static file serving

## Development Workflow

This project follows a spec-driven development approach. See `.kiro/specs/nutrition-feedback-system/` for:
- `requirements.md`: Feature requirements in EARS format
- `design.md`: Technical design and architecture
- `tasks.md`: Implementation task breakdown

## Contributing

1. Review the requirements and design documents
2. Follow the task-based implementation approach
3. Ensure all code follows the established patterns
4. Test thoroughly before submitting changes

## License

This project is developed for educational and research purposes.