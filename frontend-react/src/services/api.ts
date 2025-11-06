import axios from 'axios';
import type { Recipe } from '../types/recipe';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const recipeApi = {
  // Get all recipes
  getRecipes: async (): Promise<Recipe[]> => {
    const response = await api.get<Recipe[]>('/api/recipes');
    return response.data;
  },

  // Get single recipe
  getRecipe: async (id: number): Promise<Recipe> => {
    const response = await api.get<Recipe>(`/api/recipes/${id}`);
    return response.data;
  },

  // Create recipe
  createRecipe: async (recipe: Partial<Recipe>): Promise<Recipe> => {
    const response = await api.post<Recipe>('/api/recipes', recipe);
    return response.data;
  },

  // Update recipe
  updateRecipe: async (id: number, recipe: Partial<Recipe>): Promise<Recipe> => {
    const response = await api.put<Recipe>(`/api/recipes/${id}`, recipe);
    return response.data;
  },

  // Delete recipe
  deleteRecipe: async (id: number): Promise<void> => {
    await api.delete(`/api/recipes/${id}`);
  },
};

export default api;
