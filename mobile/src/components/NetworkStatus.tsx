/**
 * Network status indicator component
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useNetworkSync } from '@/hooks/useNetworkSync';
import { colors, spacing } from '@/styles';

export const NetworkStatus: React.FC = () => {
    const [{ networkState, syncStatus, pendingItemsCount, isOnline }, { forceSyncNow, clearSyncErrors }] = useNetworkSync();

    const getStatusColor = () => {
        if (!isOnline) return colors.error;
        if (syncStatus.isRunning) return colors.warning;
        if (syncStatus.errors.length > 0) return colors.error;
        return colors.success;
    };

    const getStatusText = () => {
        if (!isOnline) return 'Offline';
        if (syncStatus.isRunning) return 'Syncing...';
        if (syncStatus.errors.length > 0) return 'Sync Error';
        return 'Online';
    };

    const handleSyncPress = async () => {
        if (syncStatus.errors.length > 0) {
            await clearSyncErrors();
        }
        await forceSyncNow();
    };

    return (
        <View style={styles.container}>
            <View style={[styles.indicator, { backgroundColor: getStatusColor() }]} />
            <Text style={styles.statusText}>{getStatusText()}</Text>
            
            {pendingItemsCount > 0 && (
                <Text style={styles.pendingText}>
                    {pendingItemsCount} pending
                </Text>
            )}
            
            {(syncStatus.errors.length > 0 || pendingItemsCount > 0) && (
                <TouchableOpacity 
                    style={styles.syncButton} 
                    onPress={handleSyncPress}
                    disabled={syncStatus.isRunning}
                >
                    <Text style={styles.syncButtonText}>
                        {syncStatus.isRunning ? 'Syncing...' : 'Retry'}
                    </Text>
                </TouchableOpacity>
            )}
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: spacing.md,
        paddingVertical: spacing.sm,
        backgroundColor: colors.background,
        borderBottomWidth: 1,
        borderBottomColor: colors.border,
    },
    indicator: {
        width: 8,
        height: 8,
        borderRadius: 4,
        marginRight: spacing.sm,
    },
    statusText: {
        fontSize: 14,
        color: colors.text,
        marginRight: spacing.sm,
    },
    pendingText: {
        fontSize: 12,
        color: colors.textSecondary,
        marginRight: spacing.sm,
    },
    syncButton: {
        paddingHorizontal: spacing.sm,
        paddingVertical: spacing.xs,
        backgroundColor: colors.primary,
        borderRadius: 4,
        marginLeft: 'auto',
    },
    syncButtonText: {
        fontSize: 12,
        color: colors.white,
        fontWeight: '600',
    },
});