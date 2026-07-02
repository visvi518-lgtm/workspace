// ────────────── Auth / User ──────────────
export interface User {
  id: number;
  email: string;
  nickname: string;
  name?: string;
  is_admin: boolean;
  is_active: boolean;
  is_dormant: boolean;
  banned_until?: string;
  ban_reason?: string;
  profile?: UserProfile;
  created_at: string;
  last_login?: string;
}

export interface UserProfile {
  height?: number;
  weight?: number;
  medical_history?: string;
  medications?: string;
  exercise_habits?: string;
  nationality?: 'korean' | 'foreign';
  exercise_purpose?: 'posture' | 'strength' | 'weight_management';
  diet_purpose?: 'loss' | 'gain' | 'maintain' | 'medical';
}

// ────────────── Board ──────────────
export type BoardType = 'health' | 'exercise' | 'free';

export interface Post {
  id: number;
  title: string;
  content: string;
  summary?: string;
  source_url?: string;
  board_type: BoardType;
  author: { id: number; nickname: string };
  tags: string[];
  view_count: number;
  comment_count: number;
  created_at: string;
  updated_at: string;
  is_crawled: boolean;
  crawl_status?: 'draft' | 'published' | 'rejected';
}

export interface Comment {
  id: number;
  content: string;
  author: { id: number; nickname: string };
  created_at: string;
  updated_at: string;
}

// ────────────── Health Management ──────────────
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

// ────────────── Chat ──────────────
export interface ChatSession {
  id: number;
  title: string;
  summary?: string;
  created_at: string;
}

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  references?: PaperReference[];
  created_at: string;
}

export interface PaperReference {
  title: string;
  authors?: string;
  journal?: string;
  year?: number;
  url?: string;
}

// ────────────── API ──────────────
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ApiError {
  detail: string;
}

// ────────────── Banner ──────────────
export interface Banner {
  id: number;
  title?: string;
  subtitle?: string;
  link_url?: string;
  has_image: boolean;
  order_idx?: number;
  is_active?: boolean;
}

// ────────────── Recommendations ──────────────

export type ExercisePurpose = 'posture' | 'strength' | 'weight_management';
export type DietPurpose = 'loss' | 'gain' | 'maintain' | 'medical';
export type Difficulty = 'beginner' | 'intermediate' | 'advanced';

export interface RoutineExercise {
  name: string;
  sets: number | string;
  reps: string;
  rest: string;
  notes?: string;
}

export interface NutrientGoal {
  name: string;
  target: string;
  unit: string;
  notes?: string;
}

export interface ExerciseRoutine {
  id: number;
  purpose: ExercisePurpose;
  name: string;
  description?: string;
  difficulty?: Difficulty;
  sessions_per_week: number;
  exercises: RoutineExercise[];
  order_idx?: number;
  is_active?: boolean;
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
  order_idx?: number;
  is_active?: boolean;
}

export interface ExerciseCalorie {
  id: number;
  name: string;
  category: string;
  met: number;
  description?: string;
  is_active?: boolean;
}

// ────────────── Admin ──────────────
export type BanDuration = '3d' | '3w' | '3m' | '3y' | 'permanent';

export interface BanAction {
  user_id: number;
  duration: BanDuration;
  reason: string;
}
