export interface User {
  id: number;
  email: string;
  nickname: string;
  name?: string;
  is_admin: boolean;
  is_active: boolean;
  profile?: UserProfile;
  banned_until?: string;
}

export interface UserProfile {
  height?: number;
  weight?: number;
  exercise_purpose?: 'posture' | 'strength' | 'weight_management';
  diet_purpose?: 'loss' | 'gain' | 'maintain' | 'medical';
  medical_history?: string;
  medications?: string;
}

export interface ExerciseLog {
  id: number;
  date: string;
  content: string;
  duration_minutes: number;
  exercises: ExerciseItem[];
}

export interface ExerciseItem {
  name: string;
  sets?: number;
  reps?: number;
  weight?: number;
  duration_minutes?: number;
  note?: string;
}

export interface DietLog {
  id: number;
  date: string;
  meals: MealItem[];
  total_calories: number;
  note?: string;
}

export interface MealItem {
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  foods: FoodItem[];
}

export interface FoodItem {
  name: string;
  calories: number;
  amount?: string;
}

export interface WeightRecord {
  id: number;
  date: string;
  weight: number;
}

export type ExercisePurpose = 'posture' | 'strength' | 'weight_management';
export type DietPurpose = 'loss' | 'gain' | 'maintain' | 'medical';

export interface ExerciseRoutine {
  id: number;
  purpose: ExercisePurpose;
  name: string;
  description?: string;
  difficulty?: string;
  sessions_per_week: number;
  exercises: RoutineExercise[];
  is_active?: boolean;
}

export interface RoutineExercise {
  name: string;
  sets: number | string;
  reps: string;
  rest: string;
  notes?: string;
}

export interface DietRecommendation {
  id: number;
  purpose: DietPurpose;
  name: string;
  description?: string;
  carb_ratio: number;
  protein_ratio: number;
  fat_ratio: number;
  calorie_note?: string;
  nutrients: NutrientGoal[];
  is_active?: boolean;
}

export interface NutrientGoal {
  name: string;
  target: string;
  unit: string;
  notes?: string;
}

export interface ExerciseCalorie {
  id: number;
  name: string;
  category: string;
  met: number;
  description?: string;
}

export interface Post {
  id: number;
  title: string;
  content: string;
  summary?: string;
  board_type: string;
  author: { id: number; nickname: string };
  tags: string[];
  view_count: number;
  comment_count: number;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
