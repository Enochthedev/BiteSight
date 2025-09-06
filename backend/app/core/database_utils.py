"""Database utility functions for setup and management."""

import logging
from typing import Generator

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.models.base import Base

logger = logging.getLogger(__name__)


def create_database_tables() -> bool:
    """
    Create all database tables using SQLAlchemy metadata.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {e}")
        return False


def drop_database_tables() -> bool:
    """
    Drop all database tables using SQLAlchemy metadata.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error dropping database tables: {e}")
        return False


def check_database_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        return False


def get_database_session() -> Generator[Session, None, None]:
    """
    Get a database session with proper error handling.

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def initialize_sample_data(db: Session) -> bool:
    """
    Initialize database with sample Nigerian food data and nutrition rules.

    Args:
        db: Database session

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Import models here to avoid circular imports
        from app.models.meal import NigerianFood
        from app.models.feedback import NutritionRule

        # Check if data already exists
        existing_foods = db.query(NigerianFood).first()
        if existing_foods:
            logger.info("Sample data already exists, skipping initialization")
            return True

        # Sample Nigerian foods
        sample_foods = [
            NigerianFood(
                food_name="Jollof Rice",
                local_names={"yoruba": "Jollof",
                             "igbo": "Jollof", "hausa": "Jollof"},
                food_class="carbohydrates",
                nutritional_info={"calories_per_100g": 150,
                                  "carbs": 30, "protein": 3, "fat": 2},
                cultural_context="Popular West African rice dish, often served at celebrations"
            ),
            NigerianFood(
                food_name="Amala",
                local_names={"yoruba": "Àmàlà"},
                food_class="carbohydrates",
                nutritional_info={"calories_per_100g": 120,
                                  "carbs": 25, "protein": 2, "fat": 1},
                cultural_context="Traditional Yoruba dish made from yam flour"
            ),
            NigerianFood(
                food_name="Efo Riro",
                local_names={"yoruba": "Ẹ̀fọ́ rírò"},
                food_class="vitamins",
                nutritional_info={"calories_per_100g": 80,
                                  "carbs": 8, "protein": 4, "fat": 5},
                cultural_context="Nigerian spinach stew rich in vegetables"
            ),
            NigerianFood(
                food_name="Suya",
                local_names={"hausa": "Suya"},
                food_class="proteins",
                nutritional_info={"calories_per_100g": 250,
                                  "carbs": 5, "protein": 25, "fat": 15},
                cultural_context="Spiced grilled meat popular across Nigeria"
            ),
            NigerianFood(
                food_name="Moi Moi",
                local_names={"yoruba": "Mọ́í mọ́í", "igbo": "Moi moi"},
                food_class="proteins",
                nutritional_info={"calories_per_100g": 180,
                                  "carbs": 15, "protein": 12, "fat": 8},
                cultural_context="Steamed bean pudding, protein-rich traditional dish"
            )
        ]

        # Sample nutrition rules
        sample_rules = [
            NutritionRule(
                rule_name="Missing Protein Check",
                condition_logic={"missing_food_groups": ["proteins"]},
                feedback_template="Your meal looks good, but try adding some protein like beans, fish, or meat to make it more balanced. Consider adding moi moi or suya!",
                priority=1,
                is_active=True
            ),
            NutritionRule(
                rule_name="Missing Vegetables Check",
                condition_logic={"missing_food_groups": ["vitamins"]},
                feedback_template="Great choice of foods! To make your meal even healthier, add some vegetables like efo riro or ugwu for vitamins and minerals.",
                priority=1,
                is_active=True
            ),
            NutritionRule(
                rule_name="Balanced Meal Praise",
                condition_logic={"all_food_groups_present": True},
                feedback_template="Excellent! Your meal has a great balance of all food groups. Keep up the healthy eating habits!",
                priority=2,
                is_active=True
            ),
            NutritionRule(
                rule_name="Too Much Carbs Warning",
                condition_logic={"carbohydrate_ratio": ">0.7"},
                feedback_template="You have plenty of energy foods (carbohydrates), but try to balance with more proteins and vegetables for better nutrition.",
                priority=1,
                is_active=True
            )
        ]

        # Add sample data to database
        db.add_all(sample_foods)
        db.add_all(sample_rules)
        db.commit()

        logger.info("Sample data initialized successfully")
        return True

    except SQLAlchemyError as e:
        logger.error(f"Error initializing sample data: {e}")
        db.rollback()
        return False


def reset_database() -> bool:
    """
    Reset database by dropping and recreating all tables.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Resetting database...")

        # Drop all tables
        if not drop_database_tables():
            return False

        # Create all tables
        if not create_database_tables():
            return False

        # Initialize sample data
        with SessionLocal() as db:
            if not initialize_sample_data(db):
                return False

        logger.info("Database reset completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return False
