#!/usr/bin/env python3
"""
Manual integration test script for mobile app flows.
Run this against a running backend instance to test all mobile app integration points.

Usage:
    1. Start the backend: uvicorn app.main:app --reload
    2. Run this script: python test_mobile_integration_manual.py
"""

import requests
import json
import time
from uuid import uuid4
from io import BytesIO
from PIL import Image

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = f"test_mobile_{uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "SecurePassword123!"
TEST_NAME = "Mobile Test User"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_test(name):
    """Print test name."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST: {name}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")


def print_success(message):
    """Print success message."""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message):
    """Print error message."""
    print(f"{RED}✗ {message}{RESET}")


def print_info(message):
    """Print info message."""
    print(f"{YELLOW}ℹ {message}{RESET}")


def create_test_image():
    """Create a test image."""
    img = Image.new('RGB', (800, 600), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes


# Task 12.1: Test authentication flow from mobile
def test_authentication_flow():
    """Test user registration and login flow."""
    print_test("Task 12.1: Authentication Flow")
    
    # Test 1: User Registration
    print_info("Testing user registration...")
    register_data = {
        "email": TEST_EMAIL,
        "name": TEST_NAME,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    
    if response.status_code == 201:
        data = response.json()
        print_success(f"Registration successful: {data['email']}")
        
        # Verify response structure
        assert "id" in data, "Missing 'id' in response"
        assert "email" in data, "Missing 'email' in response"
        assert "name" in data, "Missing 'name' in response"
        assert "registration_date" in data, "Missing 'registration_date' in response"
        assert "history_enabled" in data, "Missing 'history_enabled' in response"
        assert "password" not in data, "Password should not be in response"
        print_success("Response structure is correct")
    else:
        print_error(f"Registration failed: {response.status_code} - {response.text}")
        return None
    
    # Test 2: User Login
    print_info("Testing user login...")
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        print_success("Login successful")
        
        # Verify JWT token structure
        assert "access_token" in data, "Missing 'access_token' in response"
        assert "token_type" in data, "Missing 'token_type' in response"
        assert data["token_type"] == "bearer", "Token type should be 'bearer'"
        assert "expires_in" in data, "Missing 'expires_in' in response"
        assert "student" in data, "Missing 'student' in response"
        print_success("JWT token structure is correct")
        
        token = data["access_token"]
        return token
    else:
        print_error(f"Login failed: {response.status_code} - {response.text}")
        return None


def test_protected_endpoints(token):
    """Test token authentication on protected endpoints."""
    print_info("Testing protected endpoint access...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Protected endpoint accessible: {data['email']}")
    else:
        print_error(f"Protected endpoint failed: {response.status_code}")
    
    # Test without token
    print_info("Testing access without token...")
    response = requests.get(f"{BASE_URL}/auth/me")
    
    if response.status_code == 401:
        print_success("Correctly rejected request without token")
    else:
        print_error(f"Should have rejected request without token: {response.status_code}")


# Task 12.2: Test meal upload and analysis flow
def test_meal_upload_flow(token):
    """Test meal upload and analysis flow."""
    print_test("Task 12.2: Meal Upload and Analysis Flow")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Upload meal image
    print_info("Testing meal image upload...")
    test_image = create_test_image()
    files = {"file": ("test_meal.jpg", test_image, "image/jpeg")}
    
    response = requests.post(f"{BASE_URL}/meals/upload", files=files, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Image uploaded successfully: meal_id={data['meal_id']}")
        
        # Verify response format
        assert data["success"] is True, "Success should be True"
        assert "meal_id" in data, "Missing 'meal_id' in response"
        assert "message" in data, "Missing 'message' in response"
        assert "validation_results" in data, "Missing 'validation_results' in response"
        assert "file_info" in data, "Missing 'file_info' in response"
        print_success("Upload response format is correct")
        
        meal_id = data["meal_id"]
        return meal_id
    else:
        print_error(f"Upload failed: {response.status_code} - {response.text}")
        return None


def test_meal_analysis_polling(token, meal_id):
    """Test polling for meal analysis status."""
    print_info("Testing meal analysis status polling...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/meals/{meal_id}/analysis", headers=headers)
    
    if response.status_code == 200:
        print_success("Analysis endpoint accessible")
        print_info(f"Response: {response.json()}")
    else:
        print_error(f"Analysis polling failed: {response.status_code}")


# Task 12.3: Test feedback retrieval
def test_feedback_retrieval(token, meal_id):
    """Test feedback retrieval from mobile."""
    print_test("Task 12.3: Feedback Retrieval")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/meals/{meal_id}/feedback", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print_success("Feedback retrieved successfully")
        
        # Verify response format
        assert "detected_foods" in data, "Missing 'detected_foods'"
        assert "missing_food_groups" in data, "Missing 'missing_food_groups'"
        assert "recommendations" in data, "Missing 'recommendations'"
        assert "overall_balance_score" in data, "Missing 'overall_balance_score'"
        print_success("Feedback response format is correct")
        
        print_info(f"Detected foods: {len(data['detected_foods'])}")
        print_info(f"Missing food groups: {data['missing_food_groups']}")
        print_info(f"Balance score: {data['overall_balance_score']}")
    elif response.status_code == 404:
        print_info("Feedback not yet generated (expected for new meal)")
    else:
        print_error(f"Feedback retrieval failed: {response.status_code}")


# Task 12.4: Test meal history
def test_meal_history(token):
    """Test meal history retrieval."""
    print_test("Task 12.4: Meal History")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test without pagination
    print_info("Testing meal history without pagination...")
    response = requests.get(f"{BASE_URL}/meals/history", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print_success("Meal history retrieved successfully")
        
        # Verify response format
        assert "meals" in data, "Missing 'meals' in response"
        assert "total_count" in data, "Missing 'total_count' in response"
        assert "has_more" in data, "Missing 'has_more' in response"
        print_success("History response format is correct")
        
        print_info(f"Total meals: {data['total_count']}")
        print_info(f"Has more: {data['has_more']}")
    else:
        print_error(f"History retrieval failed: {response.status_code}")
    
    # Test with pagination
    print_info("Testing meal history with pagination...")
    response = requests.get(f"{BASE_URL}/meals/history?limit=10&offset=0", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Paginated history retrieved: {len(data['meals'])} meals")
    else:
        print_error(f"Paginated history failed: {response.status_code}")


# Task 12.5: Test weekly insights
def test_weekly_insights(token):
    """Test weekly insights retrieval."""
    print_test("Task 12.5: Weekly Insights")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/insights/weekly", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Weekly insights retrieved: {len(data)} weeks")
        
        # Verify response format
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            insight = data[0]
            assert "nutrition_balance" in insight, "Missing 'nutrition_balance'"
            
            balance = insight["nutrition_balance"]
            assert "carbohydrates" in balance, "Missing 'carbohydrates'"
            assert "proteins" in balance, "Missing 'proteins'"
            assert "fats" in balance, "Missing 'fats'"
            assert "vitamins" in balance, "Missing 'vitamins'"
            assert "minerals" in balance, "Missing 'minerals'"
            assert "water" in balance, "Missing 'water'"
            
            assert "improvement_areas" in insight, "Missing 'improvement_areas'"
            assert "positive_trends" in insight, "Missing 'positive_trends'"
            assert "recommendations" in insight, "Missing 'recommendations'"
            
            print_success("Insights response format is correct")
            print_info(f"Improvement areas: {insight['improvement_areas']}")
        else:
            print_info("No insights available yet (expected for new user)")
    else:
        print_error(f"Insights retrieval failed: {response.status_code}")


# Task 12.7: Test error handling
def test_error_handling(token):
    """Test error handling scenarios."""
    print_test("Task 12.7: Error Handling")
    
    # Test invalid token
    print_info("Testing invalid authentication token...")
    headers = {"Authorization": "Bearer invalid_token_12345"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 401:
        print_success("Correctly rejected invalid token")
    else:
        print_error(f"Should have rejected invalid token: {response.status_code}")
    
    # Test invalid image format
    print_info("Testing invalid image format...")
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": ("test.txt", BytesIO(b"not an image"), "text/plain")}
    response = requests.post(f"{BASE_URL}/meals/upload", files=files, headers=headers)
    
    if response.status_code in [400, 422, 500]:
        print_success(f"Correctly rejected invalid image format: {response.status_code}")
    else:
        print_info(f"Image validation response: {response.status_code}")


# Main test execution
def main():
    """Run all integration tests."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Mobile App Integration Tests{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"Backend URL: {BASE_URL}")
    print(f"Test Email: {TEST_EMAIL}")
    
    try:
        # Task 12.1: Authentication
        token = test_authentication_flow()
        if not token:
            print_error("Authentication failed - cannot continue")
            return
        
        test_protected_endpoints(token)
        
        # Task 12.2: Meal Upload
        meal_id = test_meal_upload_flow(token)
        if meal_id:
            test_meal_analysis_polling(token, meal_id)
            
            # Task 12.3: Feedback
            test_feedback_retrieval(token, meal_id)
        
        # Task 12.4: History
        test_meal_history(token)
        
        # Task 12.5: Insights
        test_weekly_insights(token)
        
        # Task 12.7: Error Handling
        test_error_handling(token)
        
        print(f"\n{GREEN}{'='*60}{RESET}")
        print(f"{GREEN}All tests completed!{RESET}")
        print(f"{GREEN}{'='*60}{RESET}\n")
        
    except Exception as e:
        print_error(f"Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
