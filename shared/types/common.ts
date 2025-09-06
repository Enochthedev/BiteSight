/**
 * Common types shared between backend and mobile applications
 */

export interface BaseEntity {
  id: string;
  createdAt: string;
  updatedAt?: string;
}

export interface PaginationParams {
  limit: number;
  offset: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  totalCount: number;
  hasMore: boolean;
  limit: number;
  offset: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  timestamp: string;
}

export interface ApiError {
  errorCode: string;
  errorMessage: string;
  userMessage: string;
  retryPossible: boolean;
  suggestedActions: string[];
  timestamp: string;
}

export enum FoodClass {
  CARBOHYDRATES = 'carbohydrates',
  PROTEINS = 'proteins',
  FATS = 'fats',
  VITAMINS = 'vitamins',
  MINERALS = 'minerals',
  WATER = 'water',
}

export enum AnalysisStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum FeedbackType {
  BALANCED = 'balanced',
  MISSING_GROUPS = 'missing_groups',
  EXCESSIVE = 'excessive',
  IMPROVEMENT = 'improvement',
}

export interface NigerianFoodItem {
  id: string;
  foodName: string;
  localNames: Record<string, string>;
  foodClass: FoodClass;
  nutritionalInfo: Record<string, any>;
  culturalContext?: string;
}