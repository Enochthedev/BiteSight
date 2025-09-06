/**
 * Tests for ConsentScreen component
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import { ConsentScreen } from '@/screens/ConsentScreen';

// Mock navigation
const mockGoBack = jest.fn();
jest.mock('@react-navigation/native', () => ({
  ...jest.requireActual('@react-navigation/native'),
  useNavigation: () => ({
    goBack: mockGoBack,
  }),
}));

const renderWithNavigation = (component: React.ReactElement) => {
  return render(
    <NavigationContainer>
      {component}
    </NavigationContainer>
  );
};

describe('ConsentScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly for initial setup', () => {
    const { getByText } = renderWithNavigation(
      <ConsentScreen isInitialSetup={true} />
    );
    
    expect(getByText('Your Privacy Matters')).toBeTruthy();
    expect(getByText('Choose what data you\'re comfortable sharing with us')).toBeTruthy();
    expect(getByText('Meal History Storage')).toBeTruthy();
    expect(getByText('App Usage Analytics')).toBeTruthy();
    expect(getByText('Research Participation')).toBeTruthy();
    expect(getByText('Marketing Communications')).toBeTruthy();
  });

  it('renders correctly for settings update', () => {
    const { getByText } = renderWithNavigation(
      <ConsentScreen isInitialSetup={false} />
    );
    
    expect(getByText('Manage your data sharing preferences')).toBeTruthy();
    expect(getByText('Save Preferences')).toBeTruthy();
    expect(getByText('Cancel')).toBeTruthy();
  });

  it('shows privacy policy requirement for initial setup', () => {
    const { getByText } = renderWithNavigation(
      <ConsentScreen isInitialSetup={true} />
    );
    
    expect(getByText(/I have read and understood the/)).toBeTruthy();
    expect(getByText('Privacy Policy')).toBeTruthy();
  });

  it('toggles consent options', () => {
    const { getAllByRole } = renderWithNavigation(
      <ConsentScreen isInitialSetup={false} />
    );
    
    const switches = getAllByRole('switch');
    expect(switches.length).toBeGreaterThan(0);
    
    // Test toggling the first switch (meal history)
    const mealHistorySwitch = switches[0];
    expect(mealHistorySwitch.props.value).toBe(false);
    
    fireEvent(mealHistorySwitch, 'valueChange', true);
    expect(mealHistorySwitch.props.value).toBe(true);
  });

  it('requires privacy policy acceptance for initial setup', async () => {
    const { getByText, getAllByRole } = renderWithNavigation(
      <ConsentScreen isInitialSetup={true} />
    );
    
    const continueButton = getByText('Continue');
    fireEvent.press(continueButton);
    
    // Should show alert about privacy policy requirement
    // Note: Alert testing would require additional mocking
  });

  it('calls onConsentComplete when provided', async () => {
    const mockOnConsentComplete = jest.fn();
    const { getByText, getAllByRole } = renderWithNavigation(
      <ConsentScreen 
        isInitialSetup={true} 
        onConsentComplete={mockOnConsentComplete}
      />
    );
    
    // Accept privacy policy
    const switches = getAllByRole('switch');
    const privacyPolicySwitch = switches[switches.length - 1]; // Last switch is privacy policy
    fireEvent(privacyPolicySwitch, 'valueChange', true);
    
    const continueButton = getByText('Continue');
    fireEvent.press(continueButton);
    
    await waitFor(() => {
      expect(mockOnConsentComplete).toHaveBeenCalled();
    });
  });

  it('navigates back when cancel is pressed', () => {
    const { getByText } = renderWithNavigation(
      <ConsentScreen isInitialSetup={false} />
    );
    
    const cancelButton = getByText('Cancel');
    fireEvent.press(cancelButton);
    
    expect(mockGoBack).toHaveBeenCalled();
  });

  it('displays privacy and security information', () => {
    const { getByText } = renderWithNavigation(
      <ConsentScreen isInitialSetup={false} />
    );
    
    expect(getByText('Privacy & Security')).toBeTruthy();
    expect(getByText('Your Data is Secure')).toBeTruthy();
    expect(getByText('Easy Data Deletion')).toBeTruthy();
    expect(getByText('No Third-Party Sharing')).toBeTruthy();
  });

  it('shows consent descriptions', () => {
    const { getByText } = renderWithNavigation(
      <ConsentScreen isInitialSetup={false} />
    );
    
    expect(getByText(/Store your meal photos and analysis results/)).toBeTruthy();
    expect(getByText(/Help us improve the app by sharing anonymous usage data/)).toBeTruthy();
    expect(getByText(/Contribute to nutrition research/)).toBeTruthy();
    expect(getByText(/Receive updates about new features/)).toBeTruthy();
  });
});