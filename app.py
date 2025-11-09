#!/usr/bin/env python3
"""
Natalies Rezept-Tagebuch - Backend API
Python Flask Server with SQLAlchemy ORM (PostgreSQL/SQLite)
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from datetime import datetime, timedelta, date
import uuid
import requests
import shutil
import json
import re
import subprocess

# Import SQLAlchemy models and config
from models import db, User, Recipe, Todo, DiaryEntry
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, SQLALCHEMY_ENGINE_OPTIONS, UPLOAD_FOLDER, TESTING_MODE

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = SQLALCHEMY_ENGINE_OPTIONS

# Initialize SQLAlchemy
db.init_app(app)

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if TESTING_MODE:
    print("🧪 TESTING MODE: Using test database")

# Database initialization
def init_db():
    """Initialize database tables and seed initial data"""
    with app.app_context():
        # Create all tables
        db.create_all()

        # Seed initial users if none exist
        if User.query.count() == 0:
            # Create Natalie (default user)
            natalie = User(
                email='natalie@seaser.local',
                name='Natalie',
                avatar_color='#FFB6C1'
            )
            db.session.add(natalie)

            # Create Import user (for TheMealDB recipes)
            import_user = User(
                email='import@seaser.local',
                name='Rezept Import',
                avatar_color='#64C8FF'
            )
            db.session.add(import_user)

            db.session.commit()
            print("✓ Created initial users")

        # Seed initial todos if none exist
        if Todo.query.count() == 0:
            # Get Natalie's user ID (should be 1)
            natalie = User.query.filter_by(email='natalie@seaser.local').first()
            if natalie:
                initial_todos = [
                    Todo(text='Rezepte optimieren (kein gekocht am, etc.)', priority=1, completed=False, user_id=natalie.id),
                    Todo(text='Abbrechen Button raus, aus neu und bearbeiten', priority=1, completed=True, user_id=natalie.id),
                    Todo(text='Katalog nur Rezepte, noch kein Tagebuch als Ziel', priority=2, completed=False, user_id=natalie.id),
                    Todo(text='Profil anlegen', priority=2, completed=False, user_id=natalie.id),
                    Todo(text='Rezept vorhanden Mechanismus', priority=2, completed=False, user_id=natalie.id),
                    Todo(text='Tagebuch aus Rezepten erstellen', priority=3, completed=False, user_id=natalie.id),
                ]
                for todo in initial_todos:
                    db.session.add(todo)
                db.session.commit()
                print("✓ Created initial todos")

# API Endpoints

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/recipe-format-config.json')
def recipe_format_config():
    return send_from_directory('.', 'recipe-format-config.json')

# ============================================================================
# User API Endpoints
# ============================================================================

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users (for profile selection)"""
    try:
        users = User.query.order_by(User.created_at.asc()).all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()

        # Validation
        if not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400

        # Check if email already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'Email already exists'}), 409

        # Create new user
        user = User(
            email=data['email'],
            name=data['name'],
            avatar_color=data.get('avatar_color', '#FFB6C1')
        )
        db.session.add(user)
        db.session.commit()

        return jsonify(user.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a single user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user (only name and avatar_color, NOT email!)"""
    try:
        data = request.get_json()

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Only name and avatar_color can be changed
        if 'name' in data:
            user.name = data['name']
        if 'avatar_color' in data:
            user.avatar_color = data['avatar_color']

        db.session.commit()
        return jsonify(user.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete user (optional, for later)"""
    try:
        # Natalie (user_id=1) cannot be deleted
        if user_id == 1:
            return jsonify({'error': 'Cannot delete default user'}), 403

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Check if user has recipes
        recipe_count = Recipe.query.filter_by(user_id=user_id).count()
        if recipe_count > 0:
            return jsonify({'error': f'Cannot delete user with {recipe_count} recipes'}), 409

        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Recipe API Endpoints
# ============================================================================

@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    """Get all recipes (including user info)"""
    try:
        # Optional: Search by title or notes
        search = request.args.get('search')

        query = Recipe.query

        if search:
            search_term = f'%{search}%'
            query = query.filter(
                db.or_(
                    Recipe.title.ilike(search_term),
                    Recipe.notes.ilike(search_term)
                )
            )

        recipes = query.order_by(Recipe.created_at.desc()).all()
        return jsonify([recipe.to_dict() for recipe in recipes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recipes', methods=['POST'])
def create_recipe():
    """Create a new recipe (user_id required)"""
    try:
        data = request.json

        # user_id is required (sent from frontend)
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400

        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Create new recipe
        recipe = Recipe(
            title=data.get('title'),
            image=data.get('image'),
            notes=data.get('notes'),
            duration=data.get('duration'),
            rating=data.get('rating'),
            user_id=user_id
        )
        db.session.add(recipe)
        db.session.commit()

        return jsonify(recipe.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """Get a single recipe"""
    try:
        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found'}), 404
        return jsonify(recipe.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    """Update recipe (owner only!)"""
    try:
        data = request.json

        # user_id is required (current user)
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400

        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found'}), 404

        # System recipes cannot be edited
        if recipe.is_system:
            return jsonify({'error': 'Cannot edit system recipe'}), 403

        # Only owner can edit
        if recipe.user_id != user_id:
            return jsonify({'error': 'Permission denied. You can only edit your own recipes.'}), 403

        # Update recipe
        recipe.title = data.get('title')
        recipe.image = data.get('image')
        recipe.notes = data.get('notes')
        recipe.duration = data.get('duration')
        recipe.rating = data.get('rating')
        recipe.updated_at = datetime.utcnow()

        db.session.commit()
        return jsonify(recipe.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    """Delete recipe (owner only!)"""
    try:
        # user_id from query parameter or header
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400

        user_id = int(user_id)

        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found'}), 404

        # System recipes cannot be deleted
        if recipe.is_system:
            return jsonify({'error': 'Cannot delete system recipe'}), 403

        # Only owner can delete
        if recipe.user_id != user_id:
            return jsonify({'error': 'Permission denied. You can only delete your own recipes.'}), 403

        # Delete image if exists
        if recipe.image:
            image_path = os.path.join(UPLOAD_FOLDER, recipe.image)
            if os.path.exists(image_path):
                os.remove(image_path)

        db.session.delete(recipe)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Upload an image"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Generate unique filename
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    file.save(filepath)

    return jsonify({'filename': filename})

@app.route('/api/uploads/<filename>')
def get_image(filename):
    """Get an image"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics"""
    try:
        total = Recipe.query.count()
        with_images = Recipe.query.filter(Recipe.image.isnot(None)).count()

        return jsonify({
            'total_recipes': total,
            'recipes_with_images': with_images
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# TODO API Endpoints
# ============================================================================

@app.route('/api/todos', methods=['GET'])
def get_todos():
    """Get all TODOs, grouped by priority"""
    try:
        todos = Todo.query.order_by(Todo.priority.asc(), Todo.id.asc()).all()
        return jsonify([todo.to_dict() for todo in todos])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/todos', methods=['POST'])
def create_todo():
    """Create a new TODO"""
    try:
        data = request.json
        todo = Todo(
            text=data.get('text'),
            priority=data.get('priority', 2),
            completed=data.get('completed', False)
        )
        db.session.add(todo)
        db.session.commit()
        return jsonify(todo.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    """Get a single TODO"""
    try:
        todo = Todo.query.get(todo_id)
        if not todo:
            return jsonify({'error': 'TODO not found'}), 404
        return jsonify(todo.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    """Update TODO"""
    try:
        data = request.json
        todo = Todo.query.get(todo_id)
        if not todo:
            return jsonify({'error': 'TODO not found'}), 404

        todo.text = data.get('text')
        todo.priority = data.get('priority')
        todo.completed = data.get('completed')
        todo.updated_at = datetime.utcnow()

        db.session.commit()
        return jsonify(todo.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    """Delete TODO"""
    try:
        todo = Todo.query.get(todo_id)
        if not todo:
            return jsonify({'error': 'TODO not found'}), 404

        db.session.delete(todo)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Diary API Endpoints
# ============================================================================

@app.route('/api/diary', methods=['GET'])
def get_diary_entries():
    """Get diary entries for current user"""
    try:
        # User ID from query parameter
        user_id = request.args.get('user_id', type=int)
        search = request.args.get('search')

        query = DiaryEntry.query

        # Filter by user_id (required)
        if user_id:
            query = query.filter_by(user_id=user_id)

        if search:
            search_term = f'%{search}%'
            query = query.join(Recipe, DiaryEntry.recipe_id == Recipe.id, isouter=True)
            query = query.filter(
                db.or_(
                    DiaryEntry.dish_name.ilike(search_term),
                    DiaryEntry.notes.ilike(search_term),
                    Recipe.title.ilike(search_term)
                )
            )

        entries = query.order_by(DiaryEntry.date.desc(), DiaryEntry.created_at.desc()).all()

        # Convert to dict and parse images JSON
        result = []
        for entry in entries:
            entry_dict = entry.to_dict()

            # Add recipe info
            if entry.recipe:
                entry_dict['recipe_title'] = entry.recipe.title
                entry_dict['recipe_image'] = entry.recipe.image
            else:
                entry_dict['recipe_title'] = None
                entry_dict['recipe_image'] = None

            # Parse images JSON
            if entry_dict['images']:
                try:
                    entry_dict['images'] = json.loads(entry_dict['images'])
                except:
                    entry_dict['images'] = []
            else:
                entry_dict['images'] = []

            result.append(entry_dict)

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/diary', methods=['POST'])
def create_diary_entry():
    """Create a new diary entry"""
    try:
        data = request.json

        # Images as JSON
        images_json = json.dumps(data.get('images', []))

        entry = DiaryEntry(
            recipe_id=data.get('recipe_id'),
            user_id=data.get('user_id'),
            date=datetime.fromisoformat(data.get('date')).date() if data.get('date') else None,
            notes=data.get('notes'),
            images=images_json,
            dish_name=data.get('dish_name')
        )
        db.session.add(entry)
        db.session.commit()

        # Return entry with recipe data
        entry_dict = entry.to_dict()
        if entry.recipe:
            entry_dict['recipe_title'] = entry.recipe.title
            entry_dict['recipe_image'] = entry.recipe.image
        else:
            entry_dict['recipe_title'] = None
            entry_dict['recipe_image'] = None

        # Parse images JSON
        if entry_dict['images']:
            try:
                entry_dict['images'] = json.loads(entry_dict['images'])
            except:
                entry_dict['images'] = []
        else:
            entry_dict['images'] = []

        return jsonify(entry_dict), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/diary/<int:entry_id>', methods=['GET'])
def get_diary_entry(entry_id):
    """Get a single diary entry"""
    try:
        entry = DiaryEntry.query.get(entry_id)
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404

        entry_dict = entry.to_dict()

        # Add recipe info
        if entry.recipe:
            entry_dict['recipe_title'] = entry.recipe.title
            entry_dict['recipe_image'] = entry.recipe.image
        else:
            entry_dict['recipe_title'] = None
            entry_dict['recipe_image'] = None

        # Parse images JSON
        if entry_dict['images']:
            try:
                entry_dict['images'] = json.loads(entry_dict['images'])
            except:
                entry_dict['images'] = []
        else:
            entry_dict['images'] = []

        return jsonify(entry_dict)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/diary/<int:entry_id>', methods=['PUT'])
def update_diary_entry(entry_id):
    """Update diary entry"""
    try:
        data = request.json

        entry = DiaryEntry.query.get(entry_id)
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404

        # Images as JSON
        images_json = json.dumps(data.get('images', []))

        entry.recipe_id = data.get('recipe_id')
        entry.date = datetime.fromisoformat(data.get('date')).date() if data.get('date') else None
        entry.notes = data.get('notes')
        entry.images = images_json
        entry.dish_name = data.get('dish_name')
        entry.updated_at = datetime.utcnow()

        db.session.commit()

        # Return updated entry with recipe data
        entry_dict = entry.to_dict()
        if entry.recipe:
            entry_dict['recipe_title'] = entry.recipe.title
            entry_dict['recipe_image'] = entry.recipe.image
        else:
            entry_dict['recipe_title'] = None
            entry_dict['recipe_image'] = None

        # Parse images JSON
        if entry_dict['images']:
            try:
                entry_dict['images'] = json.loads(entry_dict['images'])
            except:
                entry_dict['images'] = []
        else:
            entry_dict['images'] = []

        return jsonify(entry_dict)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/diary/<int:entry_id>', methods=['DELETE'])
def delete_diary_entry(entry_id):
    """Delete diary entry"""
    try:
        entry = DiaryEntry.query.get(entry_id)
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404

        # Delete images if exist
        if entry.images:
            try:
                images = json.loads(entry.images)
                for image in images:
                    image_path = os.path.join(UPLOAD_FOLDER, image)
                    if os.path.exists(image_path):
                        os.remove(image_path)
            except:
                pass

        db.session.delete(entry)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Utility Endpoints
# ============================================================================

@app.route('/api/version')
def get_version():
    """Get current app version (from Git tag or env var)"""
    version = os.environ.get('APP_VERSION', None)

    # If no ENV var, try to read from Git
    if not version:
        try:
            result = subprocess.run(
                ['git', 'describe', '--tags', '--exact-match'],
                cwd='/app',
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                version = result.stdout.strip()
        except:
            pass

    # Fallback
    if not version:
        version = "unknown"

    return jsonify({'version': version})

@app.route('/api/search')
def global_search():
    """Global search across recipes, diary and TODOs"""
    try:
        query_text = request.args.get('q', '').strip()

        if not query_text or len(query_text) < 2:
            return jsonify({
                'recipes': [],
                'diary_entries': [],
                'todos': []
            })

        search_pattern = f'%{query_text}%'

        # Search in recipes
        recipes_results = Recipe.query.filter(
            db.or_(
                Recipe.title.ilike(search_pattern),
                Recipe.notes.ilike(search_pattern)
            )
        ).order_by(
            db.case(
                (Recipe.title.ilike(f'{query_text}%'), 1),
                else_=2
            ),
            Recipe.title
        ).limit(20).all()

        recipes = []
        for recipe in recipes_results:
            # Snippet from notes (first 100 chars)
            notes = recipe.notes or ''
            snippet = notes[:100] + '...' if len(notes) > 100 else notes

            recipes.append({
                'id': recipe.id,
                'title': recipe.title,
                'snippet': snippet if notes else None,
                'image': recipe.image,
                'rating': recipe.rating,
                'duration': recipe.duration,
                'type': 'recipe'
            })

        # Search in diary entries
        diary_results = DiaryEntry.query.join(Recipe, DiaryEntry.recipe_id == Recipe.id, isouter=True).filter(
            db.or_(
                DiaryEntry.notes.ilike(search_pattern),
                DiaryEntry.dish_name.ilike(search_pattern),
                Recipe.title.ilike(search_pattern)
            )
        ).order_by(DiaryEntry.created_at.desc()).limit(20).all()

        diary_entries = []
        for entry in diary_results:
            # Snippet from notes (first 100 chars)
            notes = entry.notes or ''
            snippet = notes[:100] + '...' if len(notes) > 100 else notes

            # Display title: dish_name if available, else recipe_title
            display_title = entry.dish_name or (entry.recipe.title if entry.recipe else None) or 'Ohne Titel'

            diary_entries.append({
                'id': entry.id,
                'snippet': snippet,
                'recipe_title': display_title,
                'recipe_image': entry.recipe.image if entry.recipe else None,
                'created_at': entry.created_at.isoformat() if entry.created_at else None,
                'type': 'diary'
            })

        # Search in TODOs
        todos_results = Todo.query.filter(
            Todo.text.ilike(search_pattern)
        ).order_by(
            db.case(
                (Todo.completed == True, 2),
                else_=1
            ),
            Todo.priority.desc()
        ).limit(20).all()

        todos = []
        for todo in todos_results:
            todos.append({
                'id': todo.id,
                'text': todo.text,
                'priority': todo.priority,
                'completed': todo.completed,
                'type': 'todo'
            })

        return jsonify({
            'recipes': recipes,
            'diary_entries': diary_entries,
            'todos': todos,
            'query': query_text
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# TheMealDB Daily Import
# ============================================================================

THEMEALDB_API = 'https://www.themealdb.com/api/json/v1/1'
THEMEALDB_CONFIG_FILE = 'themealdb-config.json'
DEEPL_API_KEY = os.getenv('DEEPL_API_KEY', '')
DEEPL_API_URL = 'https://api-free.deepl.com/v2/translate'

def load_themealdb_config():
    """Load TheMealDB import configuration"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), THEMEALDB_CONFIG_FILE)
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config['themealdb_import_config']
    except Exception as e:
        print(f"Warning: Could not load TheMealDB config: {e}")
        # Return default config
        return {
            'api_base_url': THEMEALDB_API,
            'default_strategy': 'random',
            'strategies': {
                'random': {
                    'endpoint': 'random.php',
                    'requires_parameter': False
                }
            }
        }

def fetch_recipe_from_themealdb(strategy='random', value=None):
    """
    Fetch recipe from TheMealDB using specified strategy

    Args:
        strategy: Import strategy (random, by_category, by_area, by_ingredient, etc.)
        value: Value for the strategy filter (e.g., "Italian" for by_area)

    Returns:
        dict: Recipe data from TheMealDB or None if error
    """
    config = load_themealdb_config()
    api_base = config.get('api_base_url', THEMEALDB_API)

    # Get strategy config
    strategies = config.get('strategies', {})
    strategy_config = strategies.get(strategy)

    if not strategy_config:
        print(f"Warning: Unknown strategy '{strategy}', falling back to random")
        strategy = 'random'
        strategy_config = strategies.get('random', {
            'endpoint': 'random.php',
            'requires_parameter': False
        })

    endpoint = strategy_config.get('endpoint')
    requires_param = strategy_config.get('requires_parameter', False)

    # Build URL
    url = f"{api_base}/{endpoint}"

    if requires_param:
        param_key = strategy_config.get('parameter_key')

        # If no value provided, use default or random from available values
        if not value:
            default_values = strategy_config.get('default_values', [])
            available_values = strategy_config.get('available_values', [])

            if default_values:
                import random
                value = random.choice(default_values)
            elif available_values:
                import random
                value = random.choice(available_values)
            else:
                print(f"Error: Strategy '{strategy}' requires a value but none provided")
                return None

        url = f"{url}?{param_key}={value}"
        print(f"🔍 TheMealDB Import: strategy={strategy}, {param_key}={value}")
    else:
        print(f"🔍 TheMealDB Import: strategy={strategy}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get('meals'):
            print(f"No recipes found for {strategy}={value}")
            return None

        # For filter endpoints, we get a list - pick random one and fetch full details
        meals = data['meals']

        # If we got abbreviated results (from filter.php), fetch full recipe details
        if 'strInstructions' not in meals[0]:
            import random
            selected_meal = random.choice(meals)
            meal_id = selected_meal['idMeal']

            print(f"📖 Fetching full recipe details for ID {meal_id}")
            detail_url = f"{api_base}/lookup.php?i={meal_id}"
            detail_response = requests.get(detail_url, timeout=10)
            detail_response.raise_for_status()
            detail_data = detail_response.json()

            if detail_data.get('meals'):
                return detail_data['meals'][0]
            else:
                return None
        else:
            # Already have full recipe (from random.php or search.php)
            return meals[0]

    except Exception as e:
        print(f"Error fetching from TheMealDB: {e}")
        return None

def translate_to_german(text):
    """Translate text from English to German using DeepL API"""
    if not DEEPL_API_KEY:
        print("Warning: No DeepL API key configured, skipping translation")
        return text

    if not text or text.strip() == '':
        return text

    try:
        response = requests.post(DEEPL_API_URL, data={
            'auth_key': DEEPL_API_KEY,
            'text': text,
            'source_lang': 'EN',
            'target_lang': 'DE'
        }, timeout=10)

        response.raise_for_status()
        result = response.json()

        if 'translations' in result and len(result['translations']) > 0:
            return result['translations'][0]['text']
        else:
            print(f"DeepL translation failed: {result}")
            return text

    except Exception as e:
        print(f"DeepL translation error: {e}")
        return text  # Fallback to original text

@app.route('/api/recipes/daily-import', methods=['POST'])
def daily_recipe_import():
    """
    Import a recipe from TheMealDB with configurable strategy

    Query Parameters:
        strategy (str): Import strategy (random, by_category, by_area, by_ingredient, etc.)
        value (str): Value for the strategy (e.g., "Italian" for by_area)

    Examples:
        POST /api/recipes/daily-import
        POST /api/recipes/daily-import?strategy=random
        POST /api/recipes/daily-import?strategy=by_category&value=Vegetarian
        POST /api/recipes/daily-import?strategy=by_area&value=Italian
        POST /api/recipes/daily-import?strategy=by_ingredient&value=chicken
    """
    try:
        # Get import strategy from query parameters
        config = load_themealdb_config()
        strategy = request.args.get('strategy', config.get('default_strategy', 'random'))
        value = request.args.get('value', None)

        # 1. Fetch recipe from TheMealDB using configured strategy
        meal = fetch_recipe_from_themealdb(strategy=strategy, value=value)

        if not meal:
            return jsonify({'error': 'No recipe found for the given criteria'}), 404

        # 1a. Validate category: Only allow meat-free recipes
        category = meal.get('strCategory', '')
        MEAT_FREE_CATEGORIES = ['Vegetarian', 'Vegan', 'Dessert', 'Breakfast', 'Pasta', 'Side', 'Starter', 'Miscellaneous']
        MEAT_CATEGORIES = ['Beef', 'Chicken', 'Lamb', 'Pork', 'Goat', 'Seafood']

        if category in MEAT_CATEGORIES:
            print(f"⚠️ Import rejected: Category '{category}' contains meat/seafood")
            return jsonify({
                'error': f'Recipe category "{category}" contains meat/seafood. Only vegetarian recipes allowed.',
                'rejected_category': category,
                'rejected_title': meal.get('strMeal')
            }), 400

        # 2. Download image
        image_url = meal.get('strMealThumb')
        image_filename = None

        if image_url:
            try:
                img_response = requests.get(image_url, timeout=10, stream=True)
                img_response.raise_for_status()

                # Generate unique filename
                image_filename = f"{uuid.uuid4()}.jpg"
                image_path = os.path.join(UPLOAD_FOLDER, image_filename)

                # Save image
                with open(image_path, 'wb') as f:
                    shutil.copyfileobj(img_response.raw, f)
            except Exception as e:
                print(f"Image download failed: {e}")
                image_filename = None

        # 3. Translate title and instructions to German
        original_title = meal.get('strMeal', 'Imported Recipe')
        translated_title = translate_to_german(original_title)

        original_instructions = meal.get('strInstructions', '')
        translated_instructions = translate_to_german(original_instructions)

        # 3a. Format instructions into SCHRITT structure for parser
        instruction_text = translated_instructions.replace('\r\n', '\n').strip()

        # Check if already formatted (contains "SCHRITT X" or "Step X")
        has_steps = bool(re.search(r'(SCHRITT\s+\d+|Step\s+\d+)', instruction_text, re.IGNORECASE))

        if has_steps:
            # Already formatted - just use as-is
            formatted_instructions = instruction_text
        else:
            # Not formatted - split by newlines and add SCHRITT markers
            instruction_lines = instruction_text.split('\n')
            formatted_steps = []
            step_num = 1
            for line in instruction_lines:
                line = line.strip()
                if line:  # Skip empty lines
                    formatted_steps.append(f"SCHRITT {step_num}\n\n{line}")
                    step_num += 1
            formatted_instructions = "\n\n".join(formatted_steps)

        # 4. Parse and translate ingredients
        ingredients = []
        ingredients_en = []
        for i in range(1, 21):
            ingredient = meal.get(f'strIngredient{i}', '').strip()
            measure = meal.get(f'strMeasure{i}', '').strip()
            if ingredient:
                ing_en = f"{measure} {ingredient}".strip()
                ingredients_en.append(ing_en)
                # Translate ingredient
                ing_de = translate_to_german(ing_en)
                ingredients.append(ing_de)

        # Build notes with structured SCHRITT format
        notes = formatted_instructions + "\n\n"
        if ingredients:
            notes += "Zutaten:\n" + "\n".join(f"- {ing}" for ing in ingredients)

        # Add source info (bilingual)
        area = meal.get('strArea', 'N/A')
        notes += f"\n\n─────────────────────────"
        notes += f"\n🌍 Quelle: TheMealDB"
        notes += f"\n📖 Original: {original_title}"
        notes += f"\n🏷️ Kategorie: {category}"
        notes += f"\n🌎 Region: {area}"
        notes += f"\n🤖 Übersetzt mit DeepL"

        # 5. Save to database
        # Get import user ID
        import_user = User.query.filter_by(email='import@seaser.local').first()
        import_user_id = import_user.id if import_user else 1

        recipe = Recipe(
            title=translated_title,
            image=image_filename,
            notes=notes,
            user_id=import_user_id,
            auto_imported=True
            # erstellt_am wird automatisch gesetzt durch DB-Default (CURRENT_TIMESTAMP)
        )
        db.session.add(recipe)
        db.session.commit()

        return jsonify({
            'success': True,
            'recipe_id': recipe.id,
            'title': meal.get('strMeal'),
            'title_de': translated_title,
            'source': 'TheMealDB',
            'strategy': strategy,
            'filter_value': value,
            'category': category,
            'area': area,
            'erstellt_am': recipe.erstellt_am.isoformat() if recipe.erstellt_am else None
        })

    except Exception as e:
        db.session.rollback()
        print(f"Daily import failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/recipes/cleanup-old-imports', methods=['POST'])
def cleanup_old_imports():
    """Delete auto-imported recipes older than 7 days without diary entry"""
    try:
        # Find old auto-imported recipes without diary entries
        cutoff_date = (datetime.now() - timedelta(days=7)).date()

        old_recipes = Recipe.query.filter(
            Recipe.auto_imported == True,
            Recipe.erstellt_am < cutoff_date
        ).filter(
            ~Recipe.diary_entries.any()
        ).all()

        deleted_count = 0

        for recipe in old_recipes:
            # Delete image file if exists
            if recipe.image:
                image_path = os.path.join(UPLOAD_FOLDER, recipe.image)
                if os.path.exists(image_path):
                    os.remove(image_path)

            # Delete recipe
            db.session.delete(recipe)
            deleted_count += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        })

    except Exception as e:
        db.session.rollback()
        print(f"Cleanup failed: {e}")
        return jsonify({'error': str(e)}), 500

# Server start
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=80, debug=False)
