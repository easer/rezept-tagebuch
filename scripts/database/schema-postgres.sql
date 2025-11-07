-- PostgreSQL Schema for Rezept-Tagebuch
-- Generated from SQLite schema on 2025-11-07
-- This is the clean starting point for PostgreSQL migration

-- Drop existing tables if they exist
DROP TABLE IF EXISTS diary_entries CASCADE;
DROP TABLE IF EXISTS todos CASCADE;
DROP TABLE IF EXISTS recipes CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS alembic_version CASCADE;

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    avatar_color TEXT DEFAULT '#FFB6C1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recipes table
CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    image TEXT,
    notes TEXT,
    duration REAL,
    rating INTEGER,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_system BOOLEAN DEFAULT FALSE,
    auto_imported BOOLEAN DEFAULT FALSE,
    imported_at DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Todos table
CREATE TABLE todos (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    priority INTEGER NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Diary Entries table
CREATE TABLE diary_entries (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes(id) ON DELETE SET NULL,
    date DATE NOT NULL,
    notes TEXT,
    images TEXT,
    dish_name TEXT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alembic version tracking
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Indexes for performance
CREATE INDEX idx_recipes_user_id ON recipes(user_id);
CREATE INDEX idx_recipes_auto_imported ON recipes(auto_imported);
CREATE INDEX idx_todos_user_id ON todos(user_id);
CREATE INDEX idx_todos_completed ON todos(completed);
CREATE INDEX idx_diary_entries_user_id ON diary_entries(user_id);
CREATE INDEX idx_diary_entries_recipe_id ON diary_entries(recipe_id);
CREATE INDEX idx_diary_entries_date ON diary_entries(date);
