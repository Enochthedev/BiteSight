/**
 * Environment configuration for different deployment environments
 */

import { Platform } from 'react-native';
import Constants from 'expo-constants';

export interface EnvironmentConfig {
    apiBaseUrl: string;
    environment: 'development' | 'staging' | 'production';
    enableLogging: boolean;
    enableAnalytics: boolean;
    apiTimeout: number;
}

const getApiBaseUrl = (): string => {
    // Check if running in Expo Go
    const isExpoGo = Constants.appOwnership === 'expo';
    
    if (__DEV__) {
        // Development mode
        if (Platform.OS === 'ios') {
            // iOS Simulator
            return isExpoGo 
                ? 'http://127.0.0.1:8000/api/v1'  // Expo Go
                : 'http://localhost:8000/api/v1';  // Standalone
        } else if (Platform.OS === 'android') {
            // Android Emulator
            return 'http://10.0.2.2:8000/api/v1';
        } else {
            // Web or other platforms
            return 'http://localhost:8000/api/v1';
        }
    } else {
        // Production mode
        return 'https://api.bitesight.app/api/v1';
    }
};

const environment: EnvironmentConfig = {
    apiBaseUrl: getApiBaseUrl(),
    environment: __DEV__ ? 'development' : 'production',
    enableLogging: __DEV__,
    enableAnalytics: !__DEV__,
    apiTimeout: 30000, // 30 seconds
};

export default environment;

// Export individual values for convenience
export const { apiBaseUrl, enableLogging, enableAnalytics, apiTimeout } = environment;
