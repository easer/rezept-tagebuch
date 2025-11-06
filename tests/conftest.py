"""
Pytest Configuration and Fixtures for Rezept-Tagebuch Tests
"""
import pytest
import requests
import time

# Test Configuration
API_BASE_URL = "http://localhost:8000/rezept-tagebuch-dev/api"
CONTAINER_NAME = "seaser-rezept-tagebuch-dev"

@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for API requests"""
    return API_BASE_URL

@pytest.fixture(scope="session")
def verify_container_running():
    """Verify dev container is running before tests"""
    import subprocess
    result = subprocess.run(
        ["podman", "ps", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"],
        capture_output=True,
        text=True
    )

    if CONTAINER_NAME not in result.stdout:
        pytest.fail(f"Container '{CONTAINER_NAME}' is not running. Run: ./build-dev.sh")

    return True

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
        "rating": 4
    }

@pytest.fixture
def sample_diary_entry_data():
    """Sample diary entry data for testing"""
    return {
        "title": "Test Tagebuch-Eintrag",
        "content": "Dies ist ein Test-Tagebuch-Eintrag erstellt von pytest.",
        "mood": "happy"
    }
