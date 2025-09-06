/**
 * Synchronization service for offline/online data sync
 */

import { networkService } from './networkService';
import { offlineStorage } from './offlineStorage';
import { uploadService } from './uploadService';
import { apiService } from './api';
import { MealHistory, WeeklyInsight, ApiError } from '@/types';

export interface SyncStatus {
    isRunning: boolean;
    lastSync: string | null;
    pendingItems: number;
    errors: ApiError[];
}

export class SyncService {
    private static instance: SyncService;
    private isSyncing: boolean = false;
    private syncListeners: ((status: SyncStatus) => void)[] = [];
    private lastSyncTime: string | null = null;
    private syncErrors: ApiError[] = [];

    private constructor() {
        this.initializeAutoSync();
    }

    public static getInstance(): SyncService {
        if (!SyncService.instance) {
            SyncService.instance = new SyncService();
        }
        return SyncService.instance;
    }

    private initializeAutoSync(): void {
        // Listen for network changes and sync when online
        networkService.addListener((networkState) => {
            if (networkState.isConnected && networkState.isInternetReachable && !this.isSyncing) {
                // Delay sync to allow network to stabilize
                setTimeout(() => {
                    this.performSync();
                }, 2000);
            }
        });

        // Periodic sync when online (every 5 minutes)
        setInterval(() => {
            if (networkService.isOnline() && !this.isSyncing) {
                this.performSync();
            }
        }, 5 * 60 * 1000);
    }

    public async performSync(force: boolean = false): Promise<void> {
        if (this.isSyncing && !force) {
            return;
        }

        if (!networkService.isOnline()) {
            return;
        }

        this.isSyncing = true;
        this.syncErrors = [];
        this.notifyListeners();

        try {
            // Sync pending uploads
            await this.syncPendingUploads();

            // Sync meal history
            await this.syncMealHistory();

            // Sync weekly insights
            await this.syncWeeklyInsights();

            // Process sync queue
            await this.processSyncQueue();

            this.lastSyncTime = new Date().toISOString();

        } catch (error) {
            console.error('Sync error:', error);
            this.syncErrors.push(error as ApiError);
        } finally {
            this.isSyncing = false;
            this.notifyListeners();
        }
    }

    private async syncPendingUploads(): Promise<void> {
        try {
            await uploadService.processPendingUploads();
        } catch (error) {
            console.error('Error syncing pending uploads:', error);
            this.syncErrors.push({
                errorCode: 'UPLOAD_SYNC_ERROR',
                errorMessage: 'Failed to sync pending uploads',
                userMessage: 'Some meal uploads are still pending. They will be retried automatically.',
                retryPossible: true,
                suggestedActions: ['Check your internet connection'],
                timestamp: new Date().toISOString(),
            });
        }
    }

    private async syncMealHistory(): Promise<void> {
        try {
            // Get latest meal history from server
            const history: MealHistory = await apiService.get('/meals/history', {
                limit: 50,
                offset: 0,
            });

            // Cache the updated history
            for (const meal of history.meals) {
                await offlineStorage.cacheMeal(meal);
            }

        } catch (error) {
            console.error('Error syncing meal history:', error);
            this.syncErrors.push({
                errorCode: 'HISTORY_SYNC_ERROR',
                errorMessage: 'Failed to sync meal history',
                userMessage: 'Unable to update meal history. Using cached data.',
                retryPossible: true,
                suggestedActions: ['Try again later'],
                timestamp: new Date().toISOString(),
            });
        }
    }

    private async syncWeeklyInsights(): Promise<void> {
        try {
            // Get latest weekly insights from server
            const insights: WeeklyInsight[] = await apiService.get('/insights/weekly');

            // Cache the insights
            await offlineStorage.cacheWeeklyInsights(insights);

        } catch (error) {
            console.error('Error syncing weekly insights:', error);
            this.syncErrors.push({
                errorCode: 'INSIGHTS_SYNC_ERROR',
                errorMessage: 'Failed to sync weekly insights',
                userMessage: 'Unable to update weekly insights. Using cached data.',
                retryPossible: true,
                suggestedActions: ['Try again later'],
                timestamp: new Date().toISOString(),
            });
        }
    }

    private async processSyncQueue(): Promise<void> {
        const syncQueue = await offlineStorage.getSyncQueue();

        for (const item of syncQueue) {
            try {
                switch (item.type) {
                    case 'meal_upload':
                        await this.syncMealUpload(item);
                        break;
                    case 'feedback_request':
                        await this.syncFeedbackRequest(item);
                        break;
                    case 'history_sync':
                        await this.syncHistoryRequest(item);
                        break;
                }

                // Remove successfully synced item
                await offlineStorage.removeFromSyncQueue(item.id);

            } catch (error) {
                console.error(`Error syncing queue item ${item.id}:`, error);
                await offlineStorage.incrementSyncRetryCount(item.id);
            }
        }
    }

    private async syncMealUpload(item: any): Promise<void> {
        // This would handle any remaining meal upload sync logic
        // Most uploads are handled by uploadService.processPendingUploads()
        const { image } = item.data;
        await uploadService.uploadMealImage(image, { retryOnFailure: false });
    }

    private async syncFeedbackRequest(item: any): Promise<void> {
        const { mealId } = item.data;
        const feedback = await apiService.get(`/meals/${mealId}/feedback`);

        // Update cached meal with feedback
        const cachedMeal = await offlineStorage.getCachedMeal(mealId);
        if (cachedMeal) {
            await offlineStorage.cacheMeal(cachedMeal.analysis, feedback);
        }
    }

    private async syncHistoryRequest(item: any): Promise<void> {
        const { dateRange } = item.data;
        const history: MealHistory = await apiService.get('/meals/history', dateRange);

        // Cache the history data
        for (const meal of history.meals) {
            await offlineStorage.cacheMeal(meal);
        }
    }

    public getSyncStatus(): SyncStatus {
        return {
            isRunning: this.isSyncing,
            lastSync: this.lastSyncTime,
            pendingItems: 0, // This would be calculated from pending uploads and sync queue
            errors: this.syncErrors,
        };
    }

    public addSyncListener(callback: (status: SyncStatus) => void): () => void {
        this.syncListeners.push(callback);

        // Return unsubscribe function
        return () => {
            const index = this.syncListeners.indexOf(callback);
            if (index > -1) {
                this.syncListeners.splice(index, 1);
            }
        };
    }

    private notifyListeners(): void {
        const status = this.getSyncStatus();
        this.syncListeners.forEach(listener => listener(status));
    }

    public async forceSyncNow(): Promise<void> {
        await this.performSync(true);
    }

    public async clearSyncErrors(): Promise<void> {
        this.syncErrors = [];
        this.notifyListeners();
    }

    public async getPendingItemsCount(): Promise<number> {
        const [pendingUploads, syncQueue] = await Promise.all([
            offlineStorage.getPendingUploads(),
            offlineStorage.getSyncQueue(),
        ]);

        return pendingUploads.length + syncQueue.length;
    }
}

export const syncService = SyncService.getInstance();