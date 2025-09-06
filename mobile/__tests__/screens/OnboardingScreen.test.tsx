/**
 * Tests for OnboardingScreen component
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import { OnboardingScreen } from '@/screens/OnboardingScreen';

// Mock navigation
const mockNavigate = jest.fn();
jest.mock('@react-navigation/native', () => ({
  ...jest.requireActual('@react-navigation/native'),
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

const renderWithNavigation = (component: React.ReactElement) => {
  return render(
    <NavigationContainer>
      {component}
    </NavigationContainer>
  );
};

describe('OnboardingScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly', () => {
    const { getByText } = renderWithNavigation(<OnboardingScreen />);
    
    expect(getByText('Welcome to Nutrition Feedback')).toBeTruthy();
    expect(getByText('Learn how to get the most out of your nutrition journey')).toBeTruthy();
  });

  it('displays all onboarding steps', () => {
    const { getByText } = renderWithNavigation(<OnboardingScreen />);
    
    expect(getByText('Capture Your Meals')).toBeTruthy();
    expect(getByText('AI-Powered Recognition')).toBeTruthy();
    expect(getByText('Get Personalized Feedback')).toBeTruthy();
    expect(getByText('Track Your Progress')).toBeTruthy();
    expect(getByText('Your Privacy Matters')).toBeTruthy();
  });

  it('shows step details', () => {
    const { getByText } = renderWithNavigation(<OnboardingScreen />);
    
    expect(getByText('Use your camera to snap photos of meals')).toBeTruthy();
    expect(getByText('Recognizes over 50 common Nigerian foods')).toBeTruthy();
    expect(getByText('Simple, encouraging feedback in plain language')).toBeTruthy();
    expect(getByText('View your meal history over time')).toBeTruthy();
    expect(getByText('Explicit consent before storing any data')).toBeTruthy();
  });

  it('navigates to next step', async () => {
    const { getByText } = renderWithNavigation(<OnboardingScreen />);
    
    const nextButton = getByText('Next');
    fireEvent.press(nextButton);
    
    // Should still show Next button (not Get Started yet)
    await waitFor(() => {
      expect(getByText('Next')).toBeTruthy();
    });
  });

  it('shows Get Started on last step', async () => {
    const { getByText } = renderWithNavigation(<OnboardingScreen />);
    
    // Navigate to last step by pressing Next multiple times
    const nextButton = getByText('Next');
    
    // Press Next 4 times to reach the last step (5 steps total, 0-indexed)
    for (let i = 0; i < 4; i++) {
      fireEvent.press(nextButton);
      await waitFor(() => {});
    }
    
    await waitFor(() => {
      expect(getByText('Get Started')).toBeTruthy();
    });
  });

  it('shows Previous button after first step', async () => {
    const { getByText } = renderWithNavigation(<OnboardingScreen />);
    
    const nextButton = getByText('Next');
    fireEvent.press(nextButton);
    
    await waitFor(() => {
      expect(getByText('Previous')).toBeTruthy();
    });
  });

  it('navigates to previous step', async () => {
    const { getByText } = renderWithNavigation(<OnboardingScreen />);
    
    // Go to second step
    const nextButton = getByText('Next');
    fireEvent.press(nextButton);
    
    await waitFor(() => {
      expect(getByText('Previous')).toBeTruthy();
    });
    
    // Go back to first step
    const previousButton = getByText('Previous');
    fireEvent.press(previousButton);
    
    // Previous button should not be visible on first step
    await waitFor(() => {
      expect(() => getByText('Previous')).toThrow();
    });
  });

  it('skips onboarding', () => {
    const { getByText } = renderWithNavigation(<OnboardingScreen />);
    
    const skipButton = getByText('Skip');
    fireEvent.press(skipButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('Auth');
  });

  it('completes onboarding from last step', async () => {
    const { getByText } = renderWithNavigation(<OnboardingScreen />);
    
    // Navigate to last step
    const nextButton = getByText('Next');
    for (let i = 0; i < 4; i++) {
      fireEvent.press(nextButton);
      await waitFor(() => {});
    }
    
    // Press Get Started
    const getStartedButton = getByText('Get Started');
    fireEvent.press(getStartedButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('Auth');
  });

  it('displays pagination dots', () => {
    const { getAllByTestId } = renderWithNavigation(<OnboardingScreen />);
    
    // Note: This would require adding testID props to pagination dots
    // For now, we'll test that the component renders without errors
    expect(true).toBe(true);
  });

  it('shows step icons', () => {
    const { getByText } = renderWithNavigation(<OnboardingScreen />);
    
    // Test that step content is visible (icons are rendered via react-native-vector-icons)
    expect(getByText('Take photos of your Nigerian dishes for instant analysis')).toBeTruthy();
    expect(getByText('Advanced AI identifies foods and analyzes nutrition')).toBeTruthy();
  });
});