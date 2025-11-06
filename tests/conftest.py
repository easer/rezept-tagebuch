"""
Pytest Configuration and Fixtures for Rezept-Tagebuch Tests
"""
import pytest
import requests
import time

# Test Configuration
API_BASE_URL = "http://localhost:8000/rezept-tagebuch-dev/api"
CONTAINER_NAME = "seaser-rezept-tagebuch-dev"
TEST_DB_PATH = "/home/gabor/easer_projekte/rezept-tagebuch/data/test/rezepte.db"

# Tests use a separate test database to avoid conflicts with dev container

@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for API requests"""
    return API_BASE_URL

@pytest.fixture(scope="session")
def verify_container_running():
    """Verify dev container is running and configure for tests"""
    import subprocess
    import os

    print("\n🧪 Setting up test environment...")

    # Check if container is running
    result = subprocess.run(
        ["podman", "ps", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"],
        capture_output=True,
        text=True
    )

    if CONTAINER_NAME not in result.stdout:
        # Start container with TESTING_MODE
        print(f"Starting {CONTAINER_NAME} with TESTING_MODE...")
        subprocess.run([
            "podman", "run", "-d", "--rm",
            "--name", CONTAINER_NAME,
            "-p", "8000:80",
            "-v", "/home/gabor/easer_projekte/rezept-tagebuch/data:/data:Z",
            "-e", "TESTING_MODE=true",  # Enable test mode
            "seaser-rezept-tagebuch:dev"
        ], check=True)

        # Wait for container to be ready
        time.sleep(3)
        print("✅ Test container started with TESTING_MODE=true")
    else:
        print(f"✅ Container {CONTAINER_NAME} is already running")
        print("⚠️  Note: Using existing container (TESTING_MODE may not be active)")
        print("   For isolated test DB, restart container with: ./build-dev.sh")

    return True

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    """Clean test database before and after test session"""
    import os

    def clean():
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
            print(f"🧹 Cleaned test database: {TEST_DB_PATH}")

    # Clean before tests
    clean()

    yield

    # Clean after tests (optional - comment out if you want to inspect DB after tests)
    # clean()

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

    def add_entry_id(entry_id):
        created_ids.append(entry_id)

    yield add_entry_id

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
