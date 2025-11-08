"""Test configuration and fixtures."""

import pytest
import uuid
from sqlalchemy import create_engine, TypeDecorator, CHAR
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import Base
from app.core.database import get_db
from app.main import app


# Custom UUID type for SQLite compatibility
class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


# Monkey patch the UUID type for testing
import sqlalchemy.dialects.postgresql as postgresql_dialect
original_uuid = postgresql_dialect.UUID
postgresql_dialect.UUID = GUID

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_student_data():
    """Sample student data for testing."""
    return {
        "email": "test@example.com",
        "name": "Test Student",
        "password": "TestPassword123"
    }


@pytest.fixture
def sample_nigerian_food_data():
    """Sample Nigerian food data for testing."""
    return {
        "food_name": "Test Jollof Rice",
        "local_names": {"yoruba": "Test Jollof"},
        "food_class": "carbohydrates",
        "nutritional_info": {"calories_per_100g": 150},
        "cultural_context": "Test food for unit testing"
    }


@pytest.fixture
def sample_nutrition_rule_data():
    """Sample nutrition rule data for testing."""
    return {
        "rule_name": "Test Rule",
        "condition_logic": {"missing_food_groups": ["proteins"]},
        "feedback_template": "Test feedback message",
        "priority": 1,
        "is_active": True
    }
