# Mobile App Integration Testing

This document describes the comprehensive integration tests for the BiteSight mobile app and backend API.

## Overview

Task 12 from the implementation plan involves testing the complete mobile app integration with the backend. This includes:

- **Task 12.1**: Authentication flow (registration, login, token validation)
- **Task 12.2**: Meal upload and analysis flow
- **Task 12.3**: Feedback retrieval
- **Task 12.4**: Meal history with pagination
- **Task 12.5**: Weekly insights
- **Task 12.6**: Offline/online sync (mobile app side)
- **Task 12.7**: Error handling

## Test Files Created

### 1. Unit Tests (`tests/test_mobile_app_integration.py`)

Comprehensive pytest-based integration tests that test all API endpoints from the mobile app perspective.

**Note**: These tests currently have issues with SQLite UUID compatibility in the test environment. The tests are designed to work with PostgreSQL.

### 2. Manual Integration Test Script (`test_mobile_integration_manual.py`)

A standalone Python script that can be run against a live backend instance to test all mobile app flows.

## Running the Tests

### Option 1: Manual Integration Tests (Recommended)

1. **Start the database and backend**:
   ```bash
   cd BiteSight
   docker-compose up -d postgres redis
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Run the manual integration test script**:
   ```bash
   python test_mobile_integration_manual.py
   ```

This script will:
- Create a test user
- Test registration and login
- Upload a test meal image
- Check analysis status
- Retrieve feedback (if available)
- Get meal history
- Get weekly insights
- Test error handling scenarios

### Option 2: Unit Tests (Requires PostgreSQL Test Database)

To run the pytest-based integration tests, you need a PostgreSQL test database:

```bash
# Set up test database
export DATABASE_URL="postgresql://test_user:test_pass@localhost:5432/test_db"

# Run tests
pytest tests/test_mobile_app_integration.py -v
```

## Test Coverage

### Task 12.1: Authentication Flow ✅

**Tests**:
- User registration from mobile app
- User login from mobile app
- JWT token validation
- Protected endpoint access
- Invalid credentials handling

**Endpoints Tested**:
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

**Expected Behavior**:
- Registration returns user profile without password
- Login returns JWT token with `access_token`, `token_type`, `expires_in`, and `student` object
- Protected endpoints require valid Bearer token
- Invalid credentials return 401 Unauthorized

### Task 12.2: Meal Upload and Analysis Flow ✅

**Tests**:
- Image upload from mobile app
- Meal record creation with 'pending' status
- AI analysis workflow trigger
- Analysis status polling
- DetectedFood records creation
- Response forma