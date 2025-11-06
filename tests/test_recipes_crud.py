"""
CRUD Tests for Recipe API

Tests:
- Create Recipe (POST /api/recipes)
- Read Recipe (GET /api/recipes/<id>)
- Update Recipe (PUT /api/recipes/<id>)
- Delete Recipe (DELETE /api/recipes/<id>)
- List Recipes (GET /api/recipes)
- Search Recipes (GET /api/recipes/search)
"""
import pytest


class TestRecipeCreate:
    """Test Recipe Creation"""

    def test_create_recipe_success(self, api_client, cleanup_test_recipes, sample_recipe_data):
        """Test successful recipe creation"""
        response = api_client.post("/recipes", json=sample_recipe_data)

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()

        assert "id" in data
        assert data["title"] == sample_recipe_data["title"]
        assert data["rating"] == sample_recipe_data["rating"]

        # Register for cleanup
        cleanup_test_recipes(data["id"])

    def test_create_recipe_missing_title(self, api_client):
        """Test recipe creation fails without title"""
        response = api_client.post("/recipes", json={
            "notes": "Test notes",
            "rating": 3
        })

        assert response.status_code == 400

    def test_create_recipe_with_image(self, api_client, cleanup_test_recipes, sample_recipe_data):
        """Test recipe creation with image upload"""
        # Create recipe first
        response = api_client.post("/recipes", json=sample_recipe_data)
        assert response.status_code == 201

        recipe_id = response.json()["id"]
        cleanup_test_recipes(recipe_id)

        # Upload image to general upload endpoint
        # NOTE: The app uses /api/upload, not /recipes/{id}/upload
        # Image upload is separate from recipe creation
        files = {
            'file': ('test.jpg', b'fake-image-data', 'image/jpeg')
        }
        upload_response = api_client.post("/upload", files=files)

        # Accept both 200 and 201 for image upload
        assert upload_response.status_code in [200, 201]

        # Check that response contains filename
        if upload_response.status_code == 200:
            data = upload_response.json()
            assert "filename" in data or "url" in data


class TestRecipeRead:
    """Test Recipe Reading"""

    def test_get_recipe_by_id(self, api_client, cleanup_test_recipes, sample_recipe_data):
        """Test retrieving recipe by ID"""
        # Create recipe
        create_response = api_client.post("/recipes", json=sample_recipe_data)
        recipe_id = create_response.json()["id"]
        cleanup_test_recipes(recipe_id)

        # Get recipe
        response = api_client.get(f"/recipes/{recipe_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == recipe_id
        assert data["title"] == sample_recipe_data["title"]
        assert "notes" in data
        assert "rating" in data

    def test_get_recipe_not_found(self, api_client):
        """Test getting non-existent recipe returns 404"""
        response = api_client.get("/recipes/999999")

        assert response.status_code == 404

    def test_list_recipes(self, api_client):
        """Test listing all recipes"""
        response = api_client.get("/recipes")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            assert "id" in data[0]
            assert "title" in data[0]


class TestRecipeUpdate:
    """Test Recipe Updates"""

    def test_update_recipe_title(self, api_client, cleanup_test_recipes, sample_recipe_data):
        """Test updating recipe title"""
        # Create recipe
        create_response = api_client.post("/recipes", json=sample_recipe_data)
        recipe_id = create_response.json()["id"]
        cleanup_test_recipes(recipe_id)

        # Update title
        updated_data = sample_recipe_data.copy()
        updated_data["title"] = "Updated Test Rezept"

        response = api_client.put(f"/recipes/{recipe_id}", json=updated_data)

        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "Updated Test Rezept"

    def test_update_recipe_rating(self, api_client, cleanup_test_recipes, sample_recipe_data):
        """Test updating recipe rating"""
        # Create recipe
        create_response = api_client.post("/recipes", json=sample_recipe_data)
        recipe_id = create_response.json()["id"]
        cleanup_test_recipes(recipe_id)

        # Update rating
        updated_data = sample_recipe_data.copy()
        updated_data["rating"] = 5

        response = api_client.put(f"/recipes/{recipe_id}", json=updated_data)

        assert response.status_code == 200
        data = response.json()

        assert data["rating"] == 5

    def test_update_recipe_not_found(self, api_client, sample_recipe_data):
        """Test updating non-existent recipe returns 404"""
        response = api_client.put("/recipes/999999", json=sample_recipe_data)

        assert response.status_code == 404


class TestRecipeDelete:
    """Test Recipe Deletion"""

    def test_delete_recipe_success(self, api_client, sample_recipe_data):
        """Test successful recipe deletion"""
        # Create recipe
        create_response = api_client.post("/recipes", json=sample_recipe_data)
        recipe_id = create_response.json()["id"]

        # Delete recipe (requires user_id)
        response = api_client.delete(f"/recipes/{recipe_id}?user_id=1")

        assert response.status_code == 200

        # Verify deleted
        get_response = api_client.get(f"/recipes/{recipe_id}")
        assert get_response.status_code == 404

    def test_delete_recipe_not_found(self, api_client):
        """Test deleting non-existent recipe returns 404"""
        response = api_client.delete("/recipes/999999?user_id=1")

        assert response.status_code == 404


class TestRecipeSearch:
    """Test Recipe Search"""

    def test_search_recipes_by_title(self, api_client, cleanup_test_recipes, sample_recipe_data):
        """Test searching recipes by title"""
        # Create test recipe with unique title
        test_data = sample_recipe_data.copy()
        test_data["title"] = "Unique Pizza Recipe pytest"

        create_response = api_client.post("/recipes", json=test_data)
        recipe_id = create_response.json()["id"]
        cleanup_test_recipes(recipe_id)

        # Search for recipe using query parameter
        response = api_client.get("/recipes", params={"user_id": 1, "search": "Unique Pizza"})

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Should find our recipe
        found = any(recipe["id"] == recipe_id for recipe in data)
        assert found, f"Recipe {recipe_id} not found in search results"

    def test_search_recipes_empty_query(self, api_client):
        """Test search with empty query returns all recipes"""
        response = api_client.get("/recipes", params={"user_id": 1})

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)


class TestRecipeParser:
    """Test Recipe Parser Integration"""

    def test_recipe_with_schritt_format(self, api_client, cleanup_test_recipes, sample_recipe_data):
        """Test recipe with SCHRITT formatting is stored correctly"""
        test_data = sample_recipe_data.copy()
        test_data["title"] = "Parser Test Rezept"
        test_data["notes"] = "SCHRITT 1\n\nMehl und Salz mischen.\n\nSCHRITT 2\n\nWasser hinzufügen.\n\nZutaten:\n- 500g Mehl\n- 2 TL Salz\n- 300ml Wasser"

        create_response = api_client.post("/recipes", json=test_data)
        recipe_id = create_response.json()["id"]
        cleanup_test_recipes(recipe_id)

        # Retrieve recipe
        get_response = api_client.get(f"/recipes/{recipe_id}")
        data = get_response.json()

        # Verify SCHRITT formatting preserved
        assert "SCHRITT 1" in data["notes"]
        assert "SCHRITT 2" in data["notes"]
        assert "Zutaten:" in data["notes"]
