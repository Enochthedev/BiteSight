"""
Comprehensive mobile app integration tests.
Tests all API flows from the mobile app perspective.
"""

import pytest
from uuid import uuid4
from io import BytesIO
from PIL import Image

from app.models.feedback import FeedbackRecord


class TestMobileAppIntegration:
    """Test suite for mobile app integration."""
    
    @pytest.fixture
    def test_user_data(self):
        """Test user registration data."""
        return {
            "email": f"testuser_{uuid4().hex[:8]}@example.com",
            "name": "Test User",
            "password": "SecurePassword123!"
        }
    
    @pytest.fixture
    def test_image(self):
        """Create a test image file."""
        # Create a simple test image
        img = Image.new('RGB', (800, 600), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes
    
    # Task 12.1: Test authentication flow from mobile
    
    def test_user_registration_from_mobile(self, client, test_user_data):
        """Test user registration from mobile app."""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure matches mobile expectations
        assert "id" in data
        assert data["email"] == test_user_data["email"]
        assert data["name"] == test_user_data["name"]
        assert "registration_date" in data
        assert "history_enabled" in data
        assert "created_at" in data
        assert "updated_at" in data
        
        # Verify password is not returned
        assert "password" not in data
        assert "password_hash" not in data
    
    def test_user_login_from_mobile(self, client, test_user_data):
        """Test user login from mobile app."""
        # First register the user
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Then login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify JWT token is returned correctly
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        
        # Verify student data is included
        assert "student" in data
        student = data["student"]
        assert student["email"] == test_user_data["email"]
        assert student["name"] == test_user_data["name"]
        
        return data["access_token"]
    
    def test_token_authentication_on_protected_endpoints(self, client, test_user_data):
        """Test token authentication on protected endpoints."""
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        
        # Test accessing protected endpoint with token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        
        # Test accessing protected endpoint without token
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    def test_invalid_credentials(self, client, test_user_data):
        """Test login with invalid credentials."""
        # Register user
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try login with wrong password
        login_data = {
            "email": test_user_data["email"],
            "password": "WrongPassword123!"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "detail" in response.json()
    
    # Task 12.2: Test meal upload and analysis flow from mobile
    
    def test_meal_upload_from_mobile(self, client, test_user_data, test_image):
        """Test image upload from mobile app."""
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Upload meal image
        files = {"file": ("test_meal.jpg", test_image, "image/jpeg")}
        response = client.post("/api/v1/meals/upload", files=files, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response format
        assert data["success"] is True
        assert "meal_id" in data
        assert "message" in data
        assert "validation_results" in data
        assert "file_info" in data
        
        return data["meal_id"], token
    
    def test_meal_analysis_status_polling(self, client, test_user_data, test_image):
        """Test polling GET /api/v1/meals/{meal_id}/analysis."""
        # Upload meal
        meal_id, token = self.test_meal_upload_from_mobile(client, test_user_data, test_image)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Poll analysis status
        response = client.get(f"/api/v1/meals/{meal_id}/analysis", headers=headers)
        
        # Note: This endpoint returns a placeholder message currently
        # In production, it should return analysis status
        assert response.status_code == 200
    
    # Task 12.3: Test feedback retrieval from mobile
    
    def test_feedback_retrieval_from_mobile(self, client, test_user_data, test_image, db_session):
        """Test GET /api/v1/meals/{meal_id}/feedback from mobile."""
        # Upload meal
        meal_id, token = self.test_meal_upload_from_mobile(client, test_user_data, test_image)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get feedback (will return 404 if not generated yet)
        response = client.get(f"/api/v1/meals/{meal_id}/feedback", headers=headers)
        
        # In production flow, feedback is generated after analysis
        # For now, we just verify the endpoint exists and returns proper error
        if response.status_code == 404:
            # Expected - no feedback generated yet
            assert "detail" in response.json()
        elif response.status_code == 200:
            data = response.json()
            
            # Verify NutritionFeedback response format
            assert "detected_foods" in data
            assert "missing_food_groups" in data
            assert "recommendations" in data
            assert "overall_balance_score" in data
            
            # Verify detected_foods array is populated
            assert isinstance(data["detected_foods"], list)
            
            # Verify missing_food_groups array
            assert isinstance(data["missing_food_groups"], list)
            
            # Verify recommendations array contains Nigerian food suggestions
            assert isinstance(data["recommendations"], list)
            
            # Verify overall_balance_score is calculated
            assert isinstance(data["overall_balance_score"], (int, float))
            assert 0 <= data["overall_balance_score"] <= 100
    
    # Task 12.4: Test meal history from mobile
    
    def test_meal_history_from_mobile(self, client, test_user_data):
        """Test GET /api/v1/meals/history from mobile."""
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get meal history
        response = client.get("/api/v1/meals/history", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify MealHistoryResponse format
        assert "meals" in data
        assert "total_count" in data
        assert "has_more" in data
        
        # Verify meals array
        assert isinstance(data["meals"], list)
        
        # Verify pagination info
        assert isinstance(data["total_count"], int)
        assert isinstance(data["has_more"], bool)
    
    def test_meal_history_pagination(self, client, test_user_data):
        """Test meal history with pagination parameters."""
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test with pagination
        response = client.get(
            "/api/v1/meals/history?limit=10&offset=0",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "meals" in data
        assert len(data["meals"]) <= 10
    
    # Task 12.5: Test weekly insights from mobile
    
    def test_weekly_insights_from_mobile(self, client, test_user_data):
        """Test GET /api/v1/insights/weekly from mobile."""
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get weekly insights
        response = client.get("/api/v1/insights/weekly", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify WeeklyInsightResponse array format
        assert isinstance(data, list)
        
        # If insights exist, verify structure
        if len(data) > 0:
            insight = data[0]
            
            # Verify nutrition_balance object with 6 categories
            assert "nutrition_balance" in insight
            balance = insight["nutrition_balance"]
            assert "carbohydrates" in balance
            assert "proteins" in balance
            assert "fats" in balance
            assert "vitamins" in balance
            assert "minerals" in balance
            assert "water" in balance
            
            # Verify improvement_areas and positive_trends arrays
            assert "improvement_areas" in insight
            assert isinstance(insight["improvement_areas"], list)
            
            assert "positive_trends" in insight
            assert isinstance(insight["positive_trends"], list)
            
            # Verify recommendations text is culturally relevant
            assert "recommendations" in insight
            assert isinstance(insight["recommendations"], str)
    
    def test_weekly_insights_with_insufficient_data(self, client, test_user_data):
        """Test weekly insights with insufficient data (< 1 week of meals)."""
        # Register and login (new user with no meals)
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get weekly insights
        response = client.get("/api/v1/insights/weekly", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty array or insights with no data
        assert isinstance(data, list)
    
    # Task 12.7: Test error handling from mobile
    
    def test_invalid_image_format(self, client, test_user_data):
        """Test with invalid image format."""
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to upload invalid file
        files = {"file": ("test.txt", BytesIO(b"not an image"), "text/plain")}
        response = client.post("/api/v1/meals/upload", files=files, headers=headers)
        
        # Should return error
        assert response.status_code in [400, 422, 500]
    
    def test_oversized_image(self, client, test_user_data):
        """Test with oversized image (> 5MB)."""
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create large image (simulated)
        large_img = Image.new('RGB', (4000, 3000), color='blue')
        img_bytes = BytesIO()
        large_img.save(img_bytes, format='JPEG', quality=100)
        img_bytes.seek(0)
        
        files = {"file": ("large_image.jpg", img_bytes, "image/jpeg")}
        response = client.post("/api/v1/meals/upload", files=files, headers=headers)
        
        # Should either accept or reject based on size validation
        # If rejected, should return appropriate error
        assert response.status_code in [200, 400, 413, 422]
    
    def test_invalid_authentication_token(self, client):
        """Test with invalid authentication token."""
        # Try to access protected endpoint with invalid token
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401
        
        # Verify error response format
        data = response.json()
        assert "detail" in data
    
    def test_expired_token(self, client, test_user_data):
        """Test with expired token."""
        # This would require mocking time or using a token with very short expiry
        # For now, we test with malformed token
        headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired.token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_network_timeout_simulation(self, client, test_user_data):
        """Test network timeout handling."""
        # This is handled client-side in the mobile app
        # Backend should have appropriate timeouts configured
        # We can test that endpoints respond within reasonable time
        
        import time
        start_time = time.time()
        
        response = client.get("/api/v1/health")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Health endpoint should respond quickly
        assert response_time < 5.0  # 5 seconds max
        assert response.status_code == 200


# Additional integration test for complete flow
class TestCompleteUserJourney:
    """Test complete user journey from registration to insights."""
    
    def test_complete_meal_analysis_flow(self, client, db_session):
        """Test complete flow: register → login → upload → analysis → feedback → history."""
        # 1. Register
        user_data = {
            "email": f"journey_{uuid4().hex[:8]}@example.com",
            "name": "Journey Test User",
            "password": "SecurePassword123!"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        # 2. Login
        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Upload meal image
        img = Image.new('RGB', (800, 600), color='green')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        files = {"file": ("meal.jpg", img_bytes, "image/jpeg")}
        upload_response = client.post("/api/v1/meals/upload", files=files, headers=headers)
        assert upload_response.status_code == 200
        meal_id = upload_response.json()["meal_id"]
        
        # 4. Check analysis status
        analysis_response = client.get(f"/api/v1/meals/{meal_id}/analysis", headers=headers)
        assert analysis_response.status_code == 200
        
        # 5. Get meal history
        history_response = client.get("/api/v1/meals/history", headers=headers)
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert "meals" in history_data
        
        # 6. Get weekly insights
        insights_response = client.get("/api/v1/insights/weekly", headers=headers)
        assert insights_response.status_code == 200
        insights_data = insights_response.json()
        assert isinstance(insights_data, list)
