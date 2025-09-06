/**
 * Tests for LoginScreen component
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import { LoginScreen } from '@/screens/auth/LoginScreen';
import { AppProvider } from '@/context/AppContext';

// Mock navigation
const mockNavigate = jest.fn();
jest.mock('@react-navigation/native', () => ({
  ...jest.requireActual('@react-navigation/native'),
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  setItem: jest.fn(),
  getItem: jest.fn(),
  multiRemove: jest.fn(),
}));

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <NavigationContainer>
      <AppProvider>
        {component}
      </AppProvider>
    </NavigationContainer>
  );
};

describe('LoginScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly', () => {
    const { getByText, getByPlaceholderText } = renderWithProviders(<LoginScreen />);
    
    expect(getByText('Welcome Back')).toBeTruthy();
    expect(getByText('Sign in to continue')).toBeTruthy();
    expect(getByPlaceholderText('Enter your email')).toBeTruthy();
    expect(getByPlaceholderText('Enter your password')).toBeTruthy();
  });

  it('validates email format', async () => {
    const { getByPlaceholderText, getByText } = renderWithProviders(<LoginScreen />);
    
    const emailInput = getByPlaceholderText('Enter your email');
    const signInButton = getByText('Sign In');
    
    fireEvent.changeText(emailInput, 'invalid-email');
    fireEvent.press(signInButton);
    
    await waitFor(() => {
      expect(getByText('Please enter a valid email')).toBeTruthy();
    });
  });

  it('validates password length', async () => {
    const { getByPlaceholderText, getByText } = renderWithProviders(<LoginScreen />);
    
    const passwordInput = getByPlaceholderText('Enter your password');
    const signInButton = getByText('Sign In');
    
    fireEvent.changeText(passwordInput, '123');
    fireEvent.press(signInButton);
    
    await waitFor(() => {
      expect(getByText('Password must be at least 6 characters')).toBeTruthy();
    });
  });

  it('shows required field errors', async () => {
    const { getByText } = renderWithProviders(<LoginScreen />);
    
    const signInButton = getByText('Sign In');
    fireEvent.press(signInButton);
    
    await waitFor(() => {
      expect(getByText('Email is required')).toBeTruthy();
      expect(getByText('Password is required')).toBeTruthy();
    });
  });

  it('navigates to register screen', () => {
    const { getByText } = renderWithProviders(<LoginScreen />);
    
    const createAccountButton = getByText('Create Account');
    fireEvent.press(createAccountButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('Register');
  });

  it('handles successful login', async () => {
    const { getByPlaceholderText, getByText } = renderWithProviders(<LoginScreen />);
    
    const emailInput = getByPlaceholderText('Enter your email');
    const passwordInput = getByPlaceholderText('Enter your password');
    const signInButton = getByText('Sign In');
    
    fireEvent.changeText(emailInput, 'test@example.com');
    fireEvent.changeText(passwordInput, 'password123');
    fireEvent.press(signInButton);
    
    // Should show loading state
    await waitFor(() => {
      expect(signInButton.props.accessibilityState?.disabled).toBe(true);
    });
  });

  it('clears errors when user starts typing', async () => {
    const { getByPlaceholderText, getByText, queryByText } = renderWithProviders(<LoginScreen />);
    
    const emailInput = getByPlaceholderText('Enter your email');
    const signInButton = getByText('Sign In');
    
    // Trigger validation error
    fireEvent.press(signInButton);
    
    await waitFor(() => {
      expect(getByText('Email is required')).toBeTruthy();
    });
    
    // Start typing to clear error
    fireEvent.changeText(emailInput, 'test@example.com');
    
    await waitFor(() => {
      expect(queryByText('Email is required')).toBeFalsy();
    });
  });
});