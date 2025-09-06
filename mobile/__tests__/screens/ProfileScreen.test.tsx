/**
 * Tests for ProfileScreen component
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import { ProfileScreen } from '@/screens/main/ProfileScreen';
import { AppProvider } from '@/context/AppContext';
import { Alert } from 'react-native';

// Mock navigation
const mockGoBack = jest.fn();
jest.mock('@react-navigation/native', () => ({
  ...jest.requireActual('@react-navigation/native'),
  useNavigation: () => ({
    goBack: mockGoBack,
  }),
}));

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  setItem: jest.fn(),
  getItem: jest.fn(() => Promise.resolve(JSON.stringify({
    id: '1',
    email: 'test@example.com',
    name: 'Test User',
    registrationDate: '2024-01-01T00:00:00.000Z',
    historyEnabled: true,
  }))),
  multiRemove: jest.fn(),
}));

// Mock Alert
jest.spyOn(Alert, 'alert');

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <NavigationContainer>
      <AppProvider>
        {component}
      </AppProvider>
    </NavigationContainer>
  );
};

describe('ProfileScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders user profile information', async () => {
    const { getByText } = renderWithProviders(<ProfileScreen />);
    
    await waitFor(() => {
      expect(getByText('Test User')).toBeTruthy();
      expect(getByText('test@example.com')).toBeTruthy();
      expect(getByText(/Member since/)).toBeTruthy();
    });
  });

  it('displays privacy and data settings', async () => {
    const { getByText } = renderWithProviders(<ProfileScreen />);
    
    await waitFor(() => {
      expect(getByText('Privacy & Data')).toBeTruthy();
      expect(getByText('Meal History')).toBeTruthy();
      expect(getByText('Weekly Insights')).toBeTruthy();
      expect(getByText('Data Sharing')).toBeTruthy();
    });
  });

  it('displays app settings', async () => {
    const { getByText } = renderWithProviders(<ProfileScreen />);
    
    await waitFor(() => {
      expect(getByText('App Settings')).toBeTruthy();
      expect(getByText('Push Notifications')).toBeTruthy();
      expect(getByText('Auto Sync')).toBeTruthy();
    });
  });

  it('displays data management options', async () => {
    const { getByText } = renderWithProviders(<ProfileScreen />);
    
    await waitFor(() => {
      expect(getByText('Data Management')).toBeTruthy();
      expect(getByText('Manage Consent')).toBeTruthy();
      expect(getByText('Export My Data')).toBeTruthy();
      expect(getByText('Delete Meal History')).toBeTruthy();
    });
  });

  it('displays account actions', async () => {
    const { getByText } = renderWithProviders(<ProfileScreen />);
    
    await waitFor(() => {
      expect(getByText('Account')).toBeTruthy();
      expect(getByText('Sign Out')).toBeTruthy();
      expect(getByText('Delete Account')).toBeTruthy();
    });
  });

  it('toggles settings switches', async () => {
    const { getAllByRole } = renderWithProviders(<ProfileScreen />);
    
    await waitFor(() => {
      const switches = getAllByRole('switch');
      expect(switches.length).toBeGreaterThan(0);
      
      // Test toggling the first switch
      const firstSwitch = switches[0];
      fireEvent(firstSwitch, 'valueChange', !firstSwitch.props.value);
    });
  });

  it('enters edit mode for profile', async () => {
    const { getByText } = renderWithProviders(<ProfileScreen />);
    
    await waitFor(() => {
      const editButton = getByText('Edit Profile');
      fireEvent.press(editButton);
      
      expect(getByText('Save')).toBeTruthy();
      expect(getByText('Cancel')).toBeTruthy();
    });
  });

  it('cancels profile editing', async () => {
    const { getByText } = renderWithProviders(<ProfileScreen />);
    
    await waitFor(() => {
      const editButton = getByText('Edit Profile');
      fireEvent.press(editButton);
      
      const cancelButton = getByText('Cancel');
      fireEvent.press(cancelButton);
      
      expect(getByText('Edit Profile')).toBeTruthy();
    });
  });

  it('saves profile changes', async () => {
    const { getByText } = renderWithProviders(<ProfileScreen />);
    
    await waitFor(() => {
      const editButton = getByText('Edit Profile');
      fireEvent.press(editButton);
      
      const saveButton = getByText('Save');
      fireEvent.press(saveButton);
      
      expect(Alert.alert).toHaveBeenCalledWith('Success', 'Profile updated successfully');
    });
  });

  it('shows logout confirmation', async () => {
    const { getByText } = renderWithProviders(<ProfileScreen />);
    
    await waitFor(() => {
      const signOutButton = getByText('Sign Out');
      fireEvent.press(signOutButton);
      
      expect(Alert.alert).toHaveBeenCalledWith(
        'Sign Out',
        'Are you sure you want to sign out?',
        expect.any(Array)
      );
    });
  });

  it('shows delete account confirmation', async () => {
    const { getByText } = renderWithProviders(<ProfileScreen />);
    
    await waitFor(() => {
      const deleteAccountButton = getByText('Delete Account');
      fireEvent.press(deleteAccountButton);
      
      expect(Alert.alert).toHaveBeenCalledWith(
        'Delete Account',
        expect.stringContaining('permanently delete'),
        expect.any(Array)
      );
    });
  });

  it('shows delete history confirmation', async () => {
    const { getByText } = renderWithProviders(<ProfileScreen />);
    
    await waitFor(() => {
      const deleteHistoryButton = getByText('Delete Meal History');
      fireEvent.press(deleteHistoryButton);
      
      expect(Alert.alert).toHaveBeenCalledWith(
        'Delete Meal History',
        expect.stringContaining('permanently delete'),
        expect.any(Array)
      );
    });
  });

  it('shows export data confirmation', async () => {
    const { getByText } = renderWithProviders(<ProfileScreen />);
    
    await waitFor(() => {
      const exportDataButton = getByText('Export My Data');
      fireEvent.press(exportDataButton);
      
      expect(Alert.alert).toHaveBeenCalledWith(
        'Export Data',
        expect.stringContaining('prepared for download'),
        expect.any(Array)
      );
    });
  });

  it('shows consent management placeholder', async () => {
    const { getByText } = renderWithProviders(<ProfileScreen />);
    
    await waitFor(() => {
      const consentButton = getByText('Manage Consent');
      fireEvent.press(consentButton);
      
      expect(Alert.alert).toHaveBeenCalledWith(
        'Consent Management',
        'This would open the consent management screen.'
      );
    });
  });

  it('displays app version information', async () => {
    const { getByText } = renderWithProviders(<ProfileScreen />);
    
    await waitFor(() => {
      expect(getByText('Nutrition Feedback v1.0.0')).toBeTruthy();
      expect(getByText('AI-powered nutrition analysis for Nigerian students')).toBeTruthy();
    });
  });
});