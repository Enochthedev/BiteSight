"""Nutrition rules management service."""

import json
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.feedback import (
    NutritionRule, NutritionRuleCreate, NutritionRuleUpdate
)


class NutritionRulesService:
    """Service for nutrition rules management."""

    def __init__(self, db: Session):
        self.db = db

    def create_rule(self, rule_data: NutritionRuleCreate) -> NutritionRule:
        """Create a new nutrition rule."""
        # Check if rule name already exists
        existing_rule = self.db.query(NutritionRule).filter(
            func.lower(NutritionRule.rule_name) == rule_data.rule_name.lower()
        ).first()

        if existing_rule:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rule '{rule_data.rule_name}' already exists"
            )

        # Create new rule
        rule = NutritionRule(
            rule_name=rule_data.rule_name,
            condition_logic=rule_data.condition_logic,
            feedback_template=rule_data.feedback_template,
            priority=rule_data.priority,
            is_active=rule_data.is_active
        )

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)

        return rule

    def get_rule(self, rule_id: UUID) -> Optional[NutritionRule]:
        """Get nutrition rule by ID."""
        return self.db.query(NutritionRule).filter(
            NutritionRule.id == rule_id
        ).first()

    def update_rule(self, rule_id: UUID, rule_data: NutritionRuleUpdate) -> Optional[NutritionRule]:
        """Update nutrition rule."""
        rule = self.get_rule(rule_id)
        if not rule:
            return None

        # Check for name conflicts if updating name
        if rule_data.rule_name and rule_data.rule_name.lower() != rule.rule_name.lower():
            existing_rule = self.db.query(NutritionRule).filter(
                and_(
                    func.lower(
                        NutritionRule.rule_name) == rule_data.rule_name.lower(),
                    NutritionRule.id != rule_id
                )
            ).first()

            if existing_rule:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Rule '{rule_data.rule_name}' already exists"
                )

        # Update fields
        if rule_data.rule_name is not None:
            rule.rule_name = rule_data.rule_name
        if rule_data.condition_logic is not None:
            rule.condition_logic = rule_data.condition_logic
        if rule_data.feedback_template is not None:
            rule.feedback_template = rule_data.feedback_template
        if rule_data.priority is not None:
            rule.priority = rule_data.priority
        if rule_data.is_active is not None:
            rule.is_active = rule_data.is_active

        self.db.commit()
        self.db.refresh(rule)

        return rule

    def delete_rule(self, rule_id: UUID) -> bool:
        """Delete nutrition rule."""
        rule = self.get_rule(rule_id)
        if not rule:
            return False

        self.db.delete(rule)
        self.db.commit()
        return True

    def list_rules(self,
                   active_only: bool = False,
                   skip: int = 0,
                   limit: int = 100) -> Tuple[List[NutritionRule], int]:
        """List nutrition rules with optional filtering."""
        query = self.db.query(NutritionRule)

        if active_only:
            query = query.filter(NutritionRule.is_active == True)

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination and ordering
        rules = query.order_by(
            NutritionRule.priority.desc(),
            NutritionRule.created_at.desc()
        ).offset(skip).limit(limit).all()

        return rules, total_count

    def search_rules(self,
                     query_text: Optional[str] = None,
                     active_only: bool = False,
                     skip: int = 0,
                     limit: int = 100) -> Tuple[List[NutritionRule], int]:
        """Search nutrition rules by name or template content."""
        query = self.db.query(NutritionRule)

        if active_only:
            query = query.filter(NutritionRule.is_active == True)

        if query_text:
            search_term = f"%{query_text.lower()}%"
            query = query.filter(
                or_(
                    func.lower(NutritionRule.rule_name).like(search_term),
                    func.lower(NutritionRule.feedback_template).like(
                        search_term)
                )
            )

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination and ordering
        rules = query.order_by(
            NutritionRule.priority.desc(),
            NutritionRule.created_at.desc()
        ).offset(skip).limit(limit).all()

        return rules, total_count

    def activate_rule(self, rule_id: UUID) -> bool:
        """Activate a nutrition rule."""
        rule = self.get_rule(rule_id)
        if not rule:
            return False

        rule.is_active = True
        self.db.commit()
        return True

    def deactivate_rule(self, rule_id: UUID) -> bool:
        """Deactivate a nutrition rule."""
        rule = self.get_rule(rule_id)
        if not rule:
            return False

        rule.is_active = False
        self.db.commit()
        return True

    def update_rule_priority(self, rule_id: UUID, new_priority: int) -> bool:
        """Update rule priority."""
        rule = self.get_rule(rule_id)
        if not rule:
            return False

        rule.priority = new_priority
        self.db.commit()
        return True

    def get_active_rules_by_priority(self) -> List[NutritionRule]:
        """Get all active rules ordered by priority (highest first)."""
        return self.db.query(NutritionRule).filter(
            NutritionRule.is_active == True
        ).order_by(
            NutritionRule.priority.desc(),
            NutritionRule.created_at.desc()
        ).all()

    def test_rule_condition(self, rule_id: UUID, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test a rule's condition logic against provided data."""
        rule = self.get_rule(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )

        try:
            # This is a simplified rule evaluation
            # In a real implementation, you'd have a more sophisticated rule engine
            result = self._evaluate_rule_condition(
                rule.condition_logic, test_data)

            return {
                "rule_id": str(rule.id),
                "rule_name": rule.rule_name,
                "condition_met": result,
                "test_data": test_data,
                "feedback_template": rule.feedback_template if result else None
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error evaluating rule condition: {str(e)}"
            )

    def _evaluate_rule_condition(self, condition_logic: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Evaluate rule condition logic against data."""
        # This is a simplified implementation
        # A real rule engine would be more sophisticated

        if not condition_logic:
            return True

        # Handle different condition types
        condition_type = condition_logic.get("type", "simple")

        if condition_type == "missing_food_groups":
            required_groups = condition_logic.get("required_groups", [])
            detected_groups = data.get("detected_food_groups", [])
            missing_groups = [
                group for group in required_groups if group not in detected_groups]
            return len(missing_groups) > 0

        elif condition_type == "food_group_balance":
            min_groups = condition_logic.get("min_groups", 3)
            detected_groups = data.get("detected_food_groups", [])
            return len(detected_groups) < min_groups

        elif condition_type == "specific_food_present":
            required_foods = condition_logic.get("required_foods", [])
            detected_foods = data.get("detected_foods", [])
            detected_food_names = [
                food.get("name", "").lower() for food in detected_foods]
            return any(food.lower() in detected_food_names for food in required_foods)

        elif condition_type == "custom":
            # For custom conditions, you could implement a more complex evaluator
            # For now, just return True
            return True

        return False

    def validate_rule_condition(self, condition_logic: Dict[str, Any]) -> List[str]:
        """Validate rule condition logic and return list of errors."""
        errors = []

        if not isinstance(condition_logic, dict):
            errors.append("Condition logic must be a dictionary")
            return errors

        condition_type = condition_logic.get("type")
        if not condition_type:
            errors.append("Condition type is required")
            return errors

        valid_types = ["missing_food_groups",
                       "food_group_balance", "specific_food_present", "custom"]
        if condition_type not in valid_types:
            errors.append(
                f"Invalid condition type. Must be one of: {', '.join(valid_types)}")

        # Validate specific condition types
        if condition_type == "missing_food_groups":
            required_groups = condition_logic.get("required_groups")
            if not required_groups or not isinstance(required_groups, list):
                errors.append("required_groups must be a non-empty list")

        elif condition_type == "food_group_balance":
            min_groups = condition_logic.get("min_groups")
            if min_groups is None or not isinstance(min_groups, int) or min_groups < 1:
                errors.append("min_groups must be a positive integer")

        elif condition_type == "specific_food_present":
            required_foods = condition_logic.get("required_foods")
            if not required_foods or not isinstance(required_foods, list):
                errors.append("required_foods must be a non-empty list")

        return errors

    def validate_feedback_template(self, template: str) -> List[str]:
        """Validate feedback template and return list of errors."""
        errors = []

        if not template or not template.strip():
            errors.append("Feedback template cannot be empty")
            return errors

        # Check for common template variables
        valid_variables = [
            "{missing_groups}", "{detected_foods}", "{recommendations}",
            "{food_groups}", "{student_name}", "{meal_time}"
        ]

        # This is a basic validation - in a real system you might use a template engine
        # to validate template syntax more thoroughly

        return errors

    def duplicate_rule(self, rule_id: UUID, new_name: str) -> NutritionRule:
        """Duplicate an existing rule with a new name."""
        original_rule = self.get_rule(rule_id)
        if not original_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Original rule not found"
            )

        # Check if new name already exists
        existing_rule = self.db.query(NutritionRule).filter(
            func.lower(NutritionRule.rule_name) == new_name.lower()
        ).first()

        if existing_rule:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rule '{new_name}' already exists"
            )

        # Create duplicate rule
        duplicate_rule = NutritionRule(
            rule_name=new_name,
            condition_logic=original_rule.condition_logic.copy(
            ) if original_rule.condition_logic else {},
            feedback_template=original_rule.feedback_template,
            priority=original_rule.priority,
            is_active=False  # Start as inactive
        )

        self.db.add(duplicate_rule)
        self.db.commit()
        self.db.refresh(duplicate_rule)

        return duplicate_rule

    def get_rules_statistics(self) -> Dict[str, Any]:
        """Get statistics about nutrition rules."""
        total_rules = self.db.query(NutritionRule).count()
        active_rules = self.db.query(NutritionRule).filter(
            NutritionRule.is_active == True
        ).count()

        # Get priority distribution
        priority_stats = self.db.query(
            NutritionRule.priority,
            func.count(NutritionRule.id).label('count')
        ).group_by(NutritionRule.priority).all()

        priority_distribution = {row[0]: row[1] for row in priority_stats}

        return {
            "total_rules": total_rules,
            "active_rules": active_rules,
            "inactive_rules": total_rules - active_rules,
            "priority_distribution": priority_distribution,
            "activation_percentage": (active_rules / total_rules * 100) if total_rules > 0 else 0
        }
