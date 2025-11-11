"""
Performance Tests for Recipe Imports

Tests that recipe imports complete within acceptable time limits:
- TheMealDB Import: < 3 seconds
- Migusto Import: < 3 seconds

These tests ensure the batch translation optimization is effective.
"""
import pytest
import requests
import time
from datetime import datetime

# Test configuration
# When running inside container: http://localhost:80
# When running from host: http://localhost:8001
import os
BASE_URL = os.getenv('TEST_BASE_URL', 'http://localhost:80')
TIMEOUT = 10  # Request timeout
PERFORMANCE_THRESHOLD_SECONDS = 3.0  # Max acceptable time


@pytest.mark.performance
@pytest.mark.integration
@pytest.mark.slow
def test_themealdb_import_performance():
    """
    Test TheMealDB import performance

    Requirements:
    - Import must complete in < 3 seconds
    - Must return successful response
    - Must create recipe in database

    Tests the batch translation optimization (22 API calls → 1)
    """
    # Measure import time
    start_time = time.time()

    response = requests.post(
        f"{BASE_URL}/api/recipes/daily-import",
        params={
            'strategy': 'by_category',
            'value': 'Vegetarian'
        },
        timeout=TIMEOUT
    )

    elapsed_time = time.time() - start_time

    # Assert response is successful (200) or rejected meat (400)
    assert response.status_code in [200, 400], f"Unexpected status code: {response.status_code}"

    # If rejected (meat filter), that's OK - still test performance
    if response.status_code == 400:
        data = response.json()
        assert 'rejected_category' in data, "Expected rejected_category in response"
        print(f"⚠️  Recipe rejected (meat filter): {data.get('rejected_title')} ({data.get('rejected_category')})")
        print(f"✅ Rejection time: {elapsed_time:.2f}s (very fast!)")
        # Rejection should be instant (< 0.5s)
        assert elapsed_time < 0.5, f"Rejection took too long: {elapsed_time:.2f}s"
        return

    # Successful import
    data = response.json()
    assert data.get('success') is True, "Import was not successful"
    assert 'recipe_id' in data, "No recipe_id in response"
    assert 'title_de' in data, "No German title in response"

    # Performance assertion: Must be < 3 seconds
    print(f"✅ Import completed in {elapsed_time:.2f}s")
    print(f"   Recipe: {data.get('title')} → {data.get('title_de')}")
    print(f"   Category: {data.get('category')}, Area: {data.get('area')}")

    assert elapsed_time < PERFORMANCE_THRESHOLD_SECONDS, \
        f"Import took {elapsed_time:.2f}s (threshold: {PERFORMANCE_THRESHOLD_SECONDS}s)"


@pytest.mark.performance
@pytest.mark.integration
@pytest.mark.slow
def test_themealdb_import_performance_multiple():
    """
    Test TheMealDB import performance with multiple attempts

    Run 3 imports and ensure average time is < 3 seconds
    This accounts for network variance and meat filter rejections
    """
    times = []
    successful_imports = 0

    categories = ['Vegetarian', 'Dessert', 'Vegan']

    for category in categories:
        start_time = time.time()

        try:
            response = requests.post(
                f"{BASE_URL}/api/recipes/daily-import",
                params={
                    'strategy': 'by_category',
                    'value': category
                },
                timeout=TIMEOUT
            )

            elapsed_time = time.time() - start_time
            times.append(elapsed_time)

            if response.status_code == 200:
                successful_imports += 1
                data = response.json()
                print(f"✅ Import {successful_imports}: {data.get('title_de')} in {elapsed_time:.2f}s")
            else:
                data = response.json()
                print(f"⚠️  Rejected: {data.get('rejected_title')} in {elapsed_time:.2f}s")

        except Exception as e:
            print(f"❌ Import failed: {e}")
            continue

    # Calculate statistics
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        print(f"\n📊 Performance Statistics:")
        print(f"   Attempts: {len(times)}")
        print(f"   Successful: {successful_imports}")
        print(f"   Average: {avg_time:.2f}s")
        print(f"   Min: {min_time:.2f}s")
        print(f"   Max: {max_time:.2f}s")

        # Assert average is within threshold
        assert avg_time < PERFORMANCE_THRESHOLD_SECONDS, \
            f"Average import time {avg_time:.2f}s exceeds threshold {PERFORMANCE_THRESHOLD_SECONDS}s"

        # At least one successful import
        assert successful_imports > 0, "No successful imports"


@pytest.mark.performance
@pytest.mark.integration
@pytest.mark.slow
def test_migusto_import_performance():
    """
    Test Migusto import performance

    Requirements:
    - Import must complete in < 3 seconds
    - Must return successful response
    - Must create recipe in database

    Note: Migusto import is typically faster than TheMealDB
    because recipes are already in German (no translation needed)
    """
    # Measure import time
    start_time = time.time()

    response = requests.post(
        f"{BASE_URL}/api/recipes/import-migusto-batch",
        json={
            'preset': 'vegetarische_pasta_familie',
            'max_recipes': 1  # Import only 1 recipe for performance test
        },
        timeout=TIMEOUT
    )

    elapsed_time = time.time() - start_time

    # Assert response is successful
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"

    data = response.json()
    assert data.get('success') is True, "Import was not successful"
    assert 'imported' in data, "No imported count in response"
    assert data.get('imported') > 0, "No recipes imported"

    # Performance assertion: Must be < 3 seconds
    print(f"✅ Migusto import completed in {elapsed_time:.2f}s")
    print(f"   Imported: {data.get('imported')} recipe(s)")
    print(f"   Total found: {data.get('total_found', 0)}")

    assert elapsed_time < PERFORMANCE_THRESHOLD_SECONDS, \
        f"Import took {elapsed_time:.2f}s (threshold: {PERFORMANCE_THRESHOLD_SECONDS}s)"


@pytest.mark.performance
@pytest.mark.integration
@pytest.mark.slow
def test_migusto_import_performance_batch():
    """
    Test Migusto batch import performance

    Import 5 recipes and ensure it completes in reasonable time
    Should be < 15 seconds for 5 recipes (< 3s average per recipe)
    """
    max_recipes = 5
    start_time = time.time()

    response = requests.post(
        f"{BASE_URL}/api/recipes/import-migusto-batch",
        json={
            'preset': 'schnelle_familiengerichte',
            'max_recipes': max_recipes
        },
        timeout=30  # Longer timeout for batch
    )

    elapsed_time = time.time() - start_time

    # Assert response is successful
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"

    data = response.json()
    assert data.get('success') is True, "Batch import was not successful"

    imported_count = data.get('imported', 0)
    if imported_count > 0:
        avg_time_per_recipe = elapsed_time / imported_count

        print(f"✅ Batch import completed in {elapsed_time:.2f}s")
        print(f"   Imported: {imported_count} recipes")
        print(f"   Average per recipe: {avg_time_per_recipe:.2f}s")

        # Each recipe should average < 3 seconds
        assert avg_time_per_recipe < PERFORMANCE_THRESHOLD_SECONDS, \
            f"Average time per recipe {avg_time_per_recipe:.2f}s exceeds threshold {PERFORMANCE_THRESHOLD_SECONDS}s"
    else:
        print(f"⚠️  No recipes imported (already exist or none found)")


@pytest.mark.integration
def test_performance_baseline_api():
    """
    Test baseline API performance (simple endpoint)

    This ensures the test environment itself is responsive
    Should complete in < 0.5 seconds
    """
    start_time = time.time()

    response = requests.get(
        f"{BASE_URL}/",
        timeout=5
    )

    elapsed_time = time.time() - start_time

    assert response.status_code == 200, "Homepage not accessible"

    print(f"✅ Baseline API response: {elapsed_time:.3f}s")

    # Baseline should be very fast
    assert elapsed_time < 0.5, f"Baseline API too slow: {elapsed_time:.3f}s"


if __name__ == '__main__':
    """Run performance tests standalone"""
    print("=" * 60)
    print("PERFORMANCE TESTS - Recipe Imports")
    print(f"Target: {BASE_URL}")
    print(f"Threshold: < {PERFORMANCE_THRESHOLD_SECONDS}s per import")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    print()

    # Run tests
    pytest.main([__file__, '-v', '-s'])
