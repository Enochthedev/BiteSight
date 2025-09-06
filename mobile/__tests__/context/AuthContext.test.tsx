/**
 * Tests for authentication context and flows
 */

import React from 'react';
import { render, act, waitFor } from '@testing-library/react-native';
import { Text } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AppProvider, useAppContext } from '@/context/AppContext';
import { User } from '@/types';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  setItem: jest.fn(),
  getItem: jest.fn(),
  multiRemove: jest.fn(),
}));

const mockAsyncStorage = AsyncStorage as jest.Mocked<typeof AsyncStorage>;

// Test component to access context
const TestComponent: React.FC = () => {
  const { state, login, logout, setLoading, setError, clearError } = useAppContext();
  
  return (
    <>
      <Text testID="isAuthenticated">{state.isAuthenticated.toString()}</Text>
      <Text testID="isLoading">{state.isLoading.toString()}</Text>
      <Text testID="error">{state.error || 'null'}</Text>
      <Text testID="userName">{state.user?.name || 'null'}</Text>
      <Text testID="userEmail">{state.user?.email || 'null'}</Text>
    </>
  );
};

const renderWithProvider = () => {
  return render(
    <AppProvider>
      <TestComponent />
    </AppProvider>
  );
};

describe('AppContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAsyncStorage.getItem.mockResolvedValue(null);
  });

  it('initializes with default state', async () => {
    const { getByTestId } = renderWithProvider();
    
    await waitFor(() => {
      expect(getByTestId('isAuthenticated').children[0]).toBe('false');
      expect(getByTestId('isLoading').children[0]).toBe('false');
      expect(getByTestId('error').children[0]).toBe('null');
      expect(getByTestId('userName').children[0]).toBe('null');
      expect(getByTestId('userEmail').children[0]).toBe('null');
    });
  });

  it('loads existing user from storage', async () => {
    const mockUser: User = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      registrationDate: '2024-01-01T00:00:00.000Z',
      historyEnabled: true,
    };

    mockAsyncStorage.getItem
      .mockResolvedValueOnce('mock-token') // accessToken
      .mockResolvedValueOnce(JSON.stringify(mockUser)); // user

    const { getByTestId } = renderWithProvider();
    
    await waitFor(() => {
      expect(getByTestId('isAuthenticated').children[0]).toBe('true');
      expect(getByTestId('userName').children[0]).toBe('Test User');
      expect(getByTestId('userEmail').children[0]).toBe('test@example.com');
    });
  });

  it('handles login correctly', async () => {
    const mockUser: User = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      registrationDate: '2024-01-01T00:00:00.000Z',
      historyEnabled: true,
    };

    const TestLoginComponent: React.FC = () => {
      const { state, login } = useAppContext();
      
      const handleLogin = async () => {
        await login(mockUser, 'mock-token');
      };

      return (
        <>
          <Text testID="isAuthenticated">{state.isAuthenticated.toString()}</Text>
          <Text testID="userName">{state.user?.name || 'null'}</Text>
          <Text onPress={handleLogin} testID="loginButton">Login</Text>
        </>
      );
    };

    const { getByTestId } = render(
      <AppProvider>
        <TestLoginComponent />
      </AppProvider>
    );

    // Initially not authenticated
    expect(getByTestId('isAuthenticated').children[0]).toBe('false');

    // Perform login
    await act(async () => {
      getByTestId('loginButton').props.onPress();
    });

    await waitFor(() => {
      expect(getByTestId('isAuthenticated').children[0]).toBe('true');
      expect(getByTestId('userName').children[0]).toBe('Test User');
    });

    // Verify AsyncStorage calls
    expect(mockAsyncStorage.setItem).toHaveBeenCalledWith('accessToken', 'mock-token');
    expect(mockAsyncStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify(mockUser));
  });

  it('handles logout correctly', async () => {
    const mockUser: User = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      registrationDate: '2024-01-01T00:00:00.000Z',
      historyEnabled: true,
    };

    const TestLogoutComponent: React.FC = () => {
      const { state, login, logout } = useAppContext();
      
      const handleLogin = async () => {
        await login(mockUser, 'mock-token');
      };

      const handleLogout = async () => {
        await logout();
      };

      return (
        <>
          <Text testID="isAuthenticated">{state.isAuthenticated.toString()}</Text>
          <Text testID="userName">{state.user?.name || 'null'}</Text>
          <Text onPress={handleLogin} testID="loginButton">Login</Text>
          <Text onPress={handleLogout} testID="logoutButton">Logout</Text>
        </>
      );
    };

    const { getByTestId } = render(
      <AppProvider>
        <TestLogoutComponent />
      </AppProvider>
    );

    // Login first
    await act(async () => {
      getByTestId('loginButton').props.onPress();
    });

    await waitFor(() => {
      expect(getByTestId('isAuthenticated').children[0]).toBe('true');
    });

    // Perform logout
    await act(async () => {
      getByTestId('logoutButton').props.onPress();
    });

    await waitFor(() => {
      expect(getByTestId('isAuthenticated').children[0]).toBe('false');
      expect(getByTestId('userName').children[0]).toBe('null');
    });

    // Verify AsyncStorage calls
    expect(mockAsyncStorage.multiRemove).toHaveBeenCalledWith(['accessToken', 'user']);
  });

  it('handles loading state', async () => {
    const TestLoadingComponent: React.FC = () => {
      const { state, setLoading } = useAppContext();
      
      const handleSetLoading = () => {
        setLoading(true);
      };

      return (
        <>
          <Text testID="isLoading">{state.isLoading.toString()}</Text>
          <Text onPress={handleSetLoading} testID="setLoadingButton">Set Loading</Text>
        </>
      );
    };

    const { getByTestId } = render(
      <AppProvider>
        <TestLoadingComponent />
      </AppProvider>
    );

    // Initially not loading (after initialization)
    await waitFor(() => {
      expect(getByTestId('isLoading').children[0]).toBe('false');
    });

    // Set loading
    await act(async () => {
      getByTestId('setLoadingButton').props.onPress();
    });

    expect(getByTestId('isLoading').children[0]).toBe('true');
  });

  it('handles error state', async () => {
    const TestErrorComponent: React.FC = () => {
      const { state, setError, clearError } = useAppContext();
      
      const handleSetError = () => {
        setError('Test error message');
      };

      const handleClearError = () => {
        clearError();
      };

      return (
        <>
          <Text testID="error">{state.error || 'null'}</Text>
          <Text onPress={handleSetError} testID="setErrorButton">Set Error</Text>
          <Text onPress={handleClearError} testID="clearErrorButton">Clear Error</Text>
        </>
      );
    };

    const { getByTestId } = render(
      <AppProvider>
        <TestErrorComponent />
      </AppProvider>
    );

    // Initially no error
    await waitFor(() => {
      expect(getByTestId('error').children[0]).toBe('null');
    });

    // Set error
    await act(async () => {
      getByTestId('setErrorButton').props.onPress();
    });

    expect(getByTestId('error').children[0]).toBe('Test error message');

    // Clear error
    await act(async () => {
      getByTestId('clearErrorButton').props.onPress();
    });

    expect(getByTestId('error').children[0]).toBe('null');
  });

  it('handles AsyncStorage errors gracefully', async () => {
    mockAsyncStorage.getItem.mockRejectedValue(new Error('Storage error'));

    const { getByTestId } = renderWithProvider();
    
    await waitFor(() => {
      expect(getByTestId('isAuthenticated').children[0]).toBe('false');
      expect(getByTestId('isLoading').children[0]).toBe('false');
    });
  });

  it('handles login storage errors', async () => {
    mockAsyncStorage.setItem.mockRejectedValue(new Error('Storage error'));

    const mockUser: User = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      registrationDate: '2024-01-01T00:00:00.000Z',
      historyEnabled: true,
    };

    const TestLoginErrorComponent: React.FC = () => {
      const { login } = useAppContext();
      
      const handleLogin = async () => {
        try {
          await login(mockUser, 'mock-token');
        } catch (error) {
          // Expected to throw
        }
      };

      return <Text onPress={handleLogin} testID="loginButton">Login</Text>;
    };

    const { getByTestId } = render(
      <AppProvider>
        <TestLoginErrorComponent />
      </AppProvider>
    );

    await expect(async () => {
      await act(async () => {
        getByTestId('loginButton').props.onPress();
      });
    }).rejects.toThrow();
  });
});