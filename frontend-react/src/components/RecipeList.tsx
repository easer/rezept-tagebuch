import { useState, useEffect } from 'react';
import type { Recipe } from '../types/recipe';
import { recipeApi } from '../services/api';
import { RecipeCard } from './RecipeCard';
import './RecipeList.css';

export const RecipeList = () => {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadRecipes();
  }, []);

  const loadRecipes = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await recipeApi.getRecipes();
      setRecipes(data);
    } catch (err) {
      console.error('Failed to load recipes:', err);
      setError('Fehler beim Laden der Rezepte');
    } finally {
      setLoading(false);
    }
  };

  const handleRecipeClick = (recipe: Recipe) => {
    console.log('Clicked recipe:', recipe);
    // TODO: Navigate to recipe detail page
  };

  if (loading) {
    return (
      <div className="recipe-list-container">
        <div className="loading">
          <div className="spinner"></div>
          <p>Lade Rezepte...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="recipe-list-container">
        <div className="error">
          <p>❌ {error}</p>
          <button onClick={loadRecipes}>Erneut versuchen</button>
        </div>
      </div>
    );
  }

  return (
    <div className="recipe-list-container">
      <header className="recipe-list-header">
        <h1 className="app-title">@rezept-tagebuch</h1>
        <p className="recipe-count">{recipes.length} Rezepte</p>
      </header>

      <div className="recipe-list">
        {recipes.length === 0 ? (
          <div className="empty-state">
            <p>Noch keine Rezepte vorhanden</p>
          </div>
        ) : (
          recipes.map((recipe) => (
            <RecipeCard
              key={recipe.id}
              recipe={recipe}
              onClick={() => handleRecipeClick(recipe)}
            />
          ))
        )}
      </div>
    </div>
  );
};
