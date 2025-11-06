import type { Recipe } from '../types/recipe';
import './RecipeCard.css';

interface RecipeCardProps {
  recipe: Recipe;
  onClick?: () => void;
}

export const RecipeCard = ({ recipe, onClick }: RecipeCardProps) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .substring(0, 2);
  };

  const renderStars = (rating?: number) => {
    if (!rating) return null;
    return (
      <div className="recipe-rating">
        {[...Array(5)].map((_, i) => (
          <span key={i} className={i < rating ? 'star filled' : 'star'}>
            ★
          </span>
        ))}
      </div>
    );
  };

  const isAutoImported = recipe.is_system === 1;

  return (
    <div
      className={`recipe-card ${isAutoImported ? 'auto-imported' : ''}`}
      onClick={onClick}
    >
      <div className="recipe-header">
        <div
          className="recipe-author-avatar"
          style={{ backgroundColor: recipe.user_avatar_color || '#FFB6C1' }}
        >
          {recipe.user_name && getInitials(recipe.user_name)}
        </div>
        <div className="recipe-info">
          <div className="recipe-title">{recipe.title}</div>
          <div className="recipe-meta">
            {recipe.user_name} • {formatDate(recipe.created_at)}
          </div>
        </div>
      </div>

      {recipe.image && (
        <div className="recipe-image">
          <img src={recipe.image} alt={recipe.title} />
        </div>
      )}

      {recipe.notes && (
        <div className="recipe-notes">{recipe.notes}</div>
      )}

      <div className="recipe-footer">
        {recipe.duration && (
          <div className="recipe-duration">⏱️ {recipe.duration} min</div>
        )}
        {renderStars(recipe.rating)}
      </div>

      {isAutoImported && (
        <div className="recipe-badge">
          🌍 TheMealDB
        </div>
      )}
    </div>
  );
};
