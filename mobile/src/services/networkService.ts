/**
 * Network monitoring and status service
 */

import NetInfo, { NetInfoState } from '@react-native-community/netinfo';
import { NetworkState } from '@/types';

export class NetworkService {
    private static instance: NetworkService;
    private listeners: ((state: NetworkState) => void)[] = [];
    private currentState: NetworkState = {
        isConnected: false,
        isInternetReachable: false,
        type: 'unknown',
    };

    private constructor() {
        this.initialize();
    }

    public static getInstance(): NetworkService {
        if (!NetworkService.instance) {
            NetworkService.instance = new NetworkService();
        }
        return NetworkService.instance;
    }

    private initialize(): void {
        // Subscribe to network state changes
        NetInfo.addEventListener((state: NetInfoState) => {
            const networkState: NetworkState = {
                isConnected: state.isConnected ?? false,
                isInternetReachable: state.isInternetReachable ?? false,
                type: state.type,
            };

            this.currentState = networkState;
            this.notifyListeners(networkState);
        });

        // Get initial network state
        NetInfo.fetch().then((state: NetInfoState) => {
            const networkState: NetworkState = {
                isConnected: state.isConnected ?? false,
                isInternetReachable: state.isInternetReachable ?? false,
                type: state.type,
            };
            this.currentState = networkState;
        });
    }

    public getCurrentState(): NetworkState {
        return this.currentState;
    }

    public isOnline(): boolean {
        return this.currentState.isConnected && this.currentState.isInternetReachable;
    }

    public addListener(callback: (state: NetworkState) => void): () => void {
        this.listeners.push(callback);

        // Return unsubscribe function
        return () => {
            const index = this.listeners.indexOf(callback);
            if (index > -1) {
                this.listeners.splice(index, 1);
            }
        };
    }

    private notifyListeners(state: NetworkState): void {
        this.listeners.forEach(listener => listener(state));
    }

    public async waitForConnection(timeout: number = 10000): Promise<boolean> {
        if (this.isOnline()) {
            return true;
        }

        return new Promise((resolve) => {
            const timeoutId = setTimeout(() => {
                unsubscribe();
                resolve(false);
            }, timeout);

            const unsubscribe = this.addListener((state) => {
                if (state.isConnected && state.isInternetReachable) {
                    clearTimeout(timeoutId);
                    unsubscribe();
                    resolve(true);
                }
            });
        });
    }
}

export const networkService = NetworkService.getInstance();