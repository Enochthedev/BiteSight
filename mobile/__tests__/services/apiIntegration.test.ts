/**
 * Integration tests for API communication and networking layer
 */

// Mock dependencies first
jest.mock('@react-native-async-storage/async-storage', () => ({
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
}));

jest.mock('@react-native-community/netinfo', () => ({
    addEventListener: jest.fn(),
    fetch: jest.fn(() => Promise.resolve({
        isConnected: true,
        isInternetReachable: true,
        type: 'wifi',
    })),
}));

jest.mock('axios', () => ({
    create: jest.fn(() => ({
        get: jest.fn(),
        post: jest.fn(),
        put: jest.fn(),
        delete: jest.fn(),
        interceptors: {
            request: { use: jest.fn() },
            response: { use: jest.fn() },
        },
        defaults: {
            baseURL: 'http://localhost:8000/api/v1',
        },
    })),
}));

import { apiService } from '@/services/api';
import { uploadService } from '@/services/uploadService';
import { networkService } from '@/services/networkService';
import { offlineStorage } from '@/services/offlineStorage';
import { syncService } from '@/services/syncService';
import { MealImage, MealAnalysis, NutritionFeedback } from '@/types';

describe('API Integration Tests', () => {
    const mockMealImage: MealImage = {
        uri: 'file://test-image.jpg',
        type: 'image/jpeg',
        fileName: 'test-meal.jpg',
        fileSize: 1024000,
    };

    const mockMealAnalysis: MealAnalysis = {
        id: 'meal-123',
        studentId: 'student-456',
        imagePath: '/uploads/meal-123.jpg',
        uploadDate: '2024-01-15T10:30:00Z',
        analysisStatus: 'completed',
        detectedFoods: [
            {
                foodName: 'Jollof Rice',
                confidence: 0.95,
                foodClass: 'carbohydrates',
                boundingBox: { x: 10, y: 10, width: 100, height: 100 },
            },
            {
                foodName: 'Chicken',
                confidence: 0.88,
                foodClass: 'proteins',
            },
        ],
    };

    const mockFeedback: NutritionFeedback = {
        mealId: 'meal-123',
        detectedFoods: mockMealAnalysis.detectedFoods,
        missingFoodGroups: ['vitamins', 'minerals'],
        recommendations: [
            'Add some vegetables like ugwu or spinach for vitamins',
            'Include fruits for additional minerals',
        ],
        overallBalanceScore: 0.7,
        feedbackMessage: 'Good protein and carbohydrate balance! Consider adding vegetables.',
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('Network Service', () => {
        it('should detect network connectivity changes', async () => {
            const mockNetInfo = require('@react-native-community/netinfo');
            const mockListener = jest.fn();

            // Mock initial offline state
            mockNetInfo.fetch.mockResolvedValue({
                isConnected: false,
                isInternetReachable: false,
                type: 'none',
            });

            const unsubscribe = networkService.addListener(mockListener);

            // Simulate network coming online
            const networkCallback = mockNetInfo.addEventListener.mock.calls[0][0];
            networkCallback({
                isConnected: true,
                isInternetReachable: true,
                type: 'wifi',
            });

            expect(mockListener).toHaveBeenCalledWith({
                isConnected: true,
                isInternetReachable: true,
                type: 'wifi',
            });

            unsubscribe();
        });

        it('should wait for connection with timeout', async () => {
            const mockNetInfo = require('@react-native-community/netinfo');

            // Mock offline state
            mockNetInfo.fetch.mockResolvedValue({
                isConnected: false,
                isInternetReachable: false,
                type: 'none',
            });

            // Test timeout
            const connectionPromise = networkService.waitForConnection(1000);
            const result = await connectionPromise;
            expect(result).toBe(false);
        });
    });

    describe('Offline Storage', () => {
        it('should store and retrieve pending uploads', async () => {
            const uploadId = await offlineStorage.addPendingUpload(mockMealImage);
            expect(uploadId).toBeDefined();

            const pendingUploads = await offlineStorage.getPendingUploads();
            expect(pendingUploads).toHaveLength(1);
            expect(pendingUploads[0].image).toEqual(mockMealImage);

            await offlineStorage.removePendingUpload(uploadId);
            const emptyUploads = await offlineStorage.getPendingUploads();
            expect(emptyUploads).toHaveLength(0);
        });

        it('should cache meal data with size limits', async () => {
            // Cache multiple meals
            for (let i = 0; i < 55; i++) {
                const meal = { ...mockMealAnalysis, id: `meal-${i}` };
                await offlineStorage.cacheMeal(meal);
            }

            const cachedMeals = await offlineStorage.getCachedMeals();
            expect(cachedMeals.length).toBeLessThanOrEqual(50); // Max cache size
        });

        it('should manage sync queue items', async () => {
            await offlineStorage.addToSyncQueue('meal_upload', { image: mockMealImage });

            const syncQueue = await offlineStorage.getSyncQueue();
            expect(syncQueue).toHaveLength(1);
            expect(syncQueue[0].type).toBe('meal_upload');

            await offlineStorage.removeFromSyncQueue(syncQueue[0].id);
            const emptySyncQueue = await offlineStorage.getSyncQueue();
            expect(emptySyncQueue).toHaveLength(0);
        });
    });

    describe('Upload Service', () => {
        it('should handle offline upload by queuing', async () => {
            // Mock offline state
            jest.spyOn(networkService, 'isOnline').mockReturnValue(false);

            const progressCallback = jest.fn();

            try {
                await uploadService.uploadMealImage(mockMealImage, {
                    onProgress: progressCallback,
                });
            } catch (error) {
                expect(error.errorCode).toBe('OFFLINE');
                expect(progressCallback).toHaveBeenCalledWith(
                    expect.objectContaining({
                        status: 'pending',
                        error: expect.objectContaining({
                            errorCode: 'OFFLINE',
                        }),
                    })
                );
            }
        });

        it('should track upload progress', async () => {
            // Mock online state
            jest.spyOn(networkService, 'isOnline').mockReturnValue(true);

            const progressCallback = jest.fn();
            const mockXHR = {
                upload: { addEventListener: jest.fn() },
                addEventListener: jest.fn(),
                open: jest.fn(),
                send: jest.fn(),
                setRequestHeader: jest.fn(),
                status: 200,
                responseText: JSON.stringify({ mealId: 'meal-123' }),
            };

            // Mock XMLHttpRequest
            global.XMLHttpRequest = jest.fn(() => mockXHR) as any;

            // Mock API response for analysis polling
            jest.spyOn(apiService, 'get').mockResolvedValue(mockMealAnalysis);

            const uploadPromise = uploadService.uploadMealImage(mockMealImage, {
                onProgress: progressCallback,
            });

            // Simulate successful upload
            const loadHandler = mockXHR.addEventListener.mock.calls.find(
                call => call[0] === 'load'
            )[1];
            loadHandler();

            await uploadPromise;

            expect(progressCallback).toHaveBeenCalledWith(
                expect.objectContaining({
                    status: 'uploading',
                    progress: expect.any(Number),
                })
            );
        });

        it('should retry failed uploads with exponential backoff', async () => {
            jest.spyOn(networkService, 'isOnline').mockReturnValue(true);

            const mockXHR = {
                upload: { addEventListener: jest.fn() },
                addEventListener: jest.fn(),
                open: jest.fn(),
                send: jest.fn(),
                setRequestHeader: jest.fn(),
                status: 500,
            };

            global.XMLHttpRequest = jest.fn(() => mockXHR) as any;

            const progressCallback = jest.fn();

            try {
                await uploadService.uploadMealImage(mockMealImage, {
                    onProgress: progressCallback,
                    maxRetries: 2,
                });
            } catch (error) {
                expect(error.errorCode).toBe('HTTP_ERROR');
            }

            // Should have attempted multiple times
            expect(mockXHR.send).toHaveBeenCalledTimes(3); // Initial + 2 retries
        });
    });

    describe('API Service with Offline Support', () => {
        it('should return cached data when offline', async () => {
            jest.spyOn(networkService, 'isOnline').mockReturnValue(false);

            // Pre-cache some data
            await offlineStorage.cacheMeal(mockMealAnalysis, mockFeedback);

            const history = await apiService.getMealHistory();
            expect(history.meals).toHaveLength(1);
            expect(history.meals[0].id).toBe('meal-123');
        });

        it('should cache successful API responses', async () => {
            jest.spyOn(networkService, 'isOnline').mockReturnValue(true);
            jest.spyOn(apiService, 'get').mockResolvedValue(mockFeedback);

            const feedback = await apiService.getMealFeedback('meal-123');
            expect(feedback).toEqual(mockFeedback);

            // Verify caching occurred
            const cachedMeal = await offlineStorage.getCachedMeal('meal-123');
            expect(cachedMeal?.feedback).toEqual(mockFeedback);
        });

        it('should handle network errors gracefully', async () => {
            jest.spyOn(networkService, 'isOnline').mockReturnValue(true);
            jest.spyOn(apiService, 'get').mockRejectedValue({
                errorCode: 'NETWORK_ERROR',
                errorMessage: 'Network failed',
            });

            // Pre-cache data
            await offlineStorage.cacheMeal(mockMealAnalysis, mockFeedback);

            // Should fallback to cached data
            const feedback = await apiService.getMealFeedback('meal-123');
            expect(feedback).toEqual(mockFeedback);
        });
    });

    describe('Sync Service', () => {
        it('should sync pending uploads when online', async () => {
            jest.spyOn(networkService, 'isOnline').mockReturnValue(true);
            jest.spyOn(uploadService, 'processPendingUploads').mockResolvedValue();

            await syncService.performSync();

            expect(uploadService.processPendingUploads).toHaveBeenCalled();
        });

        it('should handle sync errors gracefully', async () => {
            jest.spyOn(networkService, 'isOnline').mockReturnValue(true);
            jest.spyOn(uploadService, 'processPendingUploads').mockRejectedValue(
                new Error('Sync failed')
            );

            await syncService.performSync();

            const status = syncService.getSyncStatus();
            expect(status.errors).toHaveLength(1);
        });

        it('should notify listeners of sync status changes', async () => {
            const statusListener = jest.fn();
            const unsubscribe = syncService.addSyncListener(statusListener);

            jest.spyOn(networkService, 'isOnline').mockReturnValue(true);
            jest.spyOn(uploadService, 'processPendingUploads').mockResolvedValue();

            await syncService.performSync();

            expect(statusListener).toHaveBeenCalledWith(
                expect.objectContaining({
                    isRunning: expect.any(Boolean),
                    lastSync: expect.any(String),
                })
            );

            unsubscribe();
        });
    });

    describe('End-to-End Workflow', () => {
        it('should handle complete offline-to-online meal upload workflow', async () => {
            // Start offline
            jest.spyOn(networkService, 'isOnline').mockReturnValue(false);

            // Attempt upload while offline
            try {
                await uploadService.uploadMealImage(mockMealImage);
            } catch (error) {
                expect(error.errorCode).toBe('OFFLINE');
            }

            // Verify upload was queued
            const pendingUploads = await offlineStorage.getPendingUploads();
            expect(pendingUploads).toHaveLength(1);

            // Come back online
            jest.spyOn(networkService, 'isOnline').mockReturnValue(true);
            jest.spyOn(uploadService, 'uploadMealImage').mockResolvedValue(mockMealAnalysis);

            // Process pending uploads
            await uploadService.processPendingUploads();

            // Verify upload was processed
            const remainingUploads = await offlineStorage.getPendingUploads();
            expect(remainingUploads).toHaveLength(0);
        });

        it('should maintain data consistency across offline/online transitions', async () => {
            // Cache some data while online
            jest.spyOn(networkService, 'isOnline').mockReturnValue(true);
            await offlineStorage.cacheMeal(mockMealAnalysis, mockFeedback);

            // Go offline and verify cached data is accessible
            jest.spyOn(networkService, 'isOnline').mockReturnValue(false);
            const history = await apiService.getMealHistory();
            expect(history.meals).toHaveLength(1);

            // Come back online and verify sync works
            jest.spyOn(networkService, 'isOnline').mockReturnValue(true);
            jest.spyOn(apiService, 'get').mockResolvedValue({
                meals: [mockMealAnalysis],
                totalCount: 1,
                hasMore: false,
            });

            const updatedHistory = await apiService.getMealHistory();
            expect(updatedHistory.meals).toHaveLength(1);
        });
    });
});