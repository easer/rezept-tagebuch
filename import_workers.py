"""
Worker functions for background import jobs

These functions run in background threads and perform actual import work.
"""

import os
import uuid
import time
import shutil
import requests
import json
from background_jobs import update_job_progress


def themealdb_import_worker(job_id: str, params: dict, app_context):
    """
    Worker function for TheMealDB import with DeepL translation

    Params:
        - count: Number of recipes to import (default: 2)
        - user_id: User ID (optional)
    """
    from models import db, Recipe, User
    from config import UPLOAD_FOLDER

    count = params.get('count', 2)
    user_id = params.get('user_id')

    # DeepL API configuration
    DEEPL_API_KEY = os.getenv('DEEPL_API_KEY', '')
    DEEPL_API_URL = 'https://api-free.deepl.com/v2/translate'

    def translate_to_german(text):
        """Translate text to German using DeepL"""
        if not DEEPL_API_KEY or not text:
            return text

        try:
            response = requests.post(DEEPL_API_URL, data={
                'auth_key': DEEPL_API_KEY,
                'text': text,
                'target_lang': 'DE'
            }, timeout=10)

            if response.status_code == 200:
                result = response.json()
                return result['translations'][0]['text']
        except Exception as e:
            print(f"Translation error: {e}")

        return text

    with app_context:
        # Get or create user
        if not user_id:
            import_user = User.query.filter_by(email='import@seaser.local').first()
            user_id = import_user.id if import_user else 1

        imported_recipes = []
        failed_recipes = []

        update_job_progress(job_id, 0, count, 'Starting TheMealDB import...')

        for i in range(1, count + 1):
            try:
                update_job_progress(job_id, i - 1, count, f'Fetching recipe {i}/{count}...')

                # Fetch random meal
                response = requests.get('https://www.themealdb.com/api/json/v1/1/random.php', timeout=10)
                if response.status_code != 200:
                    failed_recipes.append({'error': 'Failed to fetch recipe'})
                    continue

                meal = response.json()['meals'][0]
                original_title = meal.get('strMeal', 'Unknown')
                category = meal.get('strCategory', '')
                area = meal.get('strArea', '')

                update_job_progress(job_id, i - 1, count, f'Translating "{original_title}"...')

                # Translate title
                translated_title = translate_to_german(original_title)

                # Translate instructions
                original_instructions = meal.get('strInstructions', '')
                translated_instructions = translate_to_german(original_instructions)

                # Get and translate ingredients
                ingredients_de = []
                for j in range(1, 21):
                    ingredient = meal.get(f'strIngredient{j}', '').strip()
                    measure = meal.get(f'strMeasure{j}', '').strip()
                    if ingredient:
                        ing_en = f"{measure} {ingredient}".strip()
                        ing_de = translate_to_german(ing_en)
                        ingredients_de.append(ing_de)

                # Download image
                image_filename = None
                image_url = meal.get('strMealThumb')
                if image_url:
                    try:
                        img_response = requests.get(image_url, timeout=10)
                        img_response.raise_for_status()

                        image_filename = f"{uuid.uuid4()}.jpg"
                        image_path = os.path.join(UPLOAD_FOLDER, image_filename)

                        with open(image_path, 'wb') as f:
                            f.write(img_response.content)
                    except Exception as e:
                        print(f"Image download failed: {e}")

                # Build notes with SCHRITT format
                notes = ""

                # Add instructions as steps
                if translated_instructions:
                    instruction_lines = [line.strip() for line in translated_instructions.split('\n') if line.strip()]
                    for idx, line in enumerate(instruction_lines, 1):
                        notes += f"SCHRITT {idx}\n\n{line}\n\n"

                # Add ingredients
                if ingredients_de:
                    notes += "Zutaten:\n"
                    for ing in ingredients_de:
                        notes += f"- {ing}\n"

                # Add footer
                notes += f"\n─────────────────────────\n"
                notes += f"🌍 Quelle: TheMealDB\n"
                notes += f"📖 Original: {original_title}\n"
                notes += f"🏷️ Kategorie: {category}\n"
                notes += f"🌎 Region: {area}\n"
                notes += f"🤖 Übersetzt mit DeepL"

                # Save to database
                update_job_progress(job_id, i - 1, count, f'Saving "{translated_title}"...')

                recipe = Recipe(
                    title=translated_title,
                    image=image_filename,
                    notes=notes,
                    user_id=user_id,
                    auto_imported=True
                )
                db.session.add(recipe)
                db.session.commit()

                imported_recipes.append({
                    'id': recipe.id,
                    'title': recipe.title,
                    'original_title': original_title
                })

                print(f"✓ [{i}/{count}] Imported: {translated_title}")

            except Exception as e:
                print(f"✗ [{i}/{count}] Failed: {e}")
                failed_recipes.append({'error': str(e)})
                db.session.rollback()

        update_job_progress(job_id, count, count, f'Completed! Imported {len(imported_recipes)}/{count}')

        return {
            'success': True,
            'imported': len(imported_recipes),
            'failed': len(failed_recipes),
            'recipes': imported_recipes,
            'failures': failed_recipes
        }


def migusto_import_worker(job_id: str, params: dict, app_context):
    """
    Worker function for Migusto batch import

    Params:
        - preset: Preset name (optional, default: from config)
        - filters: Custom filters (optional)
        - max_recipes: Maximum recipes to import (default: from config)
        - user_id: User ID (optional)
    """
    from models import db, Recipe, User
    from config import UPLOAD_FOLDER
    from recipe_scraper import scrape_recipe_from_url, format_recipe_for_db

    # Load Migusto config
    config_path = os.path.join(os.path.dirname(__file__), 'config/shared/migusto-import-config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)['migusto_import_config']

    # Get filters
    filters = params.get('filters')
    if not filters:
        # Use preset
        preset_name = params.get('preset', config['default_preset'])
        preset = config['presets'].get(preset_name)
        if not preset:
            raise ValueError(f'Preset {preset_name} not found')
        filters = preset['filters']

    # Build overview URL
    base_url = config['base_url']
    overview_path = config['overview_path']
    filter_string = '-'.join(filters)
    overview_url = f"{base_url}{overview_path}/{filter_string}"

    update_job_progress(job_id, 0, 0, f'Fetching recipe list from Migusto...')

    # Fetch overview page
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(overview_url, headers=headers, timeout=15)
    response.raise_for_status()

    # Extract recipe links
    import re
    pattern = r'href="(/de/rezepte/[a-z0-9-]+)"'
    matches = re.findall(pattern, response.text)
    unique_links = list(set(matches))

    max_recipes = params.get('max_recipes', config.get('max_recipes_per_import', 50))
    recipe_urls = [f"{base_url}{link}" for link in unique_links[:max_recipes]]

    total_recipes = len(recipe_urls)
    update_job_progress(job_id, 0, total_recipes, f'Found {total_recipes} recipes')

    with app_context:
        # Get user
        user_id = params.get('user_id')
        if not user_id:
            import_user = User.query.filter_by(email='import@seaser.local').first()
            user_id = import_user.id if import_user else 1

        imported_recipes = []
        failed_recipes = []
        skipped_recipes = []
        delay_ms = config.get('delay_between_imports_ms', 2000)

        for i, recipe_url in enumerate(recipe_urls, 1):
            try:
                recipe_slug = recipe_url.split('/')[-1]

                # Check if already imported
                existing = Recipe.query.filter_by(title=recipe_slug).first()
                if existing:
                    update_job_progress(job_id, i, total_recipes, f'Skipped (exists): {recipe_slug}')
                    skipped_recipes.append({'url': recipe_url, 'reason': 'already_exists'})
                    continue

                update_job_progress(job_id, i, total_recipes, f'Importing: {recipe_slug}')

                # Scrape recipe
                scraped_data = scrape_recipe_from_url(recipe_url)

                if not scraped_data.get('title'):
                    failed_recipes.append({'url': recipe_url, 'error': 'no_title'})
                    continue

                # Format for database
                formatted_data = format_recipe_for_db(scraped_data, source_url=recipe_url)

                # Download image
                image_filename = None
                image_url = formatted_data.get('image')
                if image_url and image_url.startswith('http'):
                    try:
                        img_response = requests.get(image_url, timeout=10, stream=True)
                        img_response.raise_for_status()
                        ext = image_url.split('.')[-1].split('?')[0][:4]
                        if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                            ext = 'jpg'
                        image_filename = f"{uuid.uuid4()}.{ext}"
                        image_path = os.path.join(UPLOAD_FOLDER, image_filename)
                        with open(image_path, 'wb') as f:
                            shutil.copyfileobj(img_response.raw, f)
                    except:
                        pass

                # Save to database
                recipe = Recipe(
                    title=formatted_data['title'],
                    image=image_filename,
                    notes=formatted_data['notes'],
                    duration=formatted_data.get('duration'),
                    rating=formatted_data.get('rating'),
                    user_id=user_id,
                    auto_imported=True
                )
                db.session.add(recipe)
                db.session.commit()

                imported_recipes.append({
                    'id': recipe.id,
                    'title': recipe.title,
                    'url': recipe_url
                })

                # Delay between requests
                if i < len(recipe_urls):
                    time.sleep(delay_ms / 1000.0)

            except Exception as e:
                print(f"❌ [{i}/{total_recipes}] Failed: {recipe_url} - {e}")
                failed_recipes.append({'url': recipe_url, 'error': str(e)})
                db.session.rollback()

        update_job_progress(job_id, total_recipes, total_recipes, f'Completed! Imported {len(imported_recipes)}/{total_recipes}')

        return {
            'success': True,
            'imported': len(imported_recipes),
            'failed': len(failed_recipes),
            'skipped': len(skipped_recipes),
            'recipes': imported_recipes,
            'failures': failed_recipes,
            'skips': skipped_recipes
        }
