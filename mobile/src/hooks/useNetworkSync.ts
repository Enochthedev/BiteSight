/**
 * React hook for managing network status and synchronization
 */

import { useState, useEffect, useCallback } from 'react';
import { networkService, syncService, offlineStorage } from '@/services';
import { NetworkState, SyncStatus } from '@/types';

interface NetworkSyncState {
    networkState: NetworkState;
    syncStatus: SyncStatus;
    pendingItemsCount: number;
    isOnline: boolean;
}

interface NetworkSyncActions {
    forceSyncNow: () => Promise<void>;
    clearSyncErrors: () => Promise<void>;
    retryFailedUploads: () => Promise<void>;
}

export const useNetworkSync = (): [NetworkSyncState, NetworkSyncActions] => {
    const [networkState, setNetworkState] = useState<NetworkState>(
        networkService.getCurrentState()
    );
    const [syncStatus, setSyncStatus] = useState<SyncStatus>(
        syncService.getSyncStatus()
    );
    const [pendingItemsCount, setPendingItemsCount] = useState<number>(0);

    // Update pending items count
    const updatePendingCount = useCallback(async () => {
        const count = await syncService.getPendingItemsCount();
        setPendingItemsCount(count);
    }, []);

    useEffect(() => {
        // Subscribe to network changes
        const unsubscribeNetwork = networkService.addListener(setNetworkState);

        // Subscribe to sync status changes
        const unsubscribeSync = syncService.addSyncListener(setSyncStatus);

        // Initial pending count
        updatePendingCount();

        // Update pending count periodically
        const pendingCountInterval = setInterval(updatePendingCount, 30000); // Every 30 seconds

        return () => {
            unsubscribeNetwork();
            unsubscribeSync();
            clearInterval(pendingCountInterval);
        };
    }, [updatePendingCount]);

    // Update pending count when sync status changes
    useEffect(() => {
        updatePendingCount();
    }, [syncStatus, updatePendingCount]);

    const forceSyncNow = useCallback(async () => {
        await syncService.forceSyncNow();
        await updatePendingCount();
    }, [updatePendingCount]);

    const clearSyncErrors = useCallback(async () => {
        await syncService.clearSyncErrors();
    }, []);

    const retryFailedUploads = useCallback(async () => {
        // Clear old cached meals to free up space
        await offlineStorage.clearOldCachedMeals(7);

        // Force sync to retry failed uploads
        await forceSyncNow();
    }, [forceSyncNow]);

    const state: NetworkSyncState = {
        networkState,
        syncStatus,
        pendingItemsCount,
        isOnline: networkState.isConnected && networkState.isInternetReachable,
    };

    const actions: NetworkSyncActions = {
        forceSyncNow,
        clearSyncErrors,
        retryFailedUploads,
    };

    return [state, actions];
};