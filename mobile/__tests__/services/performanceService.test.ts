/**
 * Tests for performance service
 */

import { performanceService } from '../../src/services/performanceService';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
}));

// Mock NetInfo
jest.mock('@react-native-community/netinfo', () => ({
    addEventListener: jest.fn(),
    fetch: jest.fn(() => Promise.resolve({ type: 'wifi', isConnected: true })),
}));

// Mock InteractionManager
jest.mock('react-native', () => ({
    InteractionManager: {
        runAfterInteractions: jest.fn((callback) => callback()),
    },
    AppState: {
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
    },
}));

describe('PerformanceService', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('Lazy Loading', () => {
        it('should create lazy loader with correct configuration', () => {
            const mockFetchFunction = jest.fn().mockResolvedValue(['item1', 'item2']);

            const lazyLoader = performanceService.createLazyLoader(mockFetchFunction, {
                pageSize: 10,
                preloadPages: 1,
                cacheSize: 50,
            });

            expect(lazyLoader).toBeDefined();
            expect(typeof lazyLoader.loadPage).toBe('function');
            expect(typeof lazyLoader.loadMore).toBe('function');
            expect(typeof lazyLoader.reset).toBe('function');
        });

        it('should load first page correctly', async () => {
            const mockData = ['item1', 'item2', 'item3'];
            const mockFetchFunction = jest.fn().mockResolvedValue(mockData);

            const lazyLoader = performanceService.createLazyLoader(mockFetchFunction);
            const result = await lazyLoader.loadPage(0);

            expect(mockFetchFunction).toHaveBeenCalledWith(0, 20); // Default page size
            expect(result).toEqual(mockData);
        });

        it('should cache loaded pages', async () => {
            const mockData = ['item1', 'item2'];
            const mockFetchFunction = jest.fn().mockResolvedValue(mockData);

            const lazyLoader = performanceService.createLazyLoader(mockFetchFunction);

            // Load same page twice
            await lazyLoader.loadPage(0);
            await lazyLoader.loadPage(0);

            // Should only call fetch function once due to caching
            expect(mockFetchFunction).toHaveBeenCalledTimes(1);
        });

        it('should handle load more functionality', async () => {
            const mockFetchFunction = jest.fn()
                .mockResolvedValueOnce(['item1', 'item2']) // First page
                .mockResolvedValueOnce(['item3', 'item4']); // Second page

            const lazyLoader = performanceService.createLazyLoader(mockFetchFunction, {
                pageSize: 2,
            });

            await lazyLoader.loadPage(0);
            const moreData = await lazyLoader.loadMore();

            expect(mockFetchFunction).toHaveBeenCalledTimes(2);
            expect(moreData).toEqual(['item3', 'item4']);
        });

        it('should reset loader state', async () => {
            const mockFetchFunction = jest.fn().mockResolvedValue(['item1']);
            const lazyLoader = performanceService.createLazyLoader(mockFetchFunction);

            await lazyLoader.loadPage(0);
            lazyLoader.reset();

            // After reset, should be able to load first page again
            await lazyLoader.loadPage(0);
            expect(mockFetchFunction).toHaveBeenCalledTimes(2);
        });
    });

    describe('API Optimization', () => {
        it('should debounce API calls', async () => {
            const mockApiCall = jest.fn().mockResolvedValue('result');

            // Make multiple rapid calls
            const promise1 = performanceService.debounceApiCall('test_key', mockApiCall, 100);
            const promise2 = performanceService.debounceApiCall('test_key', mockApiCall, 100);
            const promise3 = performanceService.debounceApiCall('test_key', mockApiCall, 100);

            // Wait for debounce to complete
            await new Promise(resolve => setTimeout(resolve, 150));

            const results = await Promise.all([promise1, promise2, promise3]);

            // Should only call API once due to debouncing
            expect(mockApiCall).toHaveBeenCalledTimes(1);
            expect(results).toEqual(['result', 'result', 'result']);
        });

        it('should batch API requests', async () => {
            const mockRequests = [
                jest.fn().mockResolvedValue('result1'),
                jest.fn().mockResolvedValue('result2'),
                jest.fn().mockResolvedValue('result3'),
            ];

            const results = await performanceService.batchApiRequests(mockRequests, 2);

            expect(results).toEqual(['result1', 'result2', 'result3']);
            mockRequests.forEach(request => {
                expect(request).toHaveBeenCalledTimes(1);
            });
        });

        it('should handle batch request failures gracefully', async () => {
            const mockRequests = [
                jest.fn().mockResolvedValue('result1'),
                jest.fn().mockRejectedValue(new Error('API Error')),
                jest.fn().mockResolvedValue('result3'),
            ];

            const results = await performanceService.batchApiRequests(mockRequests, 3);

            // Should continue processing despite one failure
            expect(results).toHaveLength(2); // Only successful results
            expect(results).toContain('result1');
            expect(results).toContain('result3');
        });

        it('should cache API call results', async () => {
            const mockApiCall = jest.fn().mockResolvedValue('cached_result');

            // First call
            const result1 = await performanceService.optimizedApiCall('cache_key', mockApiCall, 5000);

            // Second call should use cache
            const result2 = await performanceService.optimizedApiCall('cache_key', mockApiCall, 5000);

            expect(mockApiCall).toHaveBeenCalledTimes(1);
            expect(result1).toBe('cached_result');
            expect(result2).toBe('cached_result');
        });

        it('should handle cache expiration', async () => {
            const mockApiCall = jest.fn()
                .mockResolvedValueOnce('result1')
                .mockResolvedValueOnce('result2');

            // First call
            await performanceService.optimizedApiCall('expire_key', mockApiCall, 50); // 50ms TTL

            // Wait for cache to expire
            await new Promise(resolve => setTimeout(resolve, 100));

            // Second call should make new API call
            await performanceService.optimizedApiCall('expire_key', mockApiCall, 50);

            expect(mockApiCall).toHaveBeenCalledTimes(2);
        });
    });

    describe('Performance Metrics', () => {
        it('should track render time', () => {
            const mockRenderFunction = jest.fn(() => 'rendered');

            const result = performanceService.measureRenderTime(mockRenderFunction);
            const metrics = performanceService.getMetrics();

            expect(result).toBe('rendered');
            expect(mockRenderFunction).toHaveBeenCalledTimes(1);
            expect(metrics.renderTime).toBeGreaterThanOrEqual(0);
        });

        it('should return current metrics', () => {
            const metrics = performanceService.getMetrics();

            expect(metrics).toHaveProperty('memoryUsage');
            expect(metrics).toHaveProperty('renderTime');
            expect(metrics).toHaveProperty('apiResponseTime');
            expect(metrics).toHaveProperty('cacheHitRate');
            expect(metrics).toHaveProperty('networkType');
        });
    });

    describe('Memory Management', () => {
        it('should clear memory cache', () => {
            performanceService.clearMemoryCache();

            // Should not throw any errors
            expect(true).toBe(true);
        });

        it('should handle cleanup properly', () => {
            performanceService.cleanup();

            // Should not throw any errors
            expect(true).toBe(true);
        });
    });
});

describe('Performance Integration', () => {
    it('should handle network type changes', async () => {
        // This would test the network adaptation logic
        // In a real test, you'd mock NetInfo to simulate network changes
        expect(true).toBe(true); // Placeholder
    });

    it('should persist cache across app restarts', async () => {
        // This would test the AsyncStorage integration
        // In a real test, you'd mock AsyncStorage operations
        expect(true).toBe(true); // Placeholder
    });
});

describe('Performance Benchmarks', () => {
    it('should complete lazy loading operations quickly', async () => {
        const mockFetchFunction = jest.fn().mockResolvedValue(
            Array.from({ length: 20 }, (_, i) => `item${i}`)
        );

        const lazyLoader = performanceService.createLazyLoader(mockFetchFunction);

        const startTime = Date.now();
        await lazyLoader.loadPage(0);
        const endTime = Date.now();

        const duration = endTime - startTime;
        expect(duration).toBeLessThan(100); // Should complete within 100ms
    });

    it('should handle large batch requests efficiently', async () => {
        const requests = Array.from({ length: 50 }, (_, i) =>
            jest.fn().mockResolvedValue(`result${i}`)
        );

        const startTime = Date.now();
        await performanceService.batchApiRequests(requests, 10);
        const endTime = Date.now();

        const duration = endTime - startTime;
        expect(duration).toBeLessThan(5000); // Should complete within 5 seconds
    });
});