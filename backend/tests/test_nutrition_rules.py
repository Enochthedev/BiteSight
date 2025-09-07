"""Tests for nutrition rules management functionality."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.feedback import NutritionRule
from app.models.admin import AdminUser, AdminRole
from app.services.nutrition_rules_service import NutritionRulesService
from app.core.auth import get_password_hash


@pytest.fixture
def rules_service(db_session: Session):
    """Create nutrition rules service instance."""
    return NutritionRulesService(db_session)


@pytest.fixture
def test_nutritionist_admin(db_session: Session):
    """Create a test nutritionist admin user."""
    admin_user = AdminUser(
        email="nutritionist@test.com",
        name="Nutritionist Admin",
        password_hash=get_password_hash("nutritionistpassword123"),
        role=AdminRole.NUTRITIONIST.value,
        is_active=True
    )
    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)
    return admin_user


@pytest.fixture
def test_nutrition_rule(db_session: Session):
    """Create a test nutrition rule."""
    rule = NutritionRule(
        rule_name="Balanced Meal Check",
        condition_logic={
            "type": "food_group_balance",
            "min_groups": 3
        },
        feedback_template="Your meal is missing some food groups. Try adding {missing_groups} for better balance.",
        priority=1,
        is_active=True
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def admin_token(client: TestClient, test_nutritionist_admin):
    """Get admin authentication token."""
    response = client.post(
        "/api/v1/admin/login",
        json={
            "email": test_nutritionist_admin.email,
            "password": "nutritionistpassword123"
        }
    )
    return response.json()["access_token"]


class TestNutritionRulesService:
    """Test nutrition rules service functionality."""

    def test_create_rule(self, rules_service: NutritionRulesService):
        """Test creating a new nutrition rule."""
        from app.models.feedback import NutritionRuleCreate

        rule_data = NutritionRuleCreate(
            rule_name="Protein Check",
            condition_logic={
                "type": "missing_food_groups",
                "required_groups": ["proteins"]
            },
            feedback_template="Add some protein to your meal like beans, fish, or meat.",
            priority=2,
            is_active=True
        )

        rule = rules_service.create_rule(rule_data)

        assert rule.rule_name == "Protein Check"
        assert rule.condition_logic["type"] == "missing_food_groups"
        assert rule.priority == 2
        assert rule.is_active is True

    def test_create_duplicate_rule(self, rules_service: NutritionRulesService, test_nutrition_rule):
        """Test creating duplicate nutrition rule."""
        from app.models.feedback import NutritionRuleCreate
        from fastapi import HTTPException

        rule_data = NutritionRuleCreate(
            rule_name=test_nutrition_rule.rule_name,
            condition_logic={"type": "custom"},
            feedback_template="Test template"
        )

        with pytest.raises(HTTPException) as exc_info:
            rules_service.create_rule(rule_data)

        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)

    def test_get_rule(self, rules_service: NutritionRulesService, test_nutrition_rule):
        """Test getting rule by ID."""
        rule = rules_service.get_rule(test_nutrition_rule.id)

        assert rule is not None
        assert rule.id == test_nutrition_rule.id
        assert rule.rule_name == test_nutrition_rule.rule_name

    def test_update_rule(self, rules_service: NutritionRulesService, test_nutrition_rule):
        """Test updating nutrition rule."""
        from app.models.feedback import NutritionRuleUpdate

        update_data = NutritionRuleUpdate(
            rule_name="Updated Balanced Meal Check",
            priority=5,
            is_active=False
        )

        updated_rule = rules_service.update_rule(
            test_nutrition_rule.id, update_data)

        assert updated_rule is not None
        assert updated_rule.rule_name == "Updated Balanced Meal Check"
        assert updated_rule.priority == 5
        assert updated_rule.is_active is False

    def test_delete_rule(self, rules_service: NutritionRulesService, test_nutrition_rule):
        """Test deleting nutrition rule."""
        success = rules_service.delete_rule(test_nutrition_rule.id)

        assert success is True

        # Verify rule is deleted
        deleted_rule = rules_service.get_rule(test_nutrition_rule.id)
        assert deleted_rule is None

    def test_list_rules(self, rules_service: NutritionRulesService, test_nutrition_rule):
        """Test listing nutrition rules."""
        rules, total_count = rules_service.list_rules(skip=0, limit=10)

        assert total_count >= 1
        assert len(rules) >= 1
        assert any(rule.id == test_nutrition_rule.id for rule in rules)

    def test_list_active_rules_only(self, rules_service: NutritionRulesService, test_nutrition_rule):
        """Test listing only active rules."""
        rules, total_count = rules_service.list_rules(
            active_only=True, skip=0, limit=10)

        assert all(rule.is_active for rule in rules)
        assert any(rule.id == test_nutrition_rule.id for rule in rules)

    def test_search_rules(self, rules_service: NutritionRulesService, test_nutrition_rule):
        """Test searching nutrition rules."""
        rules, total_count = rules_service.search_rules(
            query_text="balanced",
            skip=0,
            limit=10
        )

        assert total_count >= 1
        assert any(rule.id == test_nutrition_rule.id for rule in rules)

    def test_activate_rule(self, rules_service: NutritionRulesService, test_nutrition_rule):
        """Test activating nutrition rule."""
        # First deactivate
        test_nutrition_rule.is_active = False
        rules_service.db.commit()

        # Then activate
        success = rules_service.activate_rule(test_nutrition_rule.id)

        assert success is True

        # Verify activation
        updated_rule = rules_service.get_rule(test_nutrition_rule.id)
        assert updated_rule.is_active is True

    def test_deactivate_rule(self, rules_service: NutritionRulesService, test_nutrition_rule):
        """Test deactivating nutrition rule."""
        success = rules_service.deactivate_rule(test_nutrition_rule.id)

        assert success is True

        # Verify deactivation
        updated_rule = rules_service.get_rule(test_nutrition_rule.id)
        assert updated_rule.is_active is False

    def test_update_rule_priority(self, rules_service: NutritionRulesService, test_nutrition_rule):
        """Test updating rule priority."""
        success = rules_service.update_rule_priority(
            test_nutrition_rule.id, 10)

        assert success is True

        # Verify priority update
        updated_rule = rules_service.get_rule(test_nutrition_rule.id)
        assert updated_rule.priority == 10

    def test_get_active_rules_by_priority(self, rules_service: NutritionRulesService, test_nutrition_rule):
        """Test getting active rules by priority."""
        rules = rules_service.get_active_rules_by_priority()

        assert len(rules) >= 1
        assert all(rule.is_active for rule in rules)

        # Check if rules are ordered by priority (descending)
        if len(rules) > 1:
            for i in range(len(rules) - 1):
                assert rules[i].priority >= rules[i + 1].priority

    def test_test_rule_condition(self, rules_service: NutritionRulesService, test_nutrition_rule):
        """Test testing rule condition."""
        test_data = {
            "detected_food_groups": ["carbohydrates", "proteins"]
        }

        result = rules_service.test_rule_condition(
            test_nutrition_rule.id, test_data)

        assert "rule_id" in result
        assert "rule_name" in result
        assert "condition_met" in result
        assert result["rule_id"] == str(test_nutrition_rule.id)

    def test_validate_rule_condition(self, rules_service: NutritionRulesService):
        """Test validating rule condition."""
        # Valid condition
        valid_condition = {
            "type": "missing_food_groups",
            "required_groups": ["proteins", "vitamins"]
        }

        errors = rules_service.validate_rule_condition(valid_condition)
        assert len(errors) == 0

        # Invalid condition
        invalid_condition = {
            "type": "invalid_type"
        }

        errors = rules_service.validate_rule_condition(invalid_condition)
        assert len(errors) > 0

    def test_validate_feedback_template(self, rules_service: NutritionRulesService):
        """Test validating feedback template."""
        # Valid template
        valid_template = "Your meal needs more {missing_groups}."
        errors = rules_service.validate_feedback_template(valid_template)
        assert len(errors) == 0

        # Invalid template (empty)
        invalid_template = ""
        errors = rules_service.validate_feedback_template(invalid_template)
        assert len(errors) > 0

    def test_duplicate_rule(self, rules_service: NutritionRulesService, test_nutrition_rule):
        """Test duplicating nutrition rule."""
        new_name = "Duplicated Balanced Meal Check"

        duplicated_rule = rules_service.duplicate_rule(
            test_nutrition_rule.id, new_name)

        assert duplicated_rule.rule_name == new_name
        assert duplicated_rule.condition_logic == test_nutrition_rule.condition_logic
        assert duplicated_rule.feedback_template == test_nutrition_rule.feedback_template
        assert duplicated_rule.is_active is False  # Should start as inactive

    def test_get_rules_statistics(self, rules_service: NutritionRulesService, test_nutrition_rule):
        """Test getting rules statistics."""
        stats = rules_service.get_rules_statistics()

        assert "total_rules" in stats
        assert "active_rules" in stats
        assert "inactive_rules" in stats
        assert "priority_distribution" in stats
        assert "activation_percentage" in stats

        assert stats["total_rules"] >= 1


class TestNutritionRulesEndpoints:
    """Test nutrition rules API endpoints."""

    def test_create_rule_endpoint(self, client: TestClient, admin_token):
        """Test creating nutrition rule via API."""
        response = client.post(
            "/api/v1/nutrition-rules/rules",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "rule_name": "Vegetable Check",
                "condition_logic": {
                    "type": "missing_food_groups",
                    "required_groups": ["vitamins"]
                },
                "feedback_template": "Add some vegetables to your meal for vitamins and minerals.",
                "priority": 3,
                "is_active": True
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert data["rule_name"] == "Vegetable Check"
        assert data["condition_logic"]["type"] == "missing_food_groups"
        assert data["priority"] == 3

    def test_list_rules_endpoint(self, client: TestClient, admin_token, test_nutrition_rule):
        """Test listing nutrition rules via API."""
        response = client.get(
            "/api/v1/nutrition-rules/rules",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_rule_endpoint(self, client: TestClient, admin_token, test_nutrition_rule):
        """Test getting nutrition rule via API."""
        response = client.get(
            f"/api/v1/nutrition-rules/rules/{test_nutrition_rule.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(test_nutrition_rule.id)
        assert data["rule_name"] == test_nutrition_rule.rule_name

    def test_update_rule_endpoint(self, client: TestClient, admin_token, test_nutrition_rule):
        """Test updating nutrition rule via API."""
        response = client.put(
            f"/api/v1/nutrition-rules/rules/{test_nutrition_rule.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "rule_name": "Updated Rule Name",
                "priority": 8
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["rule_name"] == "Updated Rule Name"
        assert data["priority"] == 8

    def test_delete_rule_endpoint(self, client: TestClient, admin_token, test_nutrition_rule):
        """Test deleting nutrition rule via API."""
        response = client.delete(
            f"/api/v1/nutrition-rules/rules/{test_nutrition_rule.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        assert "successfully deleted" in response.json()["message"]

    def test_activate_rule_endpoint(self, client: TestClient, admin_token, test_nutrition_rule):
        """Test activating nutrition rule via API."""
        response = client.post(
            f"/api/v1/nutrition-rules/rules/{test_nutrition_rule.id}/activate",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        assert "activated successfully" in response.json()["message"]

    def test_deactivate_rule_endpoint(self, client: TestClient, admin_token, test_nutrition_rule):
        """Test deactivating nutrition rule via API."""
        response = client.post(
            f"/api/v1/nutrition-rules/rules/{test_nutrition_rule.id}/deactivate",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        assert "deactivated successfully" in response.json()["message"]

    def test_test_rule_endpoint(self, client: TestClient, admin_token, test_nutrition_rule):
        """Test testing nutrition rule via API."""
        response = client.post(
            f"/api/v1/nutrition-rules/rules/{test_nutrition_rule.id}/test",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "detected_food_groups": ["carbohydrates"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "rule_id" in data
        assert "condition_met" in data

    def test_duplicate_rule_endpoint(self, client: TestClient, admin_token, test_nutrition_rule):
        """Test duplicating nutrition rule via API."""
        response = client.post(
            f"/api/v1/nutrition-rules/rules/{test_nutrition_rule.id}/duplicate?new_name=Duplicated Rule",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["rule_name"] == "Duplicated Rule"
        assert data["is_active"] is False

    def test_validate_condition_endpoint(self, client: TestClient, admin_token):
        """Test validating rule condition via API."""
        response = client.post(
            "/api/v1/nutrition-rules/rules/validate/condition",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "type": "missing_food_groups",
                "required_groups": ["proteins"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "is_valid" in data
        assert "errors" in data

    def test_get_statistics_endpoint(self, client: TestClient, admin_token, test_nutrition_rule):
        """Test getting rules statistics via API."""
        response = client.get(
            "/api/v1/nutrition-rules/statistics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "total_rules" in data
        assert "active_rules" in data
        assert data["total_rules"] >= 1

    def test_unauthorized_access(self, client: TestClient):
        """Test accessing nutrition rules endpoints without authentication."""
        response = client.get("/api/v1/nutrition-rules/rules")

        assert response.status_code == 401
