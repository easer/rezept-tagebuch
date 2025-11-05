#!/usr/bin/env python3
"""
Natalies Rezept-Tagebuch - Backend API
Python Flask Server mit SQLite Datenbank
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
import uuid

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Konfiguration
DATABASE = '/data/rezepte.db'
UPLOAD_FOLDER = '/data/uploads'
os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Datenbank initialisieren
def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Users Tabelle erstellen
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            avatar_color TEXT DEFAULT '#FFB6C1',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migration: Natalie als ersten User erstellen (nur wenn noch keine User existieren)
    c.execute('SELECT COUNT(*) as count FROM users')
    if c.fetchone()['count'] == 0:
        c.execute('''
            INSERT INTO users (email, name, avatar_color)
            VALUES ('natalie@seaser.local', 'Natalie', '#FFB6C1')
        ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            image TEXT,
            notes TEXT,
            duration REAL,
            rating INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migration: Add duration and rating columns if they don't exist
    c.execute("PRAGMA table_info(recipes)")
    columns = [column[1] for column in c.fetchall()]
    if 'duration' not in columns:
        c.execute('ALTER TABLE recipes ADD COLUMN duration REAL')
    if 'rating' not in columns:
        c.execute('ALTER TABLE recipes ADD COLUMN rating INTEGER')

    # Migration: Add user_id and is_system columns to recipes
    if 'user_id' not in columns:
        c.execute('ALTER TABLE recipes ADD COLUMN user_id INTEGER REFERENCES users(id)')
        # Alle existierenden Rezepte Natalie (user_id=1) zuordnen
        c.execute('UPDATE recipes SET user_id = 1 WHERE user_id IS NULL')
    if 'is_system' not in columns:
        c.execute('ALTER TABLE recipes ADD COLUMN is_system BOOLEAN DEFAULT 0')

    # TODOs Tabelle erstellen
    c.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            priority INTEGER NOT NULL,
            completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migration: Add user_id column to todos
    c.execute("PRAGMA table_info(todos)")
    todo_columns = [column[1] for column in c.fetchall()]
    if 'user_id' not in todo_columns:
        c.execute('ALTER TABLE todos ADD COLUMN user_id INTEGER REFERENCES users(id)')
        # Alle existierenden TODOs Natalie (user_id=1) zuordnen
        c.execute('UPDATE todos SET user_id = 1 WHERE user_id IS NULL')

    # Initiale TODOs einfügen (nur wenn Tabelle leer ist)
    c.execute('SELECT COUNT(*) as count FROM todos')
    if c.fetchone()['count'] == 0:
        initial_todos = [
            ('Rezepte optimieren (kein gekocht am, etc.)', 1, 0),
            ('Abbrechen Button raus, aus neu und bearbeiten', 1, 1),  # Bereits erledigt
            ('Katalog nur Rezepte, noch kein Tagebuch als Ziel', 2, 0),
            ('Profil anlegen', 2, 0),
            ('Rezept vorhanden Mechanismus', 2, 0),
            ('Tagebuch aus Rezepten erstellen', 3, 0),
        ]
        c.executemany('INSERT INTO todos (text, priority, completed) VALUES (?, ?, ?)', initial_todos)
        # Initial TODOs auch Natalie zuordnen
        c.execute('UPDATE todos SET user_id = 1 WHERE user_id IS NULL')

    # Tagebuch-Einträge Tabelle erstellen
    c.execute('''
        CREATE TABLE IF NOT EXISTS diary_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            date DATE NOT NULL,
            notes TEXT,
            images TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE SET NULL
        )
    ''')

    # Migration: Add dish_name column if it doesn't exist
    c.execute("PRAGMA table_info(diary_entries)")
    diary_columns = [column[1] for column in c.fetchall()]
    if 'dish_name' not in diary_columns:
        c.execute('ALTER TABLE diary_entries ADD COLUMN dish_name TEXT')

    conn.commit()
    conn.close()

# Datenbankverbindung
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# API Endpoints

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# ============================================================================
# User API Endpoints
# ============================================================================

@app.route('/api/users', methods=['GET'])
def get_users():
    """Alle User abrufen (für Profil-Auswahl)"""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id, email, name, avatar_color, created_at FROM users ORDER BY created_at ASC')
        users = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify(users), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    """Neuen User erstellen"""
    try:
        data = request.get_json()

        # Validierung
        if not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400

        email = data['email']
        name = data['name']
        avatar_color = data.get('avatar_color', '#FFB6C1')

        conn = get_db()
        c = conn.cursor()

        # Prüfen ob Email bereits existiert
        c.execute('SELECT id FROM users WHERE email = ?', (email,))
        if c.fetchone():
            conn.close()
            return jsonify({'error': 'Email already exists'}), 409

        c.execute('''
            INSERT INTO users (email, name, avatar_color)
            VALUES (?, ?, ?)
        ''', (email, name, avatar_color))

        user_id = c.lastrowid
        conn.commit()

        # Neuen User zurückgeben
        c.execute('SELECT id, email, name, avatar_color, created_at FROM users WHERE id = ?', (user_id,))
        user = dict(c.fetchone())
        conn.close()

        return jsonify(user), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Einzelnen User abrufen"""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id, email, name, avatar_color, created_at FROM users WHERE id = ?', (user_id,))
        user = c.fetchone()
        conn.close()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify(dict(user)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """User bearbeiten (nur Name und Avatar-Farbe, NICHT Email!)"""
    try:
        data = request.get_json()

        conn = get_db()
        c = conn.cursor()

        # Prüfen ob User existiert
        c.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        if not c.fetchone():
            conn.close()
            return jsonify({'error': 'User not found'}), 404

        # Nur Name und avatar_color können geändert werden
        if 'name' in data:
            c.execute('UPDATE users SET name = ? WHERE id = ?', (data['name'], user_id))
        if 'avatar_color' in data:
            c.execute('UPDATE users SET avatar_color = ? WHERE id = ?', (data['avatar_color'], user_id))

        conn.commit()

        # Aktualisierten User zurückgeben
        c.execute('SELECT id, email, name, avatar_color, created_at FROM users WHERE id = ?', (user_id,))
        user = dict(c.fetchone())
        conn.close()

        return jsonify(user), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """User löschen (optional, für später)"""
    try:
        # Natalie (user_id=1) kann nicht gelöscht werden
        if user_id == 1:
            return jsonify({'error': 'Cannot delete default user'}), 403

        conn = get_db()
        c = conn.cursor()

        # Prüfen ob User existiert
        c.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        if not c.fetchone():
            conn.close()
            return jsonify({'error': 'User not found'}), 404

        # Prüfen ob User Rezepte hat
        c.execute('SELECT COUNT(*) as count FROM recipes WHERE user_id = ?', (user_id,))
        recipe_count = c.fetchone()['count']
        if recipe_count > 0:
            conn.close()
            return jsonify({'error': f'Cannot delete user with {recipe_count} recipes'}), 409

        c.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()

        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Recipe API Endpoints
# ============================================================================

@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    """Alle Rezepte abrufen (inkl. User-Info)"""
    conn = get_db()
    c = conn.cursor()

    # Optional: Suche nach Titel oder Notizen
    search = request.args.get('search')

    # JOIN mit users-Tabelle um User-Info zu bekommen
    query = '''
        SELECT
            recipes.*,
            users.name as user_name,
            users.email as user_email,
            users.avatar_color as user_avatar_color
        FROM recipes
        LEFT JOIN users ON recipes.user_id = users.id
        WHERE 1=1
    '''
    params = []

    if search:
        query += ' AND (recipes.title LIKE ? OR recipes.notes LIKE ?)'
        search_term = f'%{search}%'
        params.extend([search_term, search_term])

    query += ' ORDER BY recipes.created_at DESC'

    c.execute(query, params)
    recipes = [dict(row) for row in c.fetchall()]
    conn.close()

    return jsonify(recipes)

@app.route('/api/recipes', methods=['POST'])
def create_recipe():
    """Neues Rezept erstellen (user_id required)"""
    try:
        data = request.json

        # user_id ist required (wird vom Frontend mitgeschickt)
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400

        conn = get_db()
        c = conn.cursor()

        # Prüfen ob User existiert
        c.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        if not c.fetchone():
            conn.close()
            return jsonify({'error': 'User not found'}), 404

        c.execute('''
            INSERT INTO recipes (title, image, notes, duration, rating, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.get('title'),
            data.get('image'),
            data.get('notes'),
            data.get('duration'),
            data.get('rating'),
            user_id
        ))

        conn.commit()
        recipe_id = c.lastrowid

        # Rezept mit User-Info zurückgeben
        c.execute('''
            SELECT
                recipes.*,
                users.name as user_name,
                users.email as user_email,
                users.avatar_color as user_avatar_color
            FROM recipes
            LEFT JOIN users ON recipes.user_id = users.id
            WHERE recipes.id = ?
        ''', (recipe_id,))
        recipe = dict(c.fetchone())
        conn.close()

        return jsonify(recipe), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """Einzelnes Rezept abrufen"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,))
    recipe = c.fetchone()
    conn.close()

    if recipe is None:
        return jsonify({'error': 'Recipe not found'}), 404

    return jsonify(dict(recipe))

@app.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    """Rezept aktualisieren (nur Owner!)"""
    try:
        data = request.json

        # user_id ist required (aktueller User)
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400

        conn = get_db()
        c = conn.cursor()

        # Rezept holen und Permission prüfen
        c.execute('SELECT user_id, is_system FROM recipes WHERE id = ?', (recipe_id,))
        recipe = c.fetchone()

        if not recipe:
            conn.close()
            return jsonify({'error': 'Recipe not found'}), 404

        # System-Rezepte können nicht bearbeitet werden
        if recipe['is_system']:
            conn.close()
            return jsonify({'error': 'Cannot edit system recipe'}), 403

        # Nur Owner darf bearbeiten
        if recipe['user_id'] != user_id:
            conn.close()
            return jsonify({'error': 'Permission denied. You can only edit your own recipes.'}), 403

        c.execute('''
            UPDATE recipes
            SET title = ?, image = ?, notes = ?,
                duration = ?, rating = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            data.get('title'),
            data.get('image'),
            data.get('notes'),
            data.get('duration'),
            data.get('rating'),
            recipe_id
        ))

        conn.commit()

        # Aktualisiertes Rezept mit User-Info zurückgeben
        c.execute('''
            SELECT
                recipes.*,
                users.name as user_name,
                users.email as user_email,
                users.avatar_color as user_avatar_color
            FROM recipes
            LEFT JOIN users ON recipes.user_id = users.id
            WHERE recipes.id = ?
        ''', (recipe_id,))
        recipe = dict(c.fetchone())
        conn.close()

        return jsonify(recipe)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    """Rezept löschen (nur Owner!)"""
    try:
        # user_id aus Query-Parameter oder Header
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400

        user_id = int(user_id)

        conn = get_db()
        c = conn.cursor()

        # Rezept holen und Permission prüfen
        c.execute('SELECT user_id, is_system, image FROM recipes WHERE id = ?', (recipe_id,))
        recipe = c.fetchone()

        if not recipe:
            conn.close()
            return jsonify({'error': 'Recipe not found'}), 404

        # System-Rezepte können nicht gelöscht werden
        if recipe['is_system']:
            conn.close()
            return jsonify({'error': 'Cannot delete system recipe'}), 403

        # Nur Owner darf löschen
        if recipe['user_id'] != user_id:
            conn.close()
            return jsonify({'error': 'Permission denied. You can only delete your own recipes.'}), 403

        # Bild löschen falls vorhanden
        if recipe['image']:
            image_path = os.path.join(UPLOAD_FOLDER, recipe['image'])
            if os.path.exists(image_path):
                os.remove(image_path)

        c.execute('DELETE FROM recipes WHERE id = ?', (recipe_id,))
        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Bild hochladen"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Eindeutigen Dateinamen generieren
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    file.save(filepath)

    return jsonify({'filename': filename})

@app.route('/api/uploads/<filename>')
def get_image(filename):
    """Bild abrufen"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Statistiken abrufen"""
    conn = get_db()
    c = conn.cursor()

    c.execute('SELECT COUNT(*) as total FROM recipes')
    total = c.fetchone()['total']

    c.execute('SELECT COUNT(*) as with_images FROM recipes WHERE image IS NOT NULL')
    with_images = c.fetchone()['with_images']

    conn.close()

    return jsonify({
        'total_recipes': total,
        'recipes_with_images': with_images
    })

# TODO API Endpoints

@app.route('/api/todos', methods=['GET'])
def get_todos():
    """Alle TODOs abrufen, gruppiert nach Priorität"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM todos ORDER BY priority ASC, id ASC')
    todos = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(todos)

@app.route('/api/todos', methods=['POST'])
def create_todo():
    """Neues TODO erstellen"""
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO todos (text, priority, completed)
        VALUES (?, ?, ?)
    ''', (data.get('text'), data.get('priority', 2), data.get('completed', 0)))
    conn.commit()
    todo_id = c.lastrowid
    c.execute('SELECT * FROM todos WHERE id = ?', (todo_id,))
    todo = dict(c.fetchone())
    conn.close()
    return jsonify(todo), 201

@app.route('/api/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    """Einzelnes TODO abrufen"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM todos WHERE id = ?', (todo_id,))
    todo = c.fetchone()
    conn.close()
    if todo:
        return jsonify(dict(todo))
    return jsonify({'error': 'TODO not found'}), 404

@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    """TODO aktualisieren"""
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        UPDATE todos
        SET text = ?, priority = ?, completed = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (data.get('text'), data.get('priority'), data.get('completed'), todo_id))
    conn.commit()
    c.execute('SELECT * FROM todos WHERE id = ?', (todo_id,))
    todo = dict(c.fetchone())
    conn.close()
    return jsonify(todo)

@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    """TODO löschen"""
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# Tagebuch API Endpoints

@app.route('/api/diary', methods=['GET'])
def get_diary_entries():
    """Alle Tagebucheinträge abrufen"""
    conn = get_db()
    c = conn.cursor()

    # Optional: Suche nach Name, Notizen oder Rezept-Titel
    search = request.args.get('search')

    query = '''
        SELECT
            d.id, d.recipe_id, d.date, d.notes, d.images, d.dish_name,
            d.created_at, d.updated_at,
            r.title as recipe_title, r.image as recipe_image
        FROM diary_entries d
        LEFT JOIN recipes r ON d.recipe_id = r.id
        WHERE 1=1
    '''
    params = []

    if search:
        query += ' AND (d.dish_name LIKE ? OR d.notes LIKE ? OR r.title LIKE ?)'
        search_term = f'%{search}%'
        params.extend([search_term, search_term, search_term])

    query += ' ORDER BY d.date DESC, d.created_at DESC'

    c.execute(query, params)
    entries = [dict(row) for row in c.fetchall()]
    conn.close()

    # Parse images JSON
    import json
    for entry in entries:
        if entry['images']:
            try:
                entry['images'] = json.loads(entry['images'])
            except:
                entry['images'] = []
        else:
            entry['images'] = []

    return jsonify(entries)

@app.route('/api/diary', methods=['POST'])
def create_diary_entry():
    """Neuen Tagebucheintrag erstellen"""
    import json
    data = request.json

    conn = get_db()
    c = conn.cursor()

    # Images als JSON speichern
    images_json = json.dumps(data.get('images', []))

    c.execute('''
        INSERT INTO diary_entries (recipe_id, date, notes, images, dish_name)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        data.get('recipe_id'),
        data.get('date'),
        data.get('notes'),
        images_json,
        data.get('dish_name')
    ))

    conn.commit()
    entry_id = c.lastrowid

    # Eintrag mit Rezept-Daten zurückgeben
    c.execute('''
        SELECT
            d.id, d.recipe_id, d.date, d.notes, d.images, d.dish_name,
            d.created_at, d.updated_at,
            r.title as recipe_title, r.image as recipe_image
        FROM diary_entries d
        LEFT JOIN recipes r ON d.recipe_id = r.id
        WHERE d.id = ?
    ''', (entry_id,))
    entry = dict(c.fetchone())
    conn.close()

    # Parse images JSON
    if entry['images']:
        try:
            entry['images'] = json.loads(entry['images'])
        except:
            entry['images'] = []
    else:
        entry['images'] = []

    return jsonify(entry), 201

@app.route('/api/diary/<int:entry_id>', methods=['GET'])
def get_diary_entry(entry_id):
    """Einzelnen Tagebucheintrag abrufen"""
    import json
    conn = get_db()
    c = conn.cursor()

    c.execute('''
        SELECT
            d.id, d.recipe_id, d.date, d.notes, d.images,
            d.created_at, d.updated_at,
            r.title as recipe_title, r.image as recipe_image
        FROM diary_entries d
        LEFT JOIN recipes r ON d.recipe_id = r.id
        WHERE d.id = ?
    ''', (entry_id,))
    entry = c.fetchone()
    conn.close()

    if entry is None:
        return jsonify({'error': 'Entry not found'}), 404

    entry = dict(entry)

    # Parse images JSON
    if entry['images']:
        try:
            entry['images'] = json.loads(entry['images'])
        except:
            entry['images'] = []
    else:
        entry['images'] = []

    return jsonify(entry)

@app.route('/api/diary/<int:entry_id>', methods=['PUT'])
def update_diary_entry(entry_id):
    """Tagebucheintrag aktualisieren"""
    import json
    data = request.json

    conn = get_db()
    c = conn.cursor()

    # Images als JSON speichern
    images_json = json.dumps(data.get('images', []))

    c.execute('''
        UPDATE diary_entries
        SET recipe_id = ?, date = ?, notes = ?, images = ?, dish_name = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (
        data.get('recipe_id'),
        data.get('date'),
        data.get('notes'),
        images_json,
        data.get('dish_name'),
        entry_id
    ))

    conn.commit()

    # Aktualisierter Eintrag mit Rezept-Daten zurückgeben
    c.execute('''
        SELECT
            d.id, d.recipe_id, d.date, d.notes, d.images, d.dish_name,
            d.created_at, d.updated_at,
            r.title as recipe_title, r.image as recipe_image
        FROM diary_entries d
        LEFT JOIN recipes r ON d.recipe_id = r.id
        WHERE d.id = ?
    ''', (entry_id,))
    entry = dict(c.fetchone())
    conn.close()

    # Parse images JSON
    if entry['images']:
        try:
            entry['images'] = json.loads(entry['images'])
        except:
            entry['images'] = []
    else:
        entry['images'] = []

    return jsonify(entry)

@app.route('/api/diary/<int:entry_id>', methods=['DELETE'])
def delete_diary_entry(entry_id):
    """Tagebucheintrag löschen"""
    import json
    conn = get_db()
    c = conn.cursor()

    # Bilder löschen falls vorhanden
    c.execute('SELECT images FROM diary_entries WHERE id = ?', (entry_id,))
    row = c.fetchone()
    if row and row['images']:
        try:
            images = json.loads(row['images'])
            for image in images:
                image_path = os.path.join(UPLOAD_FOLDER, image)
                if os.path.exists(image_path):
                    os.remove(image_path)
        except:
            pass

    c.execute('DELETE FROM diary_entries WHERE id = ?', (entry_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True})

@app.route('/api/version')
def get_version():
    """Gibt die aktuelle App-Version zurück (aus Git-Tag oder env var)"""
    import subprocess

    version = os.environ.get('APP_VERSION', None)

    # Falls keine ENV var, versuche aus Git zu lesen
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
    """Globale Suche über Rezepte, Tagebuch und TODOs"""
    query = request.args.get('q', '').strip()

    if not query or len(query) < 2:
        return jsonify({
            'recipes': [],
            'diary_entries': [],
            'todos': []
        })

    conn = get_db()
    c = conn.cursor()

    # Wildcard für LIKE-Suche
    search_pattern = f'%{query}%'

    # Suche in Rezepten
    c.execute('''
        SELECT id, title, notes, image, rating, duration
        FROM recipes
        WHERE title LIKE ? OR notes LIKE ?
        ORDER BY
            CASE
                WHEN title LIKE ? THEN 1
                ELSE 2
            END,
            title
        LIMIT 20
    ''', (search_pattern, search_pattern, f'{query}%'))

    recipes = []
    for row in c.fetchall():
        # Snippet aus notes erstellen (erste 100 Zeichen)
        notes = row['notes'] or ''
        snippet = notes[:100] + '...' if len(notes) > 100 else notes

        recipes.append({
            'id': row['id'],
            'title': row['title'],
            'snippet': snippet if notes else None,
            'image': row['image'],
            'rating': row['rating'],
            'duration': row['duration'],
            'type': 'recipe'
        })

    # Suche in Tagebuch-Einträgen
    c.execute('''
        SELECT d.id, d.notes, d.dish_name, d.created_at,
               r.title as recipe_title, r.image as recipe_image
        FROM diary_entries d
        LEFT JOIN recipes r ON d.recipe_id = r.id
        WHERE d.notes LIKE ? OR d.dish_name LIKE ? OR r.title LIKE ?
        ORDER BY d.created_at DESC
        LIMIT 20
    ''', (search_pattern, search_pattern, search_pattern))

    diary_entries = []
    for row in c.fetchall():
        # Snippet aus notes erstellen (erste 100 Zeichen)
        notes = row['notes'] or ''
        snippet = notes[:100] + '...' if len(notes) > 100 else notes

        # Anzeige-Titel: dish_name falls vorhanden, sonst recipe_title
        display_title = row['dish_name'] or row['recipe_title'] or 'Ohne Titel'

        diary_entries.append({
            'id': row['id'],
            'snippet': snippet,
            'recipe_title': display_title,
            'recipe_image': row['recipe_image'],
            'created_at': row['created_at'],
            'type': 'diary'
        })

    # Suche in TODOs
    c.execute('''
        SELECT id, text, priority, completed
        FROM todos
        WHERE text LIKE ?
        ORDER BY
            CASE WHEN completed = 1 THEN 2 ELSE 1 END,
            priority DESC
        LIMIT 20
    ''', (search_pattern,))

    todos = []
    for row in c.fetchall():
        todos.append({
            'id': row['id'],
            'text': row['text'],
            'priority': row['priority'],
            'completed': row['completed'],
            'type': 'todo'
        })

    conn.close()

    return jsonify({
        'recipes': recipes,
        'diary_entries': diary_entries,
        'todos': todos,
        'query': query
    })

# Server starten
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=80, debug=False)
