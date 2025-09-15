/**
 * Performance optimization service for mobile app
 * Handles lazy loading, memory management, and API optimization
 */

import { InteractionManager, AppState } from 'react-native';
import NetInfo from '@react-native-community/netinfo';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface PerformanceMetrics {
    memoryUsage: number;
    renderTime: number;
    apiResponseTime: number;
    cacheHitRate: number;
    networkType: string;
}

export interface LazyLoadConfig {
    pageSize: number;
    preloadPages: number;
    cacheSize: number;
}

export interface APIOptimizationConfig {
    maxRetries: number;
    retryDelay: number;
    timeout: number;
    batchSize: number;
    debounceDelay: number;
}

class PerformanceService {
    private metrics: PerformanceMetrics = {
        memoryUsage: 0,
        renderTime: 0,
        apiResponseTime: 0,
        cacheHitRate: 0,
        networkType: 'unknown',
    };

    private lazyLoadConfig: LazyLoadConfig = {
        pageSize: 20,
        preloadPages: 2,
        cacheSize: 100,
    };

    private apiConfig: APIOptimizationConfig = {
        maxRetries: 3,
        retryDelay: 1000,
        timeout: 10000,
        batchSize: 5,
        debounceDelay: 300,
    };

    private cache = new Map<string, any>();
    private pendingRequests = new Map<string, Promise<any>>();
    private debounceTimers = new Map<string, NodeJS.Timeout>();

    /**
     * Initialize performance monitoring
     */
    async initialize(): Promise<void> {
        // Monitor network changes
        NetInfo.addEventListener(state => {
            this.metrics.networkType = state.type;
            this.adjustConfigForNetwork(state.type);
        });

        // Monitor app state changes
        AppState.addEventListener('change', this.handleAppStateChange);

        // Initialize cache from storage
        await this.loadCacheFromStorage();
    }

    /**
     * Adjust configuration based on network type
     */
    private adjustConfigForNetwork(networkType: string): void {
        switch (networkType) {
            case 'wifi':
                this.apiConfig.timeout = 10000;
                this.lazyLoadConfig.pageSize = 20;
                break;
            case 'cellular':
                this.apiConfig.timeout = 15000;
                this.lazyLoadConfig.pageSize = 15;
                break;
            case 'none':
                this.apiConfig.timeout = 5000;
                this.lazyLoadConfig.pageSize = 10;
                break;
            default:
                // Use default values
                break;
        }
    }

    /**
     * Handle app state changes for memory management
     */
    private handleAppStateChange = (nextAppState: string): void => {
        if (nextAppState === 'background') {
            this.clearMemoryCache();
            this.saveCacheToStorage();
        } else if (nextAppState === 'active') {
            this.loadCacheFromStorage();
        }
    };

    /**
     * Lazy loading implementation for lists
     */
    createLazyLoader<T>(
        fetchFunction: (page: number, pageSize: number) => Promise<T[]>,
        config?: Partial<LazyLoadConfig>
    ) {
        const settings = { ...this.lazyLoadConfig, ...config };
        let currentPage = 0;
        let isLoading = false;
        let hasMore = true;
        const cache = new Map<number, T[]>();

        return {
            async loadPage(page: number = currentPage): Promise<T[]> {
                if (cache.has(page)) {
                    return cache.get(page)!;
                }

                if (isLoading) {
                    return [];
                }

                isLoading = true;
                try {
                    const startTime = Date.now();
                    const data = await fetchFunction(page, settings.pageSize);
                    const loadTime = Date.now() - startTime;

                    // Update metrics
                    this.updateApiResponseTime(loadTime);

                    // Cache the data
                    cache.set(page, data);

                    // Manage cache size
                    if (cache.size > settings.cacheSize) {
                        const oldestKey = Math.min(...cache.keys());
                        cache.delete(oldestKey);
                    }

                    // Preload next pages
                    this.preloadPages(fetchFunction, page + 1, settings);

                    hasMore = data.length === settings.pageSize;
                    currentPage = page + 1;

                    return data;
                } finally {
                    isLoading = false;
                }
            },

            async loadMore(): Promise<T[]> {
                if (!hasMore || isLoading) {
                    return [];
                }
                return this.loadPage(currentPage);
            },

            reset(): void {
                currentPage = 0;
                hasMore = true;
                cache.clear();
            },

            getCachedData(): T[] {
                const allData: T[] = [];
                for (let i = 0; i < currentPage; i++) {
                    const pageData = cache.get(i);
                    if (pageData) {
                        allData.push(...pageData);
                    }
                }
                return allData;
            }
        };
    }

    /**
     * Preload pages in background
     */
    private async preloadPages<T>(
        fetchFunction: (page: number, pageSize: number) => Promise<T[]>,
        startPage: number,
        config: LazyLoadConfig
    ): Promise<void> {
        InteractionManager.runAfterInteractions(() => {
            for (let i = 0; i < config.preloadPages; i++) {
                const page = startPage + i;
                setTimeout(() => {
                    fetchFunction(page, config.pageSize).catch(() => {
                        // Ignore preload errors
                    });
                }, i * 100); // Stagger requests
            }
        });
    }

    /**
     * Debounced API calls to reduce unnecessary requests
     */
    debounceApiCall<T>(
        key: string,
        apiCall: () => Promise<T>,
        delay: number = this.apiConfig.debounceDelay
    ): Promise<T> {
        return new Promise((resolve, reject) => {
            // Clear existing timer
            const existingTimer = this.debounceTimers.get(key);
            if (existingTimer) {
                clearTimeout(existingTimer);
            }

            // Set new timer
            const timer = setTimeout(async () => {
                try {
                    const result = await apiCall();
                    resolve(result);
                } catch (error) {
                    reject(error);
                } finally {
                    this.debounceTimers.delete(key);
                }
            }, delay);

            this.debounceTimers.set(key, timer);
        });
    }

    /**
     * Batch API requests to reduce network calls
     */
    async batchApiRequests<T>(
        requests: Array<() => Promise<T>>,
        batchSize: number = this.apiConfig.batchSize
    ): Promise<T[]> {
        const results: T[] = [];

        for (let i = 0; i < requests.length; i += batchSize) {
            const batch = requests.slice(i, i + batchSize);
            const batchPromises = batch.map(request => request());

            try {
                const batchResults = await Promise.all(batchPromises);
                results.push(...batchResults);
            } catch (error) {
                console.error('Batch request failed:', error);
                // Continue with next batch
            }

            // Add delay between batches to avoid overwhelming the server
            if (i + batchSize < requests.length) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        }

        return results;
    }

    /**
     * Optimized API call with caching and deduplication
     */
    async optimizedApiCall<T>(
        key: string,
        apiCall: () => Promise<T>,
        cacheTTL: number = 5 * 60 * 1000 // 5 minutes
    ): Promise<T> {
        // Check cache first
        const cached = this.getFromCache(key);
        if (cached && Date.now() - cached.timestamp < cacheTTL) {
            this.updateCacheHitRate(true);
            return cached.data;
        }

        // Check if request is already pending
        const pendingRequest = this.pendingRequests.get(key);
        if (pendingRequest) {
            return pendingRequest;
        }

        // Make new request
        const requestPromise = this.makeApiCallWithRetry(apiCall);
        this.pendingRequests.set(key, requestPromise);

        try {
            const result = await requestPromise;

            // Cache the result
            this.setCache(key, result);
            this.updateCacheHitRate(false);

            return result;
        } finally {
            this.pendingRequests.delete(key);
        }
    }

    /**
     * API call with retry logic
     */
    private async makeApiCallWithRetry<T>(
        apiCall: () => Promise<T>,
        retries: number = this.apiConfig.maxRetries
    ): Promise<T> {
        const startTime = Date.now();

        try {
            const result = await Promise.race([
                apiCall(),
                new Promise<never>((_, reject) =>
                    setTimeout(() => reject(new Error('Request timeout')), this.apiConfig.timeout)
                )
            ]);

            this.updateApiResponseTime(Date.now() - startTime);
            return result;
        } catch (error) {
            if (retries > 0) {
                await new Promise(resolve => setTimeout(resolve, this.apiConfig.retryDelay));
                return this.makeApiCallWithRetry(apiCall, retries - 1);
            }
            throw error;
        }
    }

    /**
     * Memory management utilities
     */
    clearMemoryCache(): void {
        this.cache.clear();
        this.pendingRequests.clear();

        // Clear debounce timers
        this.debounceTimers.forEach(timer => clearTimeout(timer));
        this.debounceTimers.clear();
    }

    /**
     * Cache management
     */
    private setCache(key: string, data: any): void {
        this.cache.set(key, {
            data,
            timestamp: Date.now(),
        });

        // Limit cache size
        if (this.cache.size > 100) {
            const oldestKey = this.cache.keys().next().value;
            this.cache.delete(oldestKey);
        }
    }

    private getFromCache(key: string): { data: any; timestamp: number } | null {
        return this.cache.get(key) || null;
    }

    /**
     * Persistent cache for offline support
     */
    private async saveCacheToStorage(): Promise<void> {
        try {
            const cacheData = Array.from(this.cache.entries());
            await AsyncStorage.setItem('performance_cache', JSON.stringify(cacheData));
        } catch (error) {
            console.error('Failed to save cache to storage:', error);
        }
    }

    private async loadCacheFromStorage(): Promise<void> {
        try {
            const cacheData = await AsyncStorage.getItem('performance_cache');
            if (cacheData) {
                const entries = JSON.parse(cacheData);
                this.cache = new Map(entries);
            }
        } catch (error) {
            console.error('Failed to load cache from storage:', error);
        }
    }

    /**
     * Performance metrics tracking
     */
    private updateApiResponseTime(time: number): void {
        this.metrics.apiResponseTime = (this.metrics.apiResponseTime + time) / 2;
    }

    private updateCacheHitRate(isHit: boolean): void {
        const currentRate = this.metrics.cacheHitRate;
        this.metrics.cacheHitRate = isHit ?
            (currentRate + 1) / 2 :
            currentRate * 0.9;
    }

    /**
     * Get current performance metrics
     */
    getMetrics(): PerformanceMetrics {
        return { ...this.metrics };
    }

    /**
     * Performance monitoring for render times
     */
    measureRenderTime<T>(renderFunction: () => T): T {
        const startTime = Date.now();
        const result = renderFunction();
        const renderTime = Date.now() - startTime;

        this.metrics.renderTime = (this.metrics.renderTime + renderTime) / 2;

        return result;
    }

    /**
     * Cleanup resources
     */
    cleanup(): void {
        this.clearMemoryCache();
        AppState.removeEventListener('change', this.handleAppStateChange);
    }
}

export const performanceService = new PerformanceService();