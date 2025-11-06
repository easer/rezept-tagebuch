export interface Recipe {
  id: number;
  title: string;
  image?: string;
  notes?: string;
  duration?: number;
  rating?: number;
  created_at: string;
  updated_at: string;
  user_id: number;
  user_name?: string;
  user_email?: string;
  user_avatar_color?: string;
  is_system?: number;
}

export interface User {
  id: number;
  name: string;
  email: string;
  avatar_color: string;
  created_at: string;
}
