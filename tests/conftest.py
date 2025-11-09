"""
Pytest Configuration and Fixtures for Rezept-Tagebuch Tests
"""
import pytest
import requests
import time
import os
import subprocess

# Test Configuration
TEST_PORT = "8001"  # Port when accessed from HOST
CONTAINER_NAME = "seaser-rezept-tagebuch-test"
TEST_DB_PATH = "/home/gabor/easer_projekte/rezept-tagebuch/data/test/rezepte.db"

# Determine if we're running inside a container or on the host
# When running inside container (via test-migration.sh), use localhost:80
# When running on host (local development), use localhost:8001
RUNNING_IN_CONTAINER = os.path.exists('/app/app.py')  # app.py exists at /app/ in container
if RUNNING_IN_CONTAINER:
    API_BASE_URL = "http://localhost:80"  # Same container, internal access (tests add /api)
else:
    API_BASE_URL = f"http://localhost:{TEST_PORT}"  # Host accessing container via port mapping (tests add /api)

@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for API requests"""
    return API_BASE_URL

@pytest.fixture(scope="session")
def verify_container_running():
    """Verify test environment is ready (container should already be running)"""
    print("\n🧪 Setting up test environment...")

    # When running inside container, assume environment is ready
    # When running on host, could check container status
    # For now, just verify API is accessible

    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get(f"{API_BASE_URL}/api/recipes", timeout=2)
            if response.status_code in [200, 404]:  # Either success or empty is fine
                print(f"✅ Test API is accessible at {API_BASE_URL}/api")
                break
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                print(f"⏳ Waiting for API to be ready... (attempt {i+1}/{max_retries})")
                time.sleep(1)
            else:
                print(f"❌ Failed to connect to API at {API_BASE_URL}/api")
                raise

    yield True

    print("\n✅ Test session complete")

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db(verify_container_running):
    """Clean test database before and after test session"""
    import os

    # Note: DB cleanup happens BEFORE container starts
    # The container will create and initialize a fresh database

    yield

    # Clean after tests (optional - comment out if you want to inspect DB after tests)
    # if os.path.exists(TEST_DB_PATH):
    #     os.remove(TEST_DB_PATH)
    #     print(f"🧹 Cleaned test database: {TEST_DB_PATH}")

@pytest.fixture(scope="function")
def api_client(api_base_url, verify_container_running):
    """HTTP client for API requests"""
    class APIClient:
        def __init__(self, base_url):
            self.base_url = base_url
            self.session = requests.Session()

        def get(self, endpoint, **kwargs):
            url = f"{self.base_url}{endpoint}"
            return self.session.get(url, **kwargs)

        def post(self, endpoint, **kwargs):
            url = f"{self.base_url}{endpoint}"
            return self.session.post(url, **kwargs)

        def put(self, endpoint, **kwargs):
            url = f"{self.base_url}{endpoint}"
            return self.session.put(url, **kwargs)

        def delete(self, endpoint, **kwargs):
            url = f"{self.base_url}{endpoint}"
            return self.session.delete(url, **kwargs)

    return APIClient(api_base_url)

@pytest.fixture(scope="function")
def cleanup_test_recipes(api_client):
    """Cleanup fixture - stores created recipe IDs and deletes them after test"""
    created_ids = []

    def add_recipe_id(recipe_id):
        created_ids.append(recipe_id)

    yield add_recipe_id

    # Cleanup after test
    for recipe_id in created_ids:
        try:
            api_client.delete(f"/recipes/{recipe_id}")
        except Exception as e:
            print(f"Warning: Failed to cleanup recipe {recipe_id}: {e}")

@pytest.fixture(scope="function")
def cleanup_test_diary_entries(api_client):
    """Cleanup fixture - stores created diary entry IDs and deletes them after test"""
    created_ids = []

    # Return the list itself so tests can use .append() and .extend()
    yield created_ids

    # Cleanup after test
    for entry_id in created_ids:
        try:
            api_client.delete(f"/diary/{entry_id}")
        except Exception as e:
            print(f"Warning: Failed to cleanup diary entry {entry_id}: {e}")

@pytest.fixture
def sample_recipe_data():
    """Sample recipe data for testing"""
    return {
        "title": "Test Rezept pytest",
        "notes": "SCHRITT 1\n\nTest Schritt 1 Beschreibung\n\nSCHRITT 2\n\nTest Schritt 2 Beschreibung\n\nZutaten:\n- 500g Mehl\n- 2 TL Salz",
        "rating": 4,
        "user_id": 1  # Default user for tests
    }

@pytest.fixture
def sample_diary_entry_data():
    """Sample diary entry data for testing"""
    from datetime import datetime
    return {
        "dish_name": "Test Gericht",
        "notes": "Dies ist ein Test-Tagebuch-Eintrag erstellt von pytest.",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "user_id": 1,  # Default user for tests
        "recipe_id": None,  # No linked recipe for basic test
        "images": []
    }
