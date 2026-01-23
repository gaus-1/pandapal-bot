/**
 * Типы данных API.
 */

export interface UserProfile {
  telegram_id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  age?: number;
  grade?: number;
  user_type: 'child' | 'parent';
  premium_until?: string;
  is_premium: boolean;
  premium_days_left?: number;
  active_subscription?: {
    id: number;
    plan_id: string;
    starts_at: string;
    expires_at: string;
    is_active: boolean;
    payment_method?: string;
    auto_renew?: boolean;
    has_saved_payment_method?: boolean;
  };
}

export interface ProgressItem {
  subject: string;
  level: number;
  points: number;
  last_activity: string;
}

export interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  unlocked: boolean;
  unlock_date?: string;
  xp_reward?: number;
  progress?: number;
  progress_max?: number;
}

export interface DashboardStats {
  total_messages: number;
  learning_sessions: number;
  total_points: number;
  subjects_studied: number;
  current_streak: number;
}

export interface AchievementUnlocked {
  achievement_id: string;
  title: string;
  description: string;
  icon: string;
  xp_reward: number;
}

export interface GameSession {
  id: number;
  game_type: string;
  game_state: Record<string, unknown>;
  result: string | null;
  score: number | null;
  started_at: string;
  finished_at: string | null;
  duration_seconds: number | null;
}

export interface GameStats {
  game_type: string;
  total_games: number;
  wins: number;
  losses: number;
  draws: number;
  win_rate: number;
  best_score: number | null;
  total_score: number;
  last_played_at: string | null;
}
