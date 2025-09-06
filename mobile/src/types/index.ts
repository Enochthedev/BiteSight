/**
 * Core TypeScript interfaces for the mobile application
 */

export interface User {
    id: string;
    email: string;
    name: string;
    registrationDate: string;
    historyEnabled: boolean;
}

export interface LoginCredentials {
    email: string;
    password: string;
}

export interface RegisterData {
    email: string;
    name: string;
    password: string;
}

export interface AuthResponse {
    accessToken: string;
    tokenType: string;
    expiresIn: number;
    student: User;
}

export interface MealImage {
    uri: string;
    type: string;
    fileName: string;
    fileSize?: number;
}

export interface FoodDetection {
    foodName: string;
    confidence: number;
    foodClass: string;
    boundingBox?: {
        x: number;
        y: number;
        width: number;
        height: number;
    };
}

export interface MealAnalysis {
    id: string;
    studentId: string;
    imagePath: string;
    uploadDate: string;
    analysisStatus: 'pending' | 'processing' | 'completed' | 'failed';
    detectedFoods: FoodDetection[];
}

export interface NutritionFeedback {
    mealId: string;
    detectedFoods: FoodDetection[];
    missingFoodGroups: string[];
    recommendations: string[];
    overallBalanceScore: number;
    feedbackMessage: string;
}

export interface MealHistory {
    meals: MealAnalysis[];
    totalCount: number;
    hasMore: boolean;
}

export interface WeeklyInsight {
    id: string;
    studentId: string;
    weekPeriod: string;
    mealsAnalyzed: number;
    nutritionBalance: {
        carbohydrates: number;
        proteins: number;
        fats: number;
        vitamins: number;
        minerals: number;
        water: number;
    };
    improvementAreas: string[];
    positiveTrends: string[];
    recommendations: string;
    generatedAt: string;
}

export interface ApiError {
    errorCode: string;
    errorMessage: string;
    userMessage: string;
    retryPossible: boolean;
    suggestedActions: string[];
    timestamp: string;
}

export interface AppState {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;
}

export interface CameraPermissions {
    camera: boolean;
    storage: boolean;
}

export interface NetworkState {
    isConnected: boolean;
    isInternetReachable: boolean;
    type: string;
}

export interface SyncStatus {
    isRunning: boolean;
    lastSync: string | null;
    pendingItems: number;
    errors: ApiError[];
}

export type FoodClass =
    | 'carbohydrates'
    | 'proteins'
    | 'fats'
    | 'vitamins'
    | 'minerals'
    | 'water';

export type AnalysisStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type NavigationParamList = {
    Home: undefined;
    Camera: undefined;
    Analysis: { mealId: string; imageUri?: string };
    Feedback: { feedbackData: NutritionFeedback };
    History: undefined;
    Insights: undefined;
    Profile: undefined;
    Login: undefined;
    Register: undefined;
    Consent: {
        isInitialSetup?: boolean;
        onConsentComplete?: () => void;
    };
    Onboarding: undefined;
    Auth: undefined;
    Main: undefined;
};