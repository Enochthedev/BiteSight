# Backend Services

FastAPI-based microservices architecture for the nutrition feedback system.

## Services

- **API Gateway**: Main FastAPI application with routing and middleware
- **Image Service**: Handle image upload, preprocessing, and storage
- **Analysis Service**: Food recognition and nutritional analysis
- **Feedback Service**: Generate culturally relevant recommendations
- **User Service**: Authentication and user management
- **History Service**: Meal history and insights generation

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```