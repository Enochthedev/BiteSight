/**
 * Tests for RegisterScreen component
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import { RegisterScreen } from '@/screens/auth/RegisterScreen';
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

describe('RegisterScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly', () => {
    const { getByText, getByPlaceholderText } = renderWithProviders(<RegisterScreen />);
    
    expect(getByText('Create Account')).toBeTruthy();
    expect(getByText('Join us to start your nutrition journey')).toBeTruthy();
    expect(getByPlaceholderText('Enter your full name')).toBeTruthy();
    expect(getByPlaceholderText('Enter your email')).toBeTruthy();
    expect(getByPlaceholderText('Create a password')).toBeTruthy();
    expect(getByPlaceholderText('Confirm your password')).toBeTruthy();
  });

  it('validates all required fields', async () => {
    const { getByText } = renderWithProviders(<RegisterScreen />);
    
    const createAccountButton = getByText('Create Account');
    fireEvent.press(createAccountButton);
    
    await waitFor(() => {
      expect(getByText('Name is required')).toBeTruthy();
      expect(getByText('Email is required')).toBeTruthy();
      expect(getByText('Password is required')).toBeTruthy();
    });
  });

  it('validates email format', async () => {
    const { getByPlaceholderText, getByText } = renderWithProviders(<RegisterScreen />);
    
    const emailInput = getByPlaceholderText('Enter your email');
    const createAccountButton = getByText('Create Account');
    
    fireEvent.changeText(emailInput, 'invalid-email');
    fireEvent.press(createAccountButton);
    
    await waitFor(() => {
      expect(getByText('Please enter a valid email')).toBeTruthy();
    });
  });

  it('validates password confirmation', async () => {
    const { getByPlaceholderText, getByText } = renderWithProviders(<RegisterScreen />);
    
    const passwordInput = getByPlaceholderText('Create a password');
    const confirmPasswordInput = getByPlaceholderText('Confirm your password');
    const createAccountButton = getByText('Create Account');
    
    fireEvent.changeText(passwordInput, 'password123');
    fireEvent.changeText(confirmPasswordInput, 'different123');
    fireEvent.press(createAccountButton);
    
    await waitFor(() => {
      expect(getByText('Passwords do not match')).toBeTruthy();
    });
  });

  it('validates minimum password length', async () => {
    const { getByPlaceholderText, getByText } = renderWithProviders(<RegisterScreen />);
    
    const passwordInput = getByPlaceholderText('Create a password');
    const createAccountButton = getByText('Create Account');
    
    fireEvent.changeText(passwordInput, '123');
    fireEvent.press(createAccountButton);
    
    await waitFor(() => {
      expect(getByText('Password must be at least 6 characters')).toBeTruthy();
    });
  });

  it('navigates to login screen', () => {
    const { getByText } = renderWithProviders(<RegisterScreen />);
    
    const signInButton = getByText('Sign In');
    fireEvent.press(signInButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('Login');
  });

  it('handles successful registration', async () => {
    const { getByPlaceholderText, getByText } = renderWithProviders(<RegisterScreen />);
    
    const nameInput = getByPlaceholderText('Enter your full name');
    const emailInput = getByPlaceholderText('Enter your email');
    const passwordInput = getByPlaceholderText('Create a password');
    const confirmPasswordInput = getByPlaceholderText('Confirm your password');
    const createAccountButton = getByText('Create Account');
    
    fireEvent.changeText(nameInput, 'John Doe');
    fireEvent.changeText(emailInput, 'john@example.com');
    fireEvent.changeText(passwordInput, 'password123');
    fireEvent.changeText(confirmPasswordInput, 'password123');
    fireEvent.press(createAccountButton);
    
    // Should navigate to consent screen for new users
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('Consent', {
        isInitialSetup: true,
        onConsentComplete: expect.any(Function),
      });
    });
  });

  it('clears field errors when user starts typing', async () => {
    const { getByPlaceholderText, getByText, queryByText } = renderWithProviders(<RegisterScreen />);
    
    const nameInput = getByPlaceholderText('Enter your full name');
    const createAccountButton = getByText('Create Account');
    
    // Trigger validation error
    fireEvent.press(createAccountButton);
    
    await waitFor(() => {
      expect(getByText('Name is required')).toBeTruthy();
    });
    
    // Start typing to clear error
    fireEvent.changeText(nameInput, 'John');
    
    await waitFor(() => {
      expect(queryByText('Name is required')).toBeFalsy();
    });
  });
});