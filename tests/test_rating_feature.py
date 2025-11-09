"""
Feature Tests für Rating Migration (Migration 0002)

Diese Tests prüfen, dass:
1. Ratings können zu Diary Entries hinzugefügt werden
2. Ratings werden bei GET /api/diary zurückgegeben
3. Ratings können beim Erstellen/Bearbeiten gesetzt werden
4. Rating-Feld ist optional (NULL erlaubt)
"""

import pytest


@pytest.mark.crud
def test_create_diary_entry_with_rating(api_client, cleanup_test_diary_entries):
    """Test: Diary Entry mit Rating erstellen"""
    # Recipe erstellen
    recipe_response = api_client.post('/api/recipes', json={
        'title': 'Test Recipe for Rating',
        'user_id': 1
    })
    recipe = recipe_response.json()
    assert recipe['id'] is not None

    # Diary Entry mit Rating erstellen
    entry_data = {
        'recipe_id': recipe['id'],
        'dish_name': 'Test Dish',
        'date': '2025-11-09',
        'notes': 'Sehr lecker!',
        'rating': 5,
        'user_id': 1
    }

    entry_response = api_client.post('/api/diary', json=entry_data)
    entry = entry_response.json()

    assert entry['id'] is not None
    assert entry['rating'] == 5
    assert entry['dish_name'] == 'Test Dish'

    cleanup_test_diary_entries.append(entry['id'])


@pytest.mark.crud
def test_create_diary_entry_without_rating(api_client, cleanup_test_diary_entries):
    """Test: Diary Entry ohne Rating erstellen (NULL)"""
    # Diary Entry ohne Rating
    entry_data = {
        'dish_name': 'Test Dish No Rating',
        'date': '2025-11-09',
        'notes': 'Noch nicht bewertet',
        'user_id': 1
    }

    entry_response = api_client.post('/api/diary', json=entry_data)
    entry = entry_response.json()

    assert entry['id'] is not None
    assert entry['rating'] is None
    assert entry['dish_name'] == 'Test Dish No Rating'

    cleanup_test_diary_entries.append(entry['id'])


@pytest.mark.crud
def test_update_diary_entry_rating(api_client, cleanup_test_diary_entries):
    """Test: Rating von Diary Entry aktualisieren"""
    # Diary Entry ohne Rating erstellen
    entry_response = api_client.post('/api/diary', json={
        'dish_name': 'Test Dish Update',
        'date': '2025-11-09',
        'notes': 'Test',
        'user_id': 1
    })
    entry = entry_response.json()

    assert entry['rating'] is None
    entry_id = entry['id']
    cleanup_test_diary_entries.append(entry_id)

    # Rating hinzufügen
    updated_response = api_client.put(f'/api/diary/{entry_id}', json={
        'rating': 4
    })
    updated = updated_response.json()

    assert updated['rating'] == 4

    # Rating ändern
    updated2_response = api_client.put(f'/api/diary/{entry_id}', json={
        'rating': 5
    })
    updated2 = updated2_response.json()

    assert updated2['rating'] == 5


@pytest.mark.crud
def test_get_diary_entry_includes_rating(api_client, cleanup_test_diary_entries):
    """Test: GET /api/diary gibt Rating zurück"""
    # Diary Entry mit Rating erstellen
    entry_response = api_client.post('/api/diary', json={
        'dish_name': 'Test Dish Get',
        'date': '2025-11-09',
        'rating': 3,
        'user_id': 1
    })
    entry = entry_response.json()

    entry_id = entry['id']
    cleanup_test_diary_entries.append(entry_id)

    # Einzelnen Entry abrufen
    fetched_response = api_client.get(f'/api/diary/{entry_id}')
    fetched = fetched_response.json()

    assert fetched['rating'] == 3
    assert fetched['id'] == entry_id


@pytest.mark.crud
def test_list_diary_entries_includes_rating(api_client, cleanup_test_diary_entries):
    """Test: GET /api/diary Liste enthält Rating"""
    # Mehrere Entries mit verschiedenen Ratings
    entry1_response = api_client.post('/api/diary', json={
        'dish_name': 'Test 1',
        'date': '2025-11-09',
        'rating': 5,
        'user_id': 1
    })
    entry1 = entry1_response.json()

    entry2_response = api_client.post('/api/diary', json={
        'dish_name': 'Test 2',
        'date': '2025-11-09',
        'rating': None,
        'user_id': 1
    })
    entry2 = entry2_response.json()

    cleanup_test_diary_entries.extend([entry1['id'], entry2['id']])

    # Liste abrufen
    entries_response = api_client.get('/api/diary')
    entries = entries_response.json()

    assert isinstance(entries, list)

    # Unsere Test-Entries finden
    test_entries = [e for e in entries if e['id'] in [entry1['id'], entry2['id']]]

    assert len(test_entries) == 2

    # Rating prüfen
    entry1_result = next(e for e in test_entries if e['id'] == entry1['id'])
    entry2_result = next(e for e in test_entries if e['id'] == entry2['id'])

    assert entry1_result['rating'] == 5
    assert entry2_result['rating'] is None


@pytest.mark.crud
def test_rating_validation_range(api_client, cleanup_test_diary_entries):
    """Test: Rating sollte zwischen 1 und 5 sein (Backend-Validierung optional)"""
    # Valides Rating (1-5)
    for rating in [1, 2, 3, 4, 5]:
        entry_response = api_client.post('/api/diary', json={
            'dish_name': f'Test Rating {rating}',
            'date': '2025-11-09',
            'rating': rating,
            'user_id': 1
        })
        entry = entry_response.json()

        assert entry['rating'] == rating
        cleanup_test_diary_entries.append(entry['id'])

    # Invalides Rating (0, 6) - Backend akzeptiert aktuell alles
    # TODO: Backend-Validierung implementieren wenn gewünscht


@pytest.mark.migration
def test_rating_column_exists_in_diary_entries(api_client):
    """Test: rating Spalte existiert in diary_entries Tabelle

    Dieser Test prüft indirekt ob Migration 0002 erfolgreich war.
    """
    # Wenn wir ein Diary Entry mit Rating erstellen können,
    # dann existiert die Spalte
    entry_response = api_client.post('/api/diary', json={
        'dish_name': 'Migration Test',
        'date': '2025-11-09',
        'rating': 4,
        'user_id': 1
    })
    entry = entry_response.json()

    assert 'rating' in entry
    assert entry['rating'] == 4

    # Cleanup
    api_client.delete(f'/api/diary/{entry["id"]}')


@pytest.mark.migration
def test_rating_migration_from_recipes_to_diary(api_client, cleanup_test_diary_entries):
    """Test: Workflow - Rating wird von Recipe zu Diary übertragen

    Simuliert den Workflow:
    1. Recipe mit Rating existiert
    2. User kocht das Recipe (erstellt Diary Entry)
    3. User bewertet das Kochereignis
    """
    # Recipe mit Rating erstellen (wie alte Daten)
    recipe_response = api_client.post('/api/recipes', json={
        'title': 'Recipe with Rating',
        'rating': 4,  # Altes System: Rating am Recipe
        'user_id': 1
    })
    recipe = recipe_response.json()

    assert recipe['rating'] == 4

    # User kocht das Recipe (neues System: Rating am Diary Entry)
    entry_response = api_client.post('/api/diary', json={
        'recipe_id': recipe['id'],
        'dish_name': 'Gekochtes Rezept',
        'date': '2025-11-09',
        'notes': 'War sehr gut!',
        'rating': 5,  # Neues System: Rating am Diary Entry
        'user_id': 1
    })
    entry = entry_response.json()

    assert entry['rating'] == 5  # Diary Entry hat eigenes Rating
    assert entry['recipe_id'] == recipe['id']

    # User kocht nochmal - andere Bewertung
    entry2_response = api_client.post('/api/diary', json={
        'recipe_id': recipe['id'],
        'dish_name': 'Gekochtes Rezept (2. Mal)',
        'date': '2025-11-10',
        'notes': 'Diesmal nicht so gut',
        'rating': 3,  # Neues System: Jedes Kochereignis eigene Bewertung
        'user_id': 1
    })
    entry2 = entry2_response.json()

    assert entry2['rating'] == 3
    assert entry2['recipe_id'] == recipe['id']

    cleanup_test_diary_entries.extend([entry['id'], entry2['id']])

    # Beide Diary Entries haben unterschiedliche Ratings
    # für das gleiche Recipe - genau wie gewünscht!
