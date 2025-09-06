/**
 * Offline storage service for caching data and managing sync
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { MealImage, MealAnalysis, NutritionFeedback, WeeklyInsight } from '@/types';

interface PendingUpload {
    id: string;
    image: MealImage;
    timestamp: string;
    retryCount: number;
    lastAttempt?: string;
}

interface CachedMeal {
    id: string;
    analysis: MealAnalysis;
    feedback?: NutritionFeedback;
    timestamp: string;
}

interface SyncQueueItem {
    id: string;
    type: 'meal_upload' | 'feedback_request' | 'history_sync';
    data: any;
    timestamp: string;
    retryCount: number;
}

export class OfflineStorageService {
    private static instance: OfflineStorageService;
    private readonly PENDING_UPLOADS_KEY = 'pending_uploads';
    private readonly CACHED_MEALS_KEY = 'cached_meals';
    private readonly SYNC_QUEUE_KEY = 'sync_queue';
    private readonly WEEKLY_INSIGHTS_KEY = 'weekly_insights';
    private readonly MAX_RETRY_COUNT = 3;
    private readonly MAX_CACHE_SIZE = 50; // Maximum number of cached meals

    private constructor() { }

    public static getInstance(): OfflineStorageService {
        if (!OfflineStorageService.instance) {
            OfflineStorageService.instance = new OfflineStorageService();
        }
        return OfflineStorageService.instance;
    }

    // Pending uploads management
    public async addPendingUpload(image: MealImage): Promise<string> {
        const uploadId = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const pendingUpload: PendingUpload = {
            id: uploadId,
            image,
            timestamp: new Date().toISOString(),
            retryCount: 0,
        };

        const existingUploads = await this.getPendingUploads();
        existingUploads.push(pendingUpload);

        await AsyncStorage.setItem(this.PENDING_UPLOADS_KEY, JSON.stringify(existingUploads));
        return uploadId;
    }

    public async getPendingUploads(): Promise<PendingUpload[]> {
        try {
            const data = await AsyncStorage.getItem(this.PENDING_UPLOADS_KEY);
            return data ? JSON.parse(data) : [];
        } catch (error) {
            console.error('Error getting pending uploads:', error);
            return [];
        }
    }

    public async removePendingUpload(uploadId: string): Promise<void> {
        const uploads = await this.getPendingUploads();
        const filteredUploads = uploads.filter(upload => upload.id !== uploadId);
        await AsyncStorage.setItem(this.PENDING_UPLOADS_KEY, JSON.stringify(filteredUploads));
    }

    public async incrementRetryCount(uploadId: string): Promise<void> {
        const uploads = await this.getPendingUploads();
        const upload = uploads.find(u => u.id === uploadId);

        if (upload) {
            upload.retryCount += 1;
            upload.lastAttempt = new Date().toISOString();

            if (upload.retryCount >= this.MAX_RETRY_COUNT) {
                // Remove failed uploads after max retries
                await this.removePendingUpload(uploadId);
            } else {
                await AsyncStorage.setItem(this.PENDING_UPLOADS_KEY, JSON.stringify(uploads));
            }
        }
    }

    // Cached meals management
    public async cacheMeal(analysis: MealAnalysis, feedback?: NutritionFeedback): Promise<void> {
        const cachedMeal: CachedMeal = {
            id: analysis.id,
            analysis,
            feedback,
            timestamp: new Date().toISOString(),
        };

        const cachedMeals = await this.getCachedMeals();

        // Remove existing entry if it exists
        const filteredMeals = cachedMeals.filter(meal => meal.id !== analysis.id);

        // Add new entry at the beginning
        filteredMeals.unshift(cachedMeal);

        // Limit cache size
        const limitedMeals = filteredMeals.slice(0, this.MAX_CACHE_SIZE);

        await AsyncStorage.setItem(this.CACHED_MEALS_KEY, JSON.stringify(limitedMeals));
    }

    public async getCachedMeals(): Promise<CachedMeal[]> {
        try {
            const data = await AsyncStorage.getItem(this.CACHED_MEALS_KEY);
            return data ? JSON.parse(data) : [];
        } catch (error) {
            console.error('Error getting cached meals:', error);
            return [];
        }
    }

    public async getCachedMeal(mealId: string): Promise<CachedMeal | null> {
        const cachedMeals = await this.getCachedMeals();
        return cachedMeals.find(meal => meal.id === mealId) || null;
    }

    public async clearOldCachedMeals(daysToKeep: number = 7): Promise<void> {
        const cachedMeals = await this.getCachedMeals();
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);

        const filteredMeals = cachedMeals.filter(meal =>
            new Date(meal.timestamp) > cutoffDate
        );

        await AsyncStorage.setItem(this.CACHED_MEALS_KEY, JSON.stringify(filteredMeals));
    }

    // Sync queue management
    public async addToSyncQueue(type: SyncQueueItem['type'], data: any): Promise<void> {
        const queueItem: SyncQueueItem = {
            id: `sync_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            type,
            data,
            timestamp: new Date().toISOString(),
            retryCount: 0,
        };

        const syncQueue = await this.getSyncQueue();
        syncQueue.push(queueItem);

        await AsyncStorage.setItem(this.SYNC_QUEUE_KEY, JSON.stringify(syncQueue));
    }

    public async getSyncQueue(): Promise<SyncQueueItem[]> {
        try {
            const data = await AsyncStorage.getItem(this.SYNC_QUEUE_KEY);
            return data ? JSON.parse(data) : [];
        } catch (error) {
            console.error('Error getting sync queue:', error);
            return [];
        }
    }

    public async removeFromSyncQueue(itemId: string): Promise<void> {
        const syncQueue = await this.getSyncQueue();
        const filteredQueue = syncQueue.filter(item => item.id !== itemId);
        await AsyncStorage.setItem(this.SYNC_QUEUE_KEY, JSON.stringify(filteredQueue));
    }

    public async incrementSyncRetryCount(itemId: string): Promise<void> {
        const syncQueue = await this.getSyncQueue();
        const item = syncQueue.find(i => i.id === itemId);

        if (item) {
            item.retryCount += 1;

            if (item.retryCount >= this.MAX_RETRY_COUNT) {
                await this.removeFromSyncQueue(itemId);
            } else {
                await AsyncStorage.setItem(this.SYNC_QUEUE_KEY, JSON.stringify(syncQueue));
            }
        }
    }

    // Weekly insights caching
    public async cacheWeeklyInsights(insights: WeeklyInsight[]): Promise<void> {
        await AsyncStorage.setItem(this.WEEKLY_INSIGHTS_KEY, JSON.stringify(insights));
    }

    public async getCachedWeeklyInsights(): Promise<WeeklyInsight[]> {
        try {
            const data = await AsyncStorage.getItem(this.WEEKLY_INSIGHTS_KEY);
            return data ? JSON.parse(data) : [];
        } catch (error) {
            console.error('Error getting cached weekly insights:', error);
            return [];
        }
    }

    // General cache management
    public async clearAllCache(): Promise<void> {
        await Promise.all([
            AsyncStorage.removeItem(this.PENDING_UPLOADS_KEY),
            AsyncStorage.removeItem(this.CACHED_MEALS_KEY),
            AsyncStorage.removeItem(this.SYNC_QUEUE_KEY),
            AsyncStorage.removeItem(this.WEEKLY_INSIGHTS_KEY),
        ]);
    }

    public async getCacheSize(): Promise<number> {
        try {
            const keys = [
                this.PENDING_UPLOADS_KEY,
                this.CACHED_MEALS_KEY,
                this.SYNC_QUEUE_KEY,
                this.WEEKLY_INSIGHTS_KEY,
            ];

            let totalSize = 0;
            for (const key of keys) {
                const data = await AsyncStorage.getItem(key);
                if (data) {
                    totalSize += new Blob([data]).size;
                }
            }
            return totalSize;
        } catch (error) {
            console.error('Error calculating cache size:', error);
            return 0;
        }
    }
}

export const offlineStorage = OfflineStorageService.getInstance();