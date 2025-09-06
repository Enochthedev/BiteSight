/**
 * Image upload service with progress tracking and retry logic
 */

import { MealImage, MealAnalysis, ApiError } from '@/types';
import { apiService } from './api';
import { networkService } from './networkService';
import { offlineStorage } from './offlineStorage';

export interface UploadProgress {
    uploadId: string;
    progress: number; // 0-100
    status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed';
    error?: ApiError;
}

export interface UploadOptions {
    onProgress?: (progress: UploadProgress) => void;
    retryOnFailure?: boolean;
    maxRetries?: number;
}

export class UploadService {
    private static instance: UploadService;
    private activeUploads: Map<string, AbortController> = new Map();
    private uploadListeners: Map<string, (progress: UploadProgress) => void> = new Map();

    private constructor() { }

    public static getInstance(): UploadService {
        if (!UploadService.instance) {
            UploadService.instance = new UploadService();
        }
        return UploadService.instance;
    }

    public async uploadMealImage(
        image: MealImage,
        options: UploadOptions = {}
    ): Promise<MealAnalysis> {
        const { onProgress, retryOnFailure = true, maxRetries = 3 } = options;

        // Check network connectivity
        if (!networkService.isOnline()) {
            // Store for offline upload
            const uploadId = await offlineStorage.addPendingUpload(image);

            const error: ApiError = {
                errorCode: 'OFFLINE',
                errorMessage: 'No internet connection',
                userMessage: 'Your meal has been saved and will be uploaded when you\'re back online.',
                retryPossible: true,
                suggestedActions: ['Check your internet connection'],
                timestamp: new Date().toISOString(),
            };

            if (onProgress) {
                onProgress({
                    uploadId,
                    progress: 0,
                    status: 'pending',
                    error,
                });
            }

            throw error;
        }

        const uploadId = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const abortController = new AbortController();
        this.activeUploads.set(uploadId, abortController);

        if (onProgress) {
            this.uploadListeners.set(uploadId, onProgress);
        }

        try {
            return await this.performUpload(uploadId, image, maxRetries);
        } finally {
            this.activeUploads.delete(uploadId);
            this.uploadListeners.delete(uploadId);
        }
    }

    private async performUpload(
        uploadId: string,
        image: MealImage,
        maxRetries: number,
        currentRetry: number = 0
    ): Promise<MealAnalysis> {
        const progressCallback = this.uploadListeners.get(uploadId);

        try {
            // Update progress: Starting upload
            if (progressCallback) {
                progressCallback({
                    uploadId,
                    progress: 10,
                    status: 'uploading',
                });
            }

            // Prepare form data
            const formData = new FormData();
            formData.append('image', {
                uri: image.uri,
                type: image.type,
                name: image.fileName,
            } as any);

            // Update progress: Uploading
            if (progressCallback) {
                progressCallback({
                    uploadId,
                    progress: 30,
                    status: 'uploading',
                });
            }

            // Upload image
            const uploadResponse = await this.uploadWithProgress(
                '/meals/upload',
                formData,
                uploadId,
                progressCallback
            );

            // Update progress: Processing
            if (progressCallback) {
                progressCallback({
                    uploadId,
                    progress: 70,
                    status: 'processing',
                });
            }

            // Poll for analysis completion
            const analysis = await this.pollAnalysisStatus(
                uploadResponse.mealId,
                uploadId,
                progressCallback
            );

            // Cache the result
            await offlineStorage.cacheMeal(analysis);

            // Update progress: Completed
            if (progressCallback) {
                progressCallback({
                    uploadId,
                    progress: 100,
                    status: 'completed',
                });
            }

            return analysis;

        } catch (error) {
            const apiError = error as ApiError;

            // Retry logic
            if (apiError.retryPossible && currentRetry < maxRetries) {
                // Exponential backoff
                const delay = Math.pow(2, currentRetry) * 1000;
                await new Promise(resolve => setTimeout(resolve, delay));

                return this.performUpload(uploadId, image, maxRetries, currentRetry + 1);
            }

            // Update progress: Failed
            if (progressCallback) {
                progressCallback({
                    uploadId,
                    progress: 0,
                    status: 'failed',
                    error: apiError,
                });
            }

            throw apiError;
        }
    }

    private async uploadWithProgress(
        url: string,
        formData: FormData,
        uploadId: string,
        progressCallback?: (progress: UploadProgress) => void
    ): Promise<{ mealId: string }> {
        const abortController = this.activeUploads.get(uploadId);

        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            // Set up progress tracking
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable && progressCallback) {
                    const progress = Math.round((event.loaded / event.total) * 50) + 30; // 30-80%
                    progressCallback({
                        uploadId,
                        progress,
                        status: 'uploading',
                    });
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (error) {
                        reject({
                            errorCode: 'PARSE_ERROR',
                            errorMessage: 'Failed to parse response',
                            userMessage: 'Something went wrong. Please try again.',
                            retryPossible: true,
                            suggestedActions: ['Try again'],
                            timestamp: new Date().toISOString(),
                        });
                    }
                } else {
                    reject({
                        errorCode: 'HTTP_ERROR',
                        errorMessage: `HTTP ${xhr.status}`,
                        userMessage: 'Upload failed. Please try again.',
                        retryPossible: true,
                        suggestedActions: ['Try again', 'Check your internet connection'],
                        timestamp: new Date().toISOString(),
                    });
                }
            });

            xhr.addEventListener('error', () => {
                reject({
                    errorCode: 'NETWORK_ERROR',
                    errorMessage: 'Network error during upload',
                    userMessage: 'Upload failed due to network error. Please try again.',
                    retryPossible: true,
                    suggestedActions: ['Check your internet connection', 'Try again'],
                    timestamp: new Date().toISOString(),
                });
            });

            xhr.addEventListener('timeout', () => {
                reject({
                    errorCode: 'TIMEOUT',
                    errorMessage: 'Upload timeout',
                    userMessage: 'Upload took too long. Please try again.',
                    retryPossible: true,
                    suggestedActions: ['Try again', 'Check your internet connection'],
                    timestamp: new Date().toISOString(),
                });
            });

            // Handle abort
            if (abortController) {
                abortController.signal.addEventListener('abort', () => {
                    xhr.abort();
                    reject({
                        errorCode: 'CANCELLED',
                        errorMessage: 'Upload cancelled',
                        userMessage: 'Upload was cancelled.',
                        retryPossible: true,
                        suggestedActions: ['Try again'],
                        timestamp: new Date().toISOString(),
                    });
                });
            }

            // Configure and send request
            xhr.open('POST', `${apiService['client'].defaults.baseURL}${url}`);
            xhr.timeout = 60000; // 60 seconds timeout

            // Add auth header if available
            try {
                const AsyncStorage = require('@react-native-async-storage/async-storage').default;
                const token = await AsyncStorage.getItem('accessToken');
                if (token) {
                    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
                }
            } catch (error) {
                // Ignore auth header if AsyncStorage is not available (e.g., in tests)
            }

            xhr.send(formData);
        });
    }

    private async pollAnalysisStatus(
        mealId: string,
        uploadId: string,
        progressCallback?: (progress: UploadProgress) => void,
        maxAttempts: number = 30
    ): Promise<MealAnalysis> {
        let attempts = 0;
        const pollInterval = 2000; // 2 seconds

        while (attempts < maxAttempts) {
            try {
                const analysis: MealAnalysis = await apiService.get(`/meals/${mealId}/analysis`);

                if (analysis.analysisStatus === 'completed') {
                    return analysis;
                }

                if (analysis.analysisStatus === 'failed') {
                    throw {
                        errorCode: 'ANALYSIS_FAILED',
                        errorMessage: 'Meal analysis failed',
                        userMessage: 'We couldn\'t analyze your meal. Please try again with a clearer photo.',
                        retryPossible: true,
                        suggestedActions: ['Take a clearer photo', 'Ensure good lighting', 'Try again'],
                        timestamp: new Date().toISOString(),
                    };
                }

                // Update progress during processing
                if (progressCallback) {
                    const progress = 70 + Math.min(25, (attempts / maxAttempts) * 25);
                    progressCallback({
                        uploadId,
                        progress: Math.round(progress),
                        status: 'processing',
                    });
                }

                // Wait before next poll
                await new Promise(resolve => setTimeout(resolve, pollInterval));
                attempts++;

            } catch (error) {
                if (attempts === maxAttempts - 1) {
                    throw error;
                }
                attempts++;
                await new Promise(resolve => setTimeout(resolve, pollInterval));
            }
        }

        throw {
            errorCode: 'ANALYSIS_TIMEOUT',
            errorMessage: 'Analysis timeout',
            userMessage: 'Analysis is taking longer than expected. Please try again.',
            retryPossible: true,
            suggestedActions: ['Try again', 'Contact support if the problem persists'],
            timestamp: new Date().toISOString(),
        };
    }

    public cancelUpload(uploadId: string): void {
        const abortController = this.activeUploads.get(uploadId);
        if (abortController) {
            abortController.abort();
        }
    }

    public async processPendingUploads(): Promise<void> {
        if (!networkService.isOnline()) {
            return;
        }

        const pendingUploads = await offlineStorage.getPendingUploads();

        for (const upload of pendingUploads) {
            try {
                await this.uploadMealImage(upload.image, {
                    retryOnFailure: false, // Don't retry here, we'll handle it in the queue
                });

                await offlineStorage.removePendingUpload(upload.id);
            } catch (error) {
                await offlineStorage.incrementRetryCount(upload.id);
            }
        }
    }
}

export const uploadService = UploadService.getInstance();