"""Tests for dataset management functionality."""

import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from io import BytesIO

from app.main import app
from app.models.meal import NigerianFood
from app.models.admin import AdminUser, AdminRole
from app.services.nigerian_food_service import NigerianFoodService
from app.core.auth import get_password_hash


@pytest.fixture
def food_service(db_session: Session):
    """Create Nigerian food service instance."""
    return NigerianFoodService(db_session)


@pytest.fixture
def test_dataset_admin(db_session: Session):
    """Create a test dataset admin user."""
    admin_user = AdminUser(
        email="dataset@test.com",
        name="Dataset Admin",
        password_hash=get_password_hash("datasetpassword123"),
        role=AdminRole.DATASET_MANAGER.value,
        is_active=True
    )
    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)
    return admin_user


@pytest.fixture
def test_food_item(db_session: Session):
    """Create a test Nigerian food item."""
    food_item = NigerianFood(
        food_name="Jollof Rice",
        local_names={"yoruba": ["jollof"], "igbo": ["jollof rice"]},
        food_class="carbohydrates",
        nutritional_info={
            "calories_per_100g": 150,
            "carbohydrates": 30,
            "protein": 3,
            "fat": 2
        },
        cultural_context="Popular West African rice dish"
    )
    db_session.add(food_item)
    db_session.commit()
    db_session.refresh(food_item)
    return food_item


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def admin_token(client: TestClient, test_dataset_admin):
    """Get admin authentication token."""
    response = client.post(
        "/api/v1/admin/login",
        json={
            "email": test_dataset_admin.email,
            "password": "datasetpassword123"
        }
    )
    return response.json()["access_token"]


class TestNigerianFoodService:
    """Test Nigerian food service functionality."""

    def test_create_food_item(self, food_service: NigerianFoodService):
        """Test creating a new food item."""
        from app.models.meal import NigerianFoodCreate

        food_data = NigerianFoodCreate(
            food_name="Amala",
            local_names={"yoruba": ["amala", "elubo"]},
            food_class="carbohydrates",
            nutritional_info={"calories_per_100g": 120},
            cultural_context="Traditional Yoruba food made from yam flour"
        )

        food_item = food_service.create_food_item(food_data)

        assert food_item.food_name == "Amala"
        assert food_item.local_names == {"yoruba": ["amala", "elubo"]}
        assert food_item.food_class == "carbohydrates"
        assert food_item.nutritional_info == {"calories_per_100g": 120}

    def test_create_duplicate_food_item(self, food_service: NigerianFoodService, test_food_item):
        """Test creating duplicate food item."""
        from app.models.meal import NigerianFoodCreate
        from fastapi import HTTPException

        food_data = NigerianFoodCreate(
            food_name=test_food_item.food_name,
            food_class="carbohydrates"
        )

        with pytest.raises(HTTPException) as exc_info:
            food_service.create_food_item(food_data)

        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)

    def test_get_food_item(self, food_service: NigerianFoodService, test_food_item):
        """Test getting food item by ID."""
        food_item = food_service.get_food_item(test_food_item.id)

        assert food_item is not None
        assert food_item.id == test_food_item.id
        assert food_item.food_name == test_food_item.food_name

    def test_update_food_item(self, food_service: NigerianFoodService, test_food_item):
        """Test updating food item."""
        from app.models.meal import NigerianFoodUpdate

        update_data = NigerianFoodUpdate(
            food_name="Updated Jollof Rice",
            cultural_context="Updated context"
        )

        updated_food = food_service.update_food_item(
            test_food_item.id, update_data)

        assert updated_food is not None
        assert updated_food.food_name == "Updated Jollof Rice"
        assert updated_food.cultural_context == "Updated context"
        assert updated_food.food_class == test_food_item.food_class  # Unchanged

    def test_delete_food_item(self, food_service: NigerianFoodService, test_food_item):
        """Test deleting food item."""
        success = food_service.delete_food_item(test_food_item.id)

        assert success is True

        # Verify item is deleted
        deleted_food = food_service.get_food_item(test_food_item.id)
        assert deleted_food is None

    def test_search_food_items(self, food_service: NigerianFoodService, test_food_item):
        """Test searching food items."""
        from app.models.meal import NigerianFoodSearchRequest

        search_request = NigerianFoodSearchRequest(
            query="jollof",
            skip=0,
            limit=10
        )

        foods, total_count = food_service.search_food_items(search_request)

        assert total_count >= 1
        assert len(foods) >= 1
        assert any(food.food_name.lower() == "jollof rice" for food in foods)

    def test_search_by_food_class(self, food_service: NigerianFoodService, test_food_item):
        """Test searching food items by class."""
        from app.models.meal import NigerianFoodSearchRequest

        search_request = NigerianFoodSearchRequest(
            food_class="carbohydrates",
            skip=0,
            limit=10
        )

        foods, total_count = food_service.search_food_items(search_request)

        assert total_count >= 1
        assert all(food.food_class == "carbohydrates" for food in foods)

    def test_get_food_classes(self, food_service: NigerianFoodService, test_food_item):
        """Test getting unique food classes."""
        classes = food_service.get_food_classes()

        assert isinstance(classes, list)
        assert "carbohydrates" in classes

    def test_bulk_create_food_items(self, food_service: NigerianFoodService):
        """Test bulk creating food items."""
        from app.models.meal import NigerianFoodCreate, NigerianFoodBulkCreate

        foods = [
            NigerianFoodCreate(
                food_name="Efo Riro",
                food_class="vitamins",
                cultural_context="Yoruba vegetable soup"
            ),
            NigerianFoodCreate(
                food_name="Suya",
                food_class="proteins",
                cultural_context="Grilled meat with spices"
            )
        ]

        bulk_data = NigerianFoodBulkCreate(foods=foods)
        result = food_service.bulk_create_food_items(bulk_data)

        assert result["created_count"] == 2
        assert result["failed_count"] == 0
        assert len(result["created_foods"]) == 2
        assert len(result["errors"]) == 0

    def test_import_from_json(self, food_service: NigerianFoodService):
        """Test importing foods from JSON."""
        json_data = [
            {
                "food_name": "Moimoi",
                "food_class": "proteins",
                "local_names": {"yoruba": ["moimoi"], "igbo": ["moi moi"]},
                "cultural_context": "Steamed bean pudding"
            },
            {
                "food_name": "Plantain",
                "food_class": "carbohydrates",
                "nutritional_info": {"calories_per_100g": 89}
            }
        ]

        json_string = json.dumps(json_data)
        result = food_service.import_from_json(json_string)

        assert result["created_count"] == 2
        assert result["failed_count"] == 0

    def test_export_to_json(self, food_service: NigerianFoodService, test_food_item):
        """Test exporting foods to JSON."""
        exported_data = food_service.export_to_json()

        assert isinstance(exported_data, list)
        assert len(exported_data) >= 1

        # Check if test food item is in export
        food_names = [item["food_name"] for item in exported_data]
        assert test_food_item.food_name in food_names

    def test_get_dataset_statistics(self, food_service: NigerianFoodService, test_food_item):
        """Test getting dataset statistics."""
        stats = food_service.get_dataset_statistics()

        assert "total_foods" in stats
        assert "class_distribution" in stats
        assert "foods_with_nutritional_info" in stats
        assert "foods_with_cultural_context" in stats
        assert "completion_percentage" in stats

        assert stats["total_foods"] >= 1
        assert "carbohydrates" in stats["class_distribution"]

    def test_validate_food_data(self, food_service: NigerianFoodService):
        """Test food data validation."""
        # Valid data
        valid_data = {
            "food_name": "Test Food",
            "food_class": "proteins",
            "local_names": {"yoruba": ["test"]},
            "nutritional_info": {"calories": 100}
        }

        errors = food_service.validate_food_data(valid_data)
        assert len(errors) == 0

        # Invalid data
        invalid_data = {
            "food_class": "proteins"
            # Missing food_name
        }

        errors = food_service.validate_food_data(invalid_data)
        assert len(errors) > 0
        assert any("food_name is required" in error for error in errors)


class TestDatasetEndpoints:
    """Test dataset management API endpoints."""

    def test_create_food_item_endpoint(self, client: TestClient, admin_token):
        """Test creating food item via API."""
        response = client.post(
            "/api/v1/dataset/foods",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "food_name": "Egusi Soup",
                "food_class": "vitamins",
                "local_names": {"yoruba": ["egusi"], "igbo": ["egwusi"]},
                "cultural_context": "Popular Nigerian soup made with melon seeds"
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert data["food_name"] == "Egusi Soup"
        assert data["food_class"] == "vitamins"
        assert data["local_names"] == {"yoruba": ["egusi"], "igbo": ["egwusi"]}

    def test_search_food_items_endpoint(self, client: TestClient, admin_token, test_food_item):
        """Test searching food items via API."""
        response = client.get(
            "/api/v1/dataset/foods/search?query=jollof&limit=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "foods" in data
        assert "total_count" in data
        assert data["total_count"] >= 1

    def test_get_food_item_endpoint(self, client: TestClient, admin_token, test_food_item):
        """Test getting food item via API."""
        response = client.get(
            f"/api/v1/dataset/foods/{test_food_item.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(test_food_item.id)
        assert data["food_name"] == test_food_item.food_name

    def test_update_food_item_endpoint(self, client: TestClient, admin_token, test_food_item):
        """Test updating food item via API."""
        response = client.put(
            f"/api/v1/dataset/foods/{test_food_item.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "food_name": "Updated Jollof Rice",
                "cultural_context": "Updated context"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["food_name"] == "Updated Jollof Rice"
        assert data["cultural_context"] == "Updated context"

    def test_delete_food_item_endpoint(self, client: TestClient, admin_token, test_food_item):
        """Test deleting food item via API."""
        response = client.delete(
            f"/api/v1/dataset/foods/{test_food_item.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        assert "successfully deleted" in response.json()["message"]

    def test_bulk_create_foods_endpoint(self, client: TestClient, admin_token):
        """Test bulk creating foods via API."""
        response = client.post(
            "/api/v1/dataset/foods/bulk",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "foods": [
                    {
                        "food_name": "Akara",
                        "food_class": "proteins",
                        "cultural_context": "Fried bean cakes"
                    },
                    {
                        "food_name": "Pounded Yam",
                        "food_class": "carbohydrates",
                        "cultural_context": "Traditional Nigerian swallow"
                    }
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["created_count"] == 2
        assert data["failed_count"] == 0
        assert len(data["created_foods"]) == 2

    def test_import_foods_from_json_endpoint(self, client: TestClient, admin_token):
        """Test importing foods from JSON file via API."""
        json_data = [
            {
                "food_name": "Banga Soup",
                "food_class": "vitamins",
                "cultural_context": "Palm nut soup"
            }
        ]

        json_content = json.dumps(json_data).encode('utf-8')

        response = client.post(
            "/api/v1/dataset/foods/import",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={"file": ("foods.json", BytesIO(
                json_content), "application/json")}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["created_count"] == 1
        assert data["failed_count"] == 0

    def test_get_food_classes_endpoint(self, client: TestClient, admin_token, test_food_item):
        """Test getting food classes via API."""
        response = client.get(
            "/api/v1/dataset/foods/classes",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "food_classes" in data
        assert isinstance(data["food_classes"], list)
        assert "carbohydrates" in data["food_classes"]

    def test_get_dataset_statistics_endpoint(self, client: TestClient, admin_token, test_food_item):
        """Test getting dataset statistics via API."""
        response = client.get(
            "/api/v1/dataset/statistics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "total_foods" in data
        assert "class_distribution" in data
        assert data["total_foods"] >= 1

    def test_unauthorized_access(self, client: TestClient):
        """Test accessing dataset endpoints without authentication."""
        response = client.get("/api/v1/dataset/foods/search")

        assert response.status_code == 401

    def test_validate_food_data_endpoint(self, client: TestClient, admin_token):
        """Test validating food data via API."""
        response = client.post(
            "/api/v1/dataset/foods/validate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "food_name": "Test Food",
                "food_class": "proteins"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "is_valid" in data
        assert "errors" in data
        assert data["is_valid"] is True
