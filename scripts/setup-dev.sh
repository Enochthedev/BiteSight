#!/bin/bash

# Development environment setup script

set -e

echo "🚀 Setting up Nutrition Feedback System development environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Please review and update the configuration."
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p backend/uploads
mkdir -p backend/models
mkdir -p mobile/android/app/src/main/assets

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d postgres redis

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Install backend dependencies (if running locally)
if command -v python3 &> /dev/null; then
    echo "🐍 Installing Python dependencies..."
    cd backend
    pip install -r requirements.txt
    cd ..
fi

# Install mobile dependencies
if command -v npm &> /dev/null; then
    echo "📱 Installing mobile app dependencies..."
    cd mobile
    npm install
    cd ..
fi

echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Review and update .env file with your configuration"
echo "2. Start the backend: docker-compose up backend"
echo "3. Start the mobile app: cd mobile && npm run android"
echo ""
echo "Services will be available at:"
echo "- Backend API: http://localhost:8000"
echo "- API Documentation: http://localhost:8000/docs"
echo "- PostgreSQL: localhost:5432"
echo "- Redis: localhost:6379"