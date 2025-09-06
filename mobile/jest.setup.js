import 'react-native-gesture-handler/jestSetup';

// Mock react-native-vector-icons
jest.mock('react-native-vector-icons/MaterialIcons', () => 'Icon');

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () =>
    require('@react-native-async-storage/async-storage/jest/async-storage-mock')
);

// Mock NetInfo
jest.mock('@react-native-community/netinfo', () => ({
    addEventListener: jest.fn(),
    fetch: jest.fn(() => Promise.resolve({
        isConnected: true,
        isInternetReachable: true,
        type: 'wifi',
    })),
}));

// Mock XMLHttpRequest for upload tests
global.XMLHttpRequest = jest.fn(() => ({
    upload: { addEventListener: jest.fn() },
    addEventListener: jest.fn(),
    open: jest.fn(),
    send: jest.fn(),
    setRequestHeader: jest.fn(),
    abort: jest.fn(),
    status: 200,
    responseText: '{}',
    timeout: 0,
}));

// Mock Blob for cache size calculations
global.Blob = jest.fn((content) => ({
    size: JSON.stringify(content).length,
}));

// Mock react-navigation
jest.mock('@react-navigation/native', () => ({
    useNavigation: () => ({
        navigate: jest.fn(),
        goBack: jest.fn(),
    }),
    useRoute: () => ({
        params: {},
    }),
    useFocusEffect: (callback) => {
        const React = require('react');
        React.useEffect(callback, []);
    },
    NavigationContainer: ({ children }) => children,
}));

// Mock react-navigation/stack
jest.mock('@react-navigation/stack', () => ({
    createStackNavigator: () => ({
        Navigator: ({ children }) => children,
        Screen: ({ children }) => children,
    }),
}));

// Mock SafeAreaProvider
jest.mock('react-native-safe-area-context', () => ({
    SafeAreaProvider: ({ children }) => children,
    useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }),
}));

// Silence the warning about act() wrapping
global.console = {
    ...console,
    warn: jest.fn(),
};