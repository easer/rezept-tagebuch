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
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            cooked_date DATE NOT NULL,
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

@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    """Alle Rezepte abrufen"""
    conn = get_db()
    c = conn.cursor()

    # Optional: Suche nach Titel oder Notizen
    search = request.args.get('search')

    query = 'SELECT * FROM recipes WHERE 1=1'
    params = []

    if search:
        query += ' AND (title LIKE ? OR notes LIKE ?)'
        search_term = f'%{search}%'
        params.extend([search_term, search_term])

    query += ' ORDER BY cooked_date DESC'

    c.execute(query, params)
    recipes = [dict(row) for row in c.fetchall()]
    conn.close()

    return jsonify(recipes)

@app.route('/api/recipes', methods=['POST'])
def create_recipe():
    """Neues Rezept erstellen"""
    data = request.json

    conn = get_db()
    c = conn.cursor()

    c.execute('''
        INSERT INTO recipes (title, cooked_date, image, notes, duration, rating)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data.get('title'),
        data.get('cooked_date'),
        data.get('image'),
        data.get('notes'),
        data.get('duration'),
        data.get('rating')
    ))

    conn.commit()
    recipe_id = c.lastrowid

    # Rezept zurückgeben
    c.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,))
    recipe = dict(c.fetchone())
    conn.close()

    return jsonify(recipe), 201

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
    """Rezept aktualisieren"""
    data = request.json

    conn = get_db()
    c = conn.cursor()

    c.execute('''
        UPDATE recipes
        SET title = ?, cooked_date = ?, image = ?, notes = ?,
            duration = ?, rating = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (
        data.get('title'),
        data.get('cooked_date'),
        data.get('image'),
        data.get('notes'),
        data.get('duration'),
        data.get('rating'),
        recipe_id
    ))

    conn.commit()

    # Aktualisiertes Rezept zurückgeben
    c.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,))
    recipe = dict(c.fetchone())
    conn.close()

    return jsonify(recipe)

@app.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    """Rezept löschen"""
    conn = get_db()
    c = conn.cursor()

    # Bild löschen falls vorhanden
    c.execute('SELECT image FROM recipes WHERE id = ?', (recipe_id,))
    row = c.fetchone()
    if row and row['image']:
        image_path = os.path.join(UPLOAD_FOLDER, row['image'])
        if os.path.exists(image_path):
            os.remove(image_path)

    c.execute('DELETE FROM recipes WHERE id = ?', (recipe_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True})

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

# Server starten
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=80, debug=False)
