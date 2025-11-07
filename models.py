"""
SQLAlchemy Database Models for Rezept-Tagebuch
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    avatar_color = db.Column(db.String(7), default='#FFB6C1')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    recipes = db.relationship('Recipe', back_populates='user', lazy='dynamic')
    todos = db.relationship('Todo', back_populates='user', lazy='dynamic')
    diary_entries = db.relationship('DiaryEntry', back_populates='user', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'avatar_color': self.avatar_color,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Recipe(db.Model):
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    image = db.Column(db.Text)
    notes = db.Column(db.Text)
    duration = db.Column(db.Float)
    rating = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_system = db.Column(db.Boolean, default=False)
    auto_imported = db.Column(db.Boolean, default=False)
    imported_at = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='recipes')
    diary_entries = db.relationship('DiaryEntry', back_populates='recipe', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'image': self.image,
            'notes': self.notes,
            'duration': self.duration,
            'rating': self.rating,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'user_email': self.user.email if self.user else None,
            'user_avatar_color': self.user.avatar_color if self.user else None,
            'is_system': self.is_system,
            'auto_imported': self.auto_imported,
            'imported_at': self.imported_at.isoformat() if self.imported_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Todo(db.Model):
    __tablename__ = 'todos'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='todos')

    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'priority': self.priority,
            'completed': self.completed,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DiaryEntry(db.Model):
    __tablename__ = 'diary_entries'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id', ondelete='SET NULL'))
    dish_name = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    images = db.Column(db.Text)  # JSON array as text
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recipe = db.relationship('Recipe', back_populates='diary_entries')
    user = db.relationship('User', back_populates='diary_entries')

    def to_dict(self):
        return {
            'id': self.id,
            'recipe_id': self.recipe_id,
            'dish_name': self.dish_name,
            'date': self.date.isoformat() if self.date else None,
            'notes': self.notes,
            'images': self.images,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
