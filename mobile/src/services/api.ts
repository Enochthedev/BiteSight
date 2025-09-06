/**
 * API service configuration and base client
 */

import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ApiError, MealHistory, NutritionFeedback, WeeklyInsight } from '@/types';
import { networkService } from './networkService';
import { offlineStorage } from './offlineStorage';

const API_BASE_URL = __DEV__
    ? 'http://localhost:8000/api/v1'
    : 'https://api.nutritionfeedback.com/v1';

class ApiService {
    private client: AxiosInstance;
    private retryQueue: Map<string, () => Promise<any>> = new Map();

    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        this.setupInterceptors();
        this.initializeNetworkHandling();
    }

    private setupInterceptors(): void {
        // Request interceptor to add auth token
        this.client.interceptors.request.use(
            async (config) => {
                const token = await AsyncStorage.getItem('accessToken');
                if (token) {
                    config.headers.Authorization = `Bearer ${token}`;
                }
                return config;
            },
            (error) => Promise.reject(error)
        );

        // Response interceptor for error handling
        this.client.interceptors.response.use(
            (response: AxiosResponse) => response,
            (error: AxiosError) => {
                const apiError = this.handleApiError(error);
                return Promise.reject(apiError);
            }
        );
    }

    private handleApiError(error: AxiosError): ApiError {
        if (error.response?.data) {
            // Server returned an error response
            return error.response.data as ApiError;
        }

        if (error.code === 'ECONNABORTED') {
            return {
                errorCode: 'TIMEOUT',
                errorMessage: 'Request timeout',
                userMessage: 'The request took too long. Please try again.',
                retryPossible: true,
                suggestedActions: ['Check your internet connection', 'Try again'],
                timestamp: new Date().toISOString(),
            };
        }

        if (!error.response) {
            return {
                errorCode: 'NETWORK_ERROR',
                errorMessage: 'Network connection failed',
                userMessage: 'Unable to connect to the server. Please check your internet connection.',
                retryPossible: true,
                suggestedActions: ['Check your internet connection', 'Try again later'],
                timestamp: new Date().toISOString(),
            };
        }

        return {
            errorCode: 'UNKNOWN_ERROR',
            errorMessage: error.message || 'An unknown error occurred',
            userMessage: 'Something went wrong. Please try again.',
            retryPossible: true,
            suggestedActions: ['Try again', 'Contact support if the problem persists'],
            timestamp: new Date().toISOString(),
        };
    }

    public get<T>(url: string, params?: any): Promise<T> {
        return this.client.get(url, { params }).then(response => response.data);
    }

    public post<T>(url: string, data?: any): Promise<T> {
        return this.client.post(url, data).then(response => response.data);
    }

    public put<T>(url: string, data?: any): Promise<T> {
        return this.client.put(url, data).then(response => response.data);
    }

    public delete<T>(url: string): Promise<T> {
        return this.client.delete(url).then(response => response.data);
    }

    public uploadFile<T>(url: string, formData: FormData): Promise<T> {
        return this.client.post(url, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            timeout: 60000, // Longer timeout for file uploads
        }).then(response => response.data);
    }

    private initializeNetworkHandling(): void {
        // Listen for network changes to process retry queue
        networkService.addListener((networkState) => {
            if (networkState.isConnected && networkState.isInternetReachable) {
                this.processRetryQueue();
            }
        });
    }

    private async processRetryQueue(): Promise<void> {
        const retryPromises = Array.from(this.retryQueue.values());
        this.retryQueue.clear();

        await Promise.allSettled(retryPromises);
    }

    // Enhanced methods with offline support
    public async getWithOfflineSupport<T>(
        url: string,
        params?: any,
        cacheKey?: string
    ): Promise<T> {
        try {
            if (!networkService.isOnline()) {
                // Try to get from cache
                if (cacheKey) {
                    const cachedData = await this.getCachedData<T>(cacheKey);
                    if (cachedData) {
                        return cachedData;
                    }
                }
                throw this.createOfflineError();
            }

            const data = await this.get<T>(url, params);

            // Cache the result if cache key provided
            if (cacheKey) {
                await this.setCachedData(cacheKey, data);
            }

            return data;
        } catch (error) {
            // If network error and we have cached data, return it
            if (cacheKey && this.isNetworkError(error)) {
                const cachedData = await this.getCachedData<T>(cacheKey);
                if (cachedData) {
                    return cachedData;
                }
            }
            throw error;
        }
    }

    public async postWithRetry<T>(
        url: string,
        data?: any,
        retryOnOffline: boolean = true
    ): Promise<T> {
        if (!networkService.isOnline() && retryOnOffline) {
            // Queue for retry when online
            const retryId = `retry_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            const retryPromise = () => this.post<T>(url, data);
            this.retryQueue.set(retryId, retryPromise);

            throw this.createOfflineError();
        }

        return this.post<T>(url, data);
    }

    // Specific API methods with offline support
    public async getMealHistory(
        limit: number = 20,
        offset: number = 0
    ): Promise<MealHistory> {
        try {
            return await this.getWithOfflineSupport<MealHistory>(
                '/meals/history',
                { limit, offset },
                'meal_history'
            );
        } catch (error) {
            // Fallback to cached meals
            const cachedMeals = await offlineStorage.getCachedMeals();
            return {
                meals: cachedMeals.map(cached => cached.analysis),
                totalCount: cachedMeals.length,
                hasMore: false,
            };
        }
    }

    public async getMealFeedback(mealId: string): Promise<NutritionFeedback> {
        try {
            return await this.getWithOfflineSupport<NutritionFeedback>(
                `/meals/${mealId}/feedback`,
                undefined,
                `feedback_${mealId}`
            );
        } catch (error) {
            // Check cached meal for feedback
            const cachedMeal = await offlineStorage.getCachedMeal(mealId);
            if (cachedMeal?.feedback) {
                return cachedMeal.feedback;
            }
            throw error;
        }
    }

    public async getWeeklyInsights(): Promise<WeeklyInsight[]> {
        try {
            return await this.getWithOfflineSupport<WeeklyInsight[]>(
                '/insights/weekly',
                undefined,
                'weekly_insights'
            );
        } catch (error) {
            // Fallback to cached insights
            return await offlineStorage.getCachedWeeklyInsights();
        }
    }

    private async getCachedData<T>(key: string): Promise<T | null> {
        try {
            const cached = await AsyncStorage.getItem(`api_cache_${key}`);
            return cached ? JSON.parse(cached) : null;
        } catch (error) {
            console.error('Error getting cached data:', error);
            return null;
        }
    }

    private async setCachedData<T>(key: string, data: T): Promise<void> {
        try {
            await AsyncStorage.setItem(`api_cache_${key}`, JSON.stringify(data));
        } catch (error) {
            console.error('Error setting cached data:', error);
        }
    }

    private createOfflineError(): ApiError {
        return {
            errorCode: 'OFFLINE',
            errorMessage: 'No internet connection',
            userMessage: 'You\'re currently offline. Some features may not be available.',
            retryPossible: true,
            suggestedActions: ['Check your internet connection', 'Try again when online'],
            timestamp: new Date().toISOString(),
        };
    }

    private isNetworkError(error: any): boolean {
        return error?.errorCode === 'NETWORK_ERROR' ||
            error?.errorCode === 'TIMEOUT' ||
            error?.code === 'ECONNABORTED' ||
            !error?.response;
    }
}

export const apiService = new ApiService();