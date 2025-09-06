"""Nutrition rule management service."""

from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_db
from app.models.feedback import NutritionRule as NutritionRuleModel
from app.models.feedback import NutritionRuleCreate, NutritionRuleUpdate, NutritionRuleResponse
from app.core.nutrition_engine import NutritionRule, nutrition_engine
import logging

logger = logging.getLogger(__name__)


class NutritionRuleService:
    """Service for managing nutrition rules."""

    def __init__(self):
        self._initialize_default_rules()

    def _initialize_default_rules(self) -> None:
        """Initialize default nutrition rules."""
        default_rules = [
            {
                "rule_id": "missing_protein",
                "name": "Missing Protein Warning",
                "conditions": [
                    {"field": "proteins", "operator": "lt", "value": 0.1}
                ],
                "feedback_template": "Your meal is missing protein! Try adding beans, fish, chicken, or moimoi to make it more balanced.",
                "priority": 5
            },
            {
                "rule_id": "missing_vegetables",
                "name": "Missing Vegetables Warning",
                "conditions": [
                    {"field": "minerals", "operator": "lt", "value": 0.1}
                ],
                "feedback_template": "Add some vegetables like efo riro, ugwu, or okra soup to get important minerals and nutrients.",
                "priority": 4
            },
            {
                "rule_id": "missing_carbs",
                "name": "Missing Carbohydrates Warning",
                "conditions": [
                    {"field": "carbohydrates", "operator": "lt", "value": 0.1}
                ],
                "feedback_template": "Your meal needs energy foods! Consider adding rice, yam, amala, or fufu for sustained energy.",
                "priority": 3
            },
            {
                "rule_id": "well_balanced",
                "name": "Well Balanced Meal",
                "conditions": [
                    {"field": "balance_score", "operator": "gte", "value": 0.7},
                    {"field": "missing_groups_count",
                        "operator": "lte", "value": 1}
                ],
                "feedback_template": "Excellent! Your meal looks well-balanced with good variety. Keep up the healthy eating!",
                "priority": 10
            },
            {
                "rule_id": "too_much_carbs",
                "name": "Excessive Carbohydrates",
                "conditions": [
                    {"field": "carbohydrates", "operator": "gt", "value": 0.6}
                ],
                "feedback_template": "Your meal has a lot of carbohydrates. Try balancing it with more protein and vegetables next time.",
                "priority": 2
            },
            {
                "rule_id": "good_protein",
                "name": "Good Protein Content",
                "conditions": [
                    {"field": "proteins", "operator": "gte", "value": 0.2}
                ],
                "feedback_template": "Great protein choice! This will help build and repair your muscles.",
                "priority": 6
            },
            {
                "rule_id": "traditional_combo",
                "name": "Traditional Nigerian Combination",
                "conditions": [
                    {"field": "detected_food_names",
                        "operator": "contains", "value": "amala"},
                    {"field": "detected_food_names",
                        "operator": "contains", "value": "efo_riro"}
                ],
                "feedback_template": "Nice traditional combination! Amala and efo riro is a classic Nigerian meal that provides good energy and nutrients.",
                "priority": 7
            },
            {
                "rule_id": "rice_and_beans",
                "name": "Rice and Beans Combination",
                "conditions": [
                    {"field": "food_classes", "operator": "contains",
                        "value": "carbohydrates"},
                    {"field": "detected_food_names",
                        "operator": "contains", "value": "beans"}
                ],
                "feedback_template": "Rice and beans is a perfect combination! You're getting both energy and protein in one meal.",
                "priority": 8
            }
        ]

        # Add default rules to engine
        for rule_data in default_rules:
            rule = NutritionRule(
                rule_id=rule_data["rule_id"],
                name=rule_data["name"],
                conditions=rule_data["conditions"],
                feedback_template=rule_data["feedback_template"],
                priority=rule_data["priority"]
            )
            nutrition_engine.add_rule(rule)

    async def create_rule(self, rule_data: NutritionRuleCreate, db: Session) -> NutritionRuleResponse:
        """Create a new nutrition rule."""
        # Create database record
        db_rule = NutritionRuleModel(
            rule_name=rule_data.rule_name,
            condition_logic=rule_data.condition_logic,
            feedback_template=rule_data.feedback_template,
            priority=rule_data.priority,
            is_active=rule_data.is_active
        )

        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)

        # Add to engine
        engine_rule = NutritionRule(
            rule_id=str(db_rule.id),
            name=rule_data.rule_name,
            conditions=rule_data.condition_logic.get("conditions", []),
            feedback_template=rule_data.feedback_template,
            priority=rule_data.priority,
            is_active=rule_data.is_active
        )
        nutrition_engine.add_rule(engine_rule)

        return NutritionRuleResponse(
            id=db_rule.id,
            rule_name=db_rule.rule_name,
            condition_logic=db_rule.condition_logic,
            feedback_template=db_rule.feedback_template,
            priority=db_rule.priority,
            is_active=db_rule.is_active,
            created_at=db_rule.created_at,
            updated_at=db_rule.updated_at
        )

    async def get_rule(self, rule_id: UUID, db: Session) -> Optional[NutritionRuleResponse]:
        """Get a nutrition rule by ID."""
        db_rule = db.query(NutritionRuleModel).filter(
            NutritionRuleModel.id == rule_id
        ).first()

        if not db_rule:
            return None

        return NutritionRuleResponse(
            id=db_rule.id,
            rule_name=db_rule.rule_name,
            condition_logic=db_rule.condition_logic,
            feedback_template=db_rule.feedback_template,
            priority=db_rule.priority,
            is_active=db_rule.is_active,
            created_at=db_rule.created_at,
            updated_at=db_rule.updated_at
        )

    async def get_all_rules(self, db: Session, active_only: bool = False) -> List[NutritionRuleResponse]:
        """Get all nutrition rules."""
        query = db.query(NutritionRuleModel)

        if active_only:
            query = query.filter(NutritionRuleModel.is_active == True)

        db_rules = query.order_by(NutritionRuleModel.priority.desc()).all()

        return [
            NutritionRuleResponse(
                id=rule.id,
                rule_name=rule.rule_name,
                condition_logic=rule.condition_logic,
                feedback_template=rule.feedback_template,
                priority=rule.priority,
                is_active=rule.is_active,
                created_at=rule.created_at,
                updated_at=rule.updated_at
            )
            for rule in db_rules
        ]

    async def update_rule(self, rule_id: UUID, rule_data: NutritionRuleUpdate,
                          db: Session) -> Optional[NutritionRuleResponse]:
        """Update a nutrition rule."""
        db_rule = db.query(NutritionRuleModel).filter(
            NutritionRuleModel.id == rule_id
        ).first()

        if not db_rule:
            return None

        # Update database record
        update_data = rule_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_rule, field, value)

        db.commit()
        db.refresh(db_rule)

        # Update engine rule
        engine_rule = NutritionRule(
            rule_id=str(db_rule.id),
            name=db_rule.rule_name,
            conditions=db_rule.condition_logic.get("conditions", []),
            feedback_template=db_rule.feedback_template,
            priority=db_rule.priority,
            is_active=db_rule.is_active
        )
        nutrition_engine.update_rule(str(rule_id), engine_rule)

        return NutritionRuleResponse(
            id=db_rule.id,
            rule_name=db_rule.rule_name,
            condition_logic=db_rule.condition_logic,
            feedback_template=db_rule.feedback_template,
            priority=db_rule.priority,
            is_active=db_rule.is_active,
            created_at=db_rule.created_at,
            updated_at=db_rule.updated_at
        )

    async def delete_rule(self, rule_id: UUID, db: Session) -> bool:
        """Delete a nutrition rule."""
        db_rule = db.query(NutritionRuleModel).filter(
            NutritionRuleModel.id == rule_id
        ).first()

        if not db_rule:
            return False

        # Remove from engine
        nutrition_engine.remove_rule(str(rule_id))

        # Delete from database
        db.delete(db_rule)
        db.commit()

        return True

    async def load_rules_from_database(self, db: Session) -> None:
        """Load all active rules from database into engine."""
        db_rules = db.query(NutritionRuleModel).filter(
            NutritionRuleModel.is_active == True
        ).all()

        for db_rule in db_rules:
            engine_rule = NutritionRule(
                rule_id=str(db_rule.id),
                name=db_rule.rule_name,
                conditions=db_rule.condition_logic.get("conditions", []),
                feedback_template=db_rule.feedback_template,
                priority=db_rule.priority,
                is_active=db_rule.is_active
            )
            nutrition_engine.add_rule(engine_rule)


# Global service instance
nutrition_rule_service = NutritionRuleService()
