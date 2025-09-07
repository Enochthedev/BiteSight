/**
 * Optimized upload service with compression, progress tracking, and retry logic
 */

import { cameraService, OptimizedImage } from './cameraService';
import { apiService } from './api';
import { networkService } from './networkService';
import { performanceService } from './performanceService';
import { MealImage } from '@/types';

export interface UploadProgress {
    loaded: number;
    total: number;
    percentage: number;
    speed: number; // bytes per second
    estimatedTimeRemaining: number; // seconds
}

export interface UploadOptions {
    compress: boolean;
    quality: number;
    maxWidth: number;
    maxHeight: number;
    retryAttempts: number;
    chunkSize?: number;
}

export interface UploadResult {
    success: boolean;
    imageId?: string;
    analysisId?: string;
    error?: string;
    compressionStats?: {
        originalSize: number;
        compressedSize: number;
        compressionRatio: number;
    };
}

class OptimizedUploadService {
    private defaultOptions: UploadOptions = {
        compress: true,
        quality: 80,
        maxWidth: 1024,
        maxHeight: 1024,
        retryAttempts: 3,
    };

    private activeUploads = new Map<string, AbortController>();
    private uploadQueue: Array<() => Promise<any>> = [];
    private isProcessingQueue = false;

    /**
     * Upload image with optimization and progress tracking
     */
    async uploadImage(
        image: MealImage,
        onProgress?: (progress: UploadProgress) => void,
        options?: Partial<UploadOptions>
    ): Promise<UploadResult> {
        const uploadOptions = { ...this.defaultOptions, ...options };
        const uploadId = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        try {
            // Optimize image based on network conditions
            const optimizedImage = await this.optimizeImageForUpload(image, uploadOptions);

            // Create abort controller for cancellation
            const abortController = new AbortController();
            this.activeUploads.set(uploadId, abortController);

            // Prepare form data
            const formData = new FormData();
            formData.append('image', {
                uri: optimizedImage.uri,
                type: optimizedImage.type,
                name: optimizedImage.fileName,
            } as any);

            // Track upload progress
            let startTime = Date.now();
            let lastLoaded = 0;

            const progressHandler = (progressEvent: any) => {
                const currentTime = Date.now();
                const timeElapsed = (currentTime - startTime) / 1000;
                const loaded = progressEvent.loaded || 0;
                const total = progressEvent.total || optimizedImage.compressedSize;

                const speed = timeElapsed > 0 ? (loaded - lastLoaded) / timeElapsed : 0;
                const estimatedTimeRemaining = speed > 0 ? (total - loaded) / speed : 0;

                const progress: UploadProgress = {
                    loaded,
                    total,
                    percentage: total > 0 ? Math.round((loaded / total) * 100) : 0,
                    speed,
                    estimatedTimeRemaining,
                };

                onProgress?.(progress);
                lastLoaded = loaded;
                startTime = currentTime;
            };

            // Perform upload with retry logic
            const result = await this.uploadWithRetry(
                formData,
                progressHandler,
                abortController.signal,
                uploadOptions.retryAttempts
            );

            return {
                success: true,
                imageId: result.imageId,
                analysisId: result.analysisId,
                compressionStats: {
                    originalSize: optimizedImage.originalSize || 0,
                    compressedSize: optimizedImage.compressedSize,
                    compressionRatio: optimizedImage.compressionRatio || 0,
                },
            };

        } catch (error) {
            console.error('Upload failed:', error);
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Upload failed',
            };
        } finally {
            this.activeUploads.delete(uploadId);
        }
    }

    /**
     * Optimize image for upload based on network conditions
     */
    private async optimizeImageForUpload(
        image: MealImage,
        options: UploadOptions
    ): Promise<OptimizedImage> {
        if (!options.compress) {
            return {
                ...image,
                compressedSize: image.fileSize || 0,
            };
        }

        // Get network type for optimization
        const networkState = await networkService.getNetworkState();
        let networkType: 'wifi' | 'cellular' | 'slow' = 'cellular';

        if (networkState.type === 'wifi') {
            networkType = 'wifi';
        } else if (networkState.type === 'cellular') {
            networkType = networkState.details?.cellularGeneration === '2g' ? 'slow' : 'cellular';
        }

        // Optimize based on network
        return cameraService.optimizeForNetwork(image, networkType);
    }

    /**
     * Upload with retry logic and exponential backoff
     */
    private async uploadWithRetry(
        formData: FormData,
        onProgress: (progress: any) => void,
        signal: AbortSignal,
        maxRetries: number
    ): Promise<any> {
        let lastError: Error | null = null;

        for (let attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                // Add delay for retries (exponential backoff)
                if (attempt > 0) {
                    const delay = Math.min(1000 * Math.pow(2, attempt - 1), 10000);
                    await new Promise(resolve => setTimeout(resolve, delay));
                }

                // Check if upload was cancelled
                if (signal.aborted) {
                    throw new Error('Upload cancelled');
                }

                // Perform the upload
                return await this.performUpload(formData, onProgress, signal);

            } catch (error) {
                lastError = error instanceof Error ? error : new Error('Upload failed');

                // Don't retry on certain errors
                if (this.isNonRetryableError(error)) {
                    throw lastError;
                }

                console.warn(`Upload attempt ${attempt + 1} failed:`, lastError.message);
            }
        }

        throw lastError || new Error('Upload failed after all retries');
    }

    /**
     * Perform the actual upload
     */
    private async performUpload(
        formData: FormData,
        onProgress: (progress: any) => void,
        signal: AbortSignal
    ): Promise<any> {
        // Use axios directly for better progress tracking
        const response = await apiService['client'].post('/meals/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            timeout: 60000,
            signal,
            onUploadProgress: onProgress,
        });

        return response.data;
    }

    /**
     * Check if error should not be retried
     */
    private isNonRetryableError(error: any): boolean {
        // Don't retry on client errors (4xx) or cancellation
        if (error.response?.status >= 400 && error.response?.status < 500) {
            return true;
        }

        if (error.message?.includes('cancelled') || error.message?.includes('aborted')) {
            return true;
        }

        return false;
    }

    /**
     * Batch upload multiple images
     */
    async batchUpload(
        images: MealImage[],
        onProgress?: (imageIndex: number, progress: UploadProgress) => void,
        options?: Partial<UploadOptions>
    ): Promise<UploadResult[]> {
        const results: UploadResult[] = [];

        // Process uploads in batches to avoid overwhelming the server
        const batchSize = 3;
        for (let i = 0; i < images.length; i += batchSize) {
            const batch = images.slice(i, i + batchSize);

            const batchPromises = batch.map((image, batchIndex) => {
                const imageIndex = i + batchIndex;
                return this.uploadImage(
                    image,
                    (progress) => onProgress?.(imageIndex, progress),
                    options
                );
            });

            const batchResults = await Promise.allSettled(batchPromises);

            batchResults.forEach((result) => {
                if (result.status === 'fulfilled') {
                    results.push(result.value);
                } else {
                    results.push({
                        success: false,
                        error: result.reason?.message || 'Upload failed',
                    });
                }
            });

            // Add delay between batches
            if (i + batchSize < images.length) {
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }

        return results;
    }

    /**
     * Queue upload for when network is available
     */
    async queueUpload(
        image: MealImage,
        options?: Partial<UploadOptions>
    ): Promise<void> {
        const uploadTask = () => this.uploadImage(image, undefined, options);
        this.uploadQueue.push(uploadTask);

        // Process queue if network is available
        if (networkService.isOnline()) {
            this.processUploadQueue();
        }
    }

    /**
     * Process queued uploads
     */
    private async processUploadQueue(): Promise<void> {
        if (this.isProcessingQueue || this.uploadQueue.length === 0) {
            return;
        }

        this.isProcessingQueue = true;

        try {
            while (this.uploadQueue.length > 0 && networkService.isOnline()) {
                const uploadTask = this.uploadQueue.shift();
                if (uploadTask) {
                    try {
                        await uploadTask();
                    } catch (error) {
                        console.error('Queued upload failed:', error);
                    }
                }

                // Add small delay between uploads
                await new Promise(resolve => setTimeout(resolve, 500));
            }
        } finally {
            this.isProcessingQueue = false;
        }
    }

    /**
     * Cancel upload by ID
     */
    cancelUpload(uploadId: string): boolean {
        const controller = this.activeUploads.get(uploadId);
        if (controller) {
            controller.abort();
            this.activeUploads.delete(uploadId);
            return true;
        }
        return false;
    }

    /**
     * Cancel all active uploads
     */
    cancelAllUploads(): void {
        this.activeUploads.forEach(controller => controller.abort());
        this.activeUploads.clear();
    }

    /**
     * Get upload statistics
     */
    getUploadStats(): {
        activeUploads: number;
        queuedUploads: number;
    } {
        return {
            activeUploads: this.activeUploads.size,
            queuedUploads: this.uploadQueue.length,
        };
    }

    /**
     * Initialize service and set up network listeners
     */
    initialize(): void {
        // Listen for network changes to process queue
        networkService.addListener((networkState) => {
            if (networkState.isConnected && networkState.isInternetReachable) {
                this.processUploadQueue();
            }
        });
    }

    /**
     * Cleanup resources
     */
    cleanup(): void {
        this.cancelAllUploads();
        this.uploadQueue.length = 0;
    }
}

export const optimizedUploadService = new OptimizedUploadService();