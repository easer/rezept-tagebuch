"""
CRUD Tests for Diary API

The diary tracks when you cooked dishes (with or without recipe links).

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
        assert data["dish_name"] == sample_diary_entry_data["dish_name"]
        assert data["notes"] == sample_diary_entry_data["notes"]
        assert data["date"] == sample_diary_entry_data["date"]
        assert data["user_id"] == sample_diary_entry_data["user_id"]

        # Register for cleanup
        cleanup_test_diary_entries(data["id"])

    def test_create_diary_entry_missing_date(self, api_client):
        """Test diary entry creation fails without date"""
        response = api_client.post("/diary", json={
            "dish_name": "Test Gericht",
            "user_id": 1
        })

        # Should fail with NOT NULL constraint on date
        assert response.status_code == 400 or response.status_code == 500

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
        assert data["recipe_id"] == recipe_id
        # Should have recipe_title and recipe_image from JOIN
        if recipe_response.json().get("title"):
            assert data["recipe_title"] == recipe_response.json()["title"]


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
        assert data["dish_name"] == sample_diary_entry_data["dish_name"]
        assert data["notes"] == sample_diary_entry_data["notes"]

    def test_get_diary_entry_not_found(self, api_client):
        """Test getting non-existent diary entry returns 404"""
        response = api_client.get("/diary/999999")

        assert response.status_code == 404

    def test_list_diary_entries(self, api_client):
        """Test listing all diary entries"""
        response = api_client.get("/diary?user_id=1")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            assert "id" in data[0]
            # Diary entries have dish_name or recipe_title
            assert "dish_name" in data[0] or "recipe_title" in data[0]


class TestDiaryUpdate:
    """Test Diary Entry Updates"""

    def test_update_diary_entry_dish_name(self, api_client, cleanup_test_diary_entries, sample_diary_entry_data):
        """Test updating diary entry dish_name"""
        # Create diary entry
        create_response = api_client.post("/diary", json=sample_diary_entry_data)
        entry_id = create_response.json()["id"]
        cleanup_test_diary_entries(entry_id)

        # Update dish_name
        updated_data = sample_diary_entry_data.copy()
        updated_data["dish_name"] = "Updated Test Gericht"

        response = api_client.put(f"/diary/{entry_id}", json=updated_data)

        assert response.status_code == 200
        data = response.json()

        assert data["dish_name"] == "Updated Test Gericht"

    def test_update_diary_entry_notes(self, api_client, cleanup_test_diary_entries, sample_diary_entry_data):
        """Test updating diary entry notes"""
        # Create diary entry
        create_response = api_client.post("/diary", json=sample_diary_entry_data)
        entry_id = create_response.json()["id"]
        cleanup_test_diary_entries(entry_id)

        # Update notes
        updated_data = sample_diary_entry_data.copy()
        updated_data["notes"] = "Updated notes for testing"

        response = api_client.put(f"/diary/{entry_id}", json=updated_data)

        assert response.status_code == 200
        data = response.json()

        assert data["notes"] == "Updated notes for testing"

    def test_update_diary_entry_not_found(self, api_client, sample_diary_entry_data):
        """Test updating non-existent diary entry returns 500"""
        response = api_client.put("/diary/999999", json=sample_diary_entry_data)

        # API currently returns 500 for non-existent entries
        assert response.status_code == 500


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
        """Test deleting non-existent diary entry (API returns 200)"""
        response = api_client.delete("/diary/999999")

        # Diary API returns 200 even for non-existent entries
        assert response.status_code == 200


class TestDiarySearch:
    """Test Diary Entry Search"""

    def test_search_diary_entries_by_dish_name(self, api_client, cleanup_test_diary_entries, sample_diary_entry_data):
        """Test searching diary entries by dish name"""
        # Create test diary entry with unique dish name
        test_data = sample_diary_entry_data.copy()
        test_data["dish_name"] = "Unique Gericht pytest"

        create_response = api_client.post("/diary", json=test_data)
        entry_id = create_response.json()["id"]
        cleanup_test_diary_entries(entry_id)

        # Search for entry
        response = api_client.get("/diary?user_id=1&search=Unique Gericht")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Should find our entry
        found = any(entry["id"] == entry_id for entry in data)
        assert found, f"Diary entry {entry_id} not found in search results"

    def test_search_diary_entries_by_notes(self, api_client, cleanup_test_diary_entries, sample_diary_entry_data):
        """Test searching diary entries by notes"""
        # Create test diary entry
        test_data = sample_diary_entry_data.copy()
        test_data["notes"] = "This contains a unique search term: PyTestSearchTerm123"

        create_response = api_client.post("/diary", json=test_data)
        entry_id = create_response.json()["id"]
        cleanup_test_diary_entries(entry_id)

        # Search for entry by notes
        response = api_client.get("/diary?user_id=1&search=PyTestSearchTerm123")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Should find our entry
        found = any(entry["id"] == entry_id for entry in data)
        assert found, f"Diary entry {entry_id} not found in search results"
