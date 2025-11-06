"""
CRUD Tests for Diary API

Tests:
- Create Diary Entry (POST /api/diary)
- Read Diary Entry (GET /api/diary/<id>)
- Update Diary Entry (PUT /api/diary/<id>)
- Delete Diary Entry (DELETE /api/diary/<id>)
- List Diary Entries (GET /api/diary)
"""
import pytest


class TestDiaryCreate:
    """Test Diary Entry Creation"""

    def test_create_diary_entry_success(self, api_client, cleanup_test_diary_entries, sample_diary_entry_data):
        """Test successful diary entry creation"""
        response = api_client.post("/diary", json=sample_diary_entry_data)

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()

        assert "id" in data
        assert data["title"] == sample_diary_entry_data["title"]
        assert data["content"] == sample_diary_entry_data["content"]

        # Register for cleanup
        cleanup_test_diary_entries(data["id"])

    def test_create_diary_entry_missing_title(self, api_client):
        """Test diary entry creation fails without title"""
        response = api_client.post("/diary", json={
            "content": "Test content"
        })

        assert response.status_code == 400

    def test_create_diary_entry_with_recipe_link(self, api_client, cleanup_test_diary_entries, cleanup_test_recipes, sample_recipe_data, sample_diary_entry_data):
        """Test diary entry with linked recipe"""
        # Create recipe first
        recipe_response = api_client.post("/recipes", json=sample_recipe_data)
        recipe_id = recipe_response.json()["id"]
        cleanup_test_recipes(recipe_id)

        # Create diary entry with recipe link
        diary_data = sample_diary_entry_data.copy()
        diary_data["recipe_id"] = recipe_id

        response = api_client.post("/diary", json=diary_data)

        assert response.status_code == 201
        data = response.json()

        cleanup_test_diary_entries(data["id"])

        # Verify recipe link
        if "recipe_id" in data:
            assert data["recipe_id"] == recipe_id


class TestDiaryRead:
    """Test Diary Entry Reading"""

    def test_get_diary_entry_by_id(self, api_client, cleanup_test_diary_entries, sample_diary_entry_data):
        """Test retrieving diary entry by ID"""
        # Create diary entry
        create_response = api_client.post("/diary", json=sample_diary_entry_data)
        entry_id = create_response.json()["id"]
        cleanup_test_diary_entries(entry_id)

        # Get diary entry
        response = api_client.get(f"/diary/{entry_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == entry_id
        assert data["title"] == sample_diary_entry_data["title"]
        assert "content" in data

    def test_get_diary_entry_not_found(self, api_client):
        """Test getting non-existent diary entry returns 404"""
        response = api_client.get("/diary/999999")

        assert response.status_code == 404

    def test_list_diary_entries(self, api_client):
        """Test listing all diary entries"""
        response = api_client.get("/diary")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            assert "id" in data[0]
            assert "title" in data[0]


class TestDiaryUpdate:
    """Test Diary Entry Updates"""

    def test_update_diary_entry_title(self, api_client, cleanup_test_diary_entries, sample_diary_entry_data):
        """Test updating diary entry title"""
        # Create diary entry
        create_response = api_client.post("/diary", json=sample_diary_entry_data)
        entry_id = create_response.json()["id"]
        cleanup_test_diary_entries(entry_id)

        # Update title
        updated_data = sample_diary_entry_data.copy()
        updated_data["title"] = "Updated Test Entry"

        response = api_client.put(f"/diary/{entry_id}", json=updated_data)

        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "Updated Test Entry"

    def test_update_diary_entry_content(self, api_client, cleanup_test_diary_entries, sample_diary_entry_data):
        """Test updating diary entry content"""
        # Create diary entry
        create_response = api_client.post("/diary", json=sample_diary_entry_data)
        entry_id = create_response.json()["id"]
        cleanup_test_diary_entries(entry_id)

        # Update content
        updated_data = sample_diary_entry_data.copy()
        updated_data["content"] = "Updated content for testing"

        response = api_client.put(f"/diary/{entry_id}", json=updated_data)

        assert response.status_code == 200
        data = response.json()

        assert data["content"] == "Updated content for testing"

    def test_update_diary_entry_not_found(self, api_client, sample_diary_entry_data):
        """Test updating non-existent diary entry returns 404"""
        response = api_client.put("/diary/999999", json=sample_diary_entry_data)

        assert response.status_code == 404


class TestDiaryDelete:
    """Test Diary Entry Deletion"""

    def test_delete_diary_entry_success(self, api_client, sample_diary_entry_data):
        """Test successful diary entry deletion"""
        # Create diary entry
        create_response = api_client.post("/diary", json=sample_diary_entry_data)
        entry_id = create_response.json()["id"]

        # Delete diary entry
        response = api_client.delete(f"/diary/{entry_id}")

        assert response.status_code == 200

        # Verify deleted
        get_response = api_client.get(f"/diary/{entry_id}")
        assert get_response.status_code == 404

    def test_delete_diary_entry_not_found(self, api_client):
        """Test deleting non-existent diary entry returns 404"""
        response = api_client.delete("/diary/999999")

        assert response.status_code == 404


class TestDiarySearch:
    """Test Diary Entry Search"""

    def test_search_diary_entries_by_title(self, api_client, cleanup_test_diary_entries):
        """Test searching diary entries by title"""
        # Create test diary entry with unique title
        test_data = {
            "title": "Unique Diary Entry pytest",
            "content": "Test content for search"
        }

        create_response = api_client.post("/diary", json=test_data)
        entry_id = create_response.json()["id"]
        cleanup_test_diary_entries(entry_id)

        # Search for entry
        response = api_client.get("/diary/search", params={"q": "Unique Diary"})

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Should find our entry
        found = any(entry["id"] == entry_id for entry in data)
        assert found, f"Diary entry {entry_id} not found in search results"

    def test_search_diary_entries_by_content(self, api_client, cleanup_test_diary_entries):
        """Test searching diary entries by content"""
        # Create test diary entry
        test_data = {
            "title": "Search Test Entry",
            "content": "This contains a unique search term: PyTestSearchTerm123"
        }

        create_response = api_client.post("/diary", json=test_data)
        entry_id = create_response.json()["id"]
        cleanup_test_diary_entries(entry_id)

        # Search for entry by content
        response = api_client.get("/diary/search", params={"q": "PyTestSearchTerm123"})

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Should find our entry
        found = any(entry["id"] == entry_id for entry in data)
        assert found, f"Diary entry {entry_id} not found in search results"
