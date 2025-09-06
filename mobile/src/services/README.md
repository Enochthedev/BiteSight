# Networking and API Integration Layer

This directory contains the comprehensive networking layer for the React Native mobile application, providing robust offline support, automatic synchronization, and progress tracking for API communications.

## Services Overview

### 1. Network Service (`networkService.ts`)

Monitors network connectivity and provides real-time network status updates.

**Key Features:**

- Real-time network connectivity monitoring
- Online/offline status detection
- Network state change listeners
- Connection waiting with timeout

**Usage:**

```typescript
import { networkService } from "@/services";

// Check current network status
const isOnline = networkService.isOnline();

// Listen for network changes
const unsubscribe = networkService.addListener((state) => {
  console.log("Network state:", state);
});

// Wait for connection with timeout
const connected = await networkService.waitForConnection(5000);
```

### 2. Offline Storage Service (`offlineStorage.ts`)

Manages local data caching and offline storage with automatic cleanup.

**Key Features:**

- Pending upload queue management
- Meal data caching with size limits
- Sync queue for failed operations
- Weekly insights caching
- Automatic cache cleanup

**Usage:**

```typescript
import { offlineStorage } from "@/services";

// Add pending upload
const uploadId = await offlineStorage.addPendingUpload(imageData);

// Cache meal data
await offlineStorage.cacheMeal(mealAnalysis, feedback);

// Get cached meals
const cachedMeals = await offlineStorage.getCachedMeals();
```

### 3. Upload Service (`uploadService.ts`)

Handles image uploads with progress tracking, retry logic, and offline queuing.

**Key Features:**

- Progress tracking with callbacks
- Automatic retry with exponential backoff
- Offline upload queuing
- Upload cancellation support
- Analysis status polling

**Usage:**

```typescript
import { uploadService } from "@/services";

// Upload with progress tracking
const analysis = await uploadService.uploadMealImage(imageData, {
  onProgress: (progress) => {
    console.log(`Upload progress: ${progress.progress}%`);
  },
  maxRetries: 3,
});

// Cancel upload
uploadService.cancelUpload(uploadId);
```

### 4. Sync Service (`syncService.ts`)

Coordinates data synchronization between offline and online states.

**Key Features:**

- Automatic sync when network becomes available
- Periodic background sync
- Sync status monitoring
- Error handling and retry logic
- Manual sync triggering

**Usage:**

```typescript
import { syncService } from "@/services";

// Listen for sync status changes
const unsubscribe = syncService.addSyncListener((status) => {
  console.log("Sync status:", status);
});

// Force sync now
await syncService.forceSyncNow();

// Get current sync status
const status = syncService.getSyncStatus();
```

### 5. Enhanced API Service (`api.ts`)

Extended API client with offline support and intelligent caching.

**Key Features:**

- Automatic offline fallback to cached data
- Request retry queue for offline scenarios
- Enhanced error handling
- Specific methods for meal history, feedback, and insights

**Usage:**

```typescript
import { apiService } from "@/services";

// Get meal history with offline support
const history = await apiService.getMealHistory(20, 0);

// Get feedback with caching
const feedback = await apiService.getMealFeedback(mealId);

// Post with retry on offline
const result = await apiService.postWithRetry("/endpoint", data);
```

## React Hook Integration

### useNetworkSync Hook (`hooks/useNetworkSync.ts`)

React hook that provides network and sync state management.

**Features:**

- Network state monitoring
- Sync status tracking
- Pending items count
- Action methods for sync operations

**Usage:**

```typescript
import { useNetworkSync } from "@/hooks";

const MyComponent = () => {
  const [
    { networkState, syncStatus, pendingItemsCount, isOnline },
    { forceSyncNow, clearSyncErrors, retryFailedUploads },
  ] = useNetworkSync();

  return (
    <View>
      <Text>Status: {isOnline ? "Online" : "Offline"}</Text>
      <Text>Pending: {pendingItemsCount}</Text>
      {syncStatus.errors.length > 0 && (
        <Button onPress={clearSyncErrors}>Clear Errors</Button>
      )}
    </View>
  );
};
```

## Components

### NetworkStatus Component (`components/NetworkStatus.tsx`)

Ready-to-use component that displays network status and sync information.

**Features:**

- Visual network status indicator
- Pending items count display
- Retry button for failed syncs
- Real-time status updates

## Error Handling

The networking layer provides comprehensive error handling with structured error responses:

```typescript
interface ApiError {
  errorCode: string;
  errorMessage: string;
  userMessage: string;
  retryPossible: boolean;
  suggestedActions: string[];
  timestamp: string;
}
```

**Common Error Codes:**

- `OFFLINE`: No internet connection
- `NETWORK_ERROR`: Network communication failed
- `TIMEOUT`: Request timeout
- `HTTP_ERROR`: HTTP status error
- `ANALYSIS_FAILED`: Meal analysis failed
- `UPLOAD_SYNC_ERROR`: Upload synchronization failed

## Offline Capabilities

### Data Persistence

- Meal images and metadata cached locally
- Failed uploads queued for retry
- API responses cached for offline access
- Weekly insights stored locally

### Sync Strategies

- **Immediate Sync**: When network becomes available
- **Periodic Sync**: Every 5 minutes when online
- **Manual Sync**: User-triggered sync operations
- **Retry Logic**: Exponential backoff for failed operations

### Cache Management

- Automatic cleanup of old cached data
- Size-limited caches to prevent storage bloat
- Cache invalidation strategies
- Manual cache clearing options

## Performance Optimizations

### Upload Optimization

- Image compression before upload
- Progress tracking for user feedback
- Chunked upload support for large files
- Concurrent upload limiting

### Network Efficiency

- Request deduplication
- Response caching
- Batch operations where possible
- Intelligent retry strategies

### Memory Management

- Lazy loading of cached data
- Automatic cleanup of old entries
- Memory-efficient data structures
- Garbage collection friendly patterns

## Testing

The networking layer includes comprehensive integration tests covering:

- Network state management
- Offline storage operations
- Upload progress tracking
- Error handling scenarios
- Cache management
- Offline-to-online transitions

Run tests with:

```bash
npm test -- __tests__/services/networkingIntegration.test.ts
```

## Configuration

### Network Timeouts

- Default request timeout: 30 seconds
- Upload timeout: 60 seconds
- Sync retry interval: 2 seconds
- Connection wait timeout: 10 seconds

### Cache Limits

- Maximum cached meals: 50
- Maximum retry attempts: 3
- Cache cleanup interval: 7 days
- Sync queue size limit: 100 items

### Retry Policies

- Exponential backoff: 2^attempt \* 1000ms
- Maximum retry delay: 30 seconds
- Retry on network errors: Yes
- Retry on server errors (5xx): Yes
- Retry on client errors (4xx): No

## Best Practices

### Service Usage

1. Always check network status before critical operations
2. Provide user feedback for long-running operations
3. Handle offline scenarios gracefully
4. Use appropriate error messages for different scenarios

### Performance

1. Cache frequently accessed data
2. Implement proper loading states
3. Use progress indicators for uploads
4. Batch operations when possible

### Error Handling

1. Provide meaningful error messages to users
2. Implement retry logic for transient failures
3. Log errors for debugging purposes
4. Gracefully degrade functionality when offline

### Testing

1. Test offline scenarios thoroughly
2. Verify error handling paths
3. Test network state transitions
4. Validate cache behavior

## Dependencies

- `@react-native-async-storage/async-storage`: Local storage
- `@react-native-community/netinfo`: Network monitoring
- `axios`: HTTP client
- `react`: React hooks and components

## Future Enhancements

- WebSocket support for real-time updates
- Background sync using background tasks
- Advanced caching strategies (LRU, TTL)
- Compression for cached data
- Metrics and analytics integration
- Push notification integration for sync status
