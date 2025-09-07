/**
 * End-to-end mobile app testing for complete user workflows
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Alert } from 'react-native';

// Mock navigation
const mockNavigate = jest.fn();
const mockGoBack = jest.fn();
const mockReset = jest.fn();

jest.mock('@react-navigation/native', () => ({
  ...jest.requireActual('@react-navigation/native'),
  useNavigation: () => ({
    navigate: mockNavigate,
    goBack: mockGoBack,
    reset: mockReset,
  }),
  useRoute: () => ({
    params: {},
  }),
}));

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}));

// Mock camera and image picker
jest.mock('react-native-image-picker', () => ({
  launchCamera: jest.fn(),
  launchImageLibrary: jest.fn(),
  MediaType: {
    photo: 'photo',
  },
}));

// Mock network info
jest.mock('@react-native-community/netinfo', () => ({
  fetch: jest.fn(() => Promise.resolve({ isConnected: true })),
  addEventListener: jest.fn(() => jest.fn()),
}));

// Import components after mocks
import App from '../../App';
import { AppProvider } from '../../src/context/AppContext';
import LoginScreen from '../../src/screens/auth/LoginScreen';
import RegisterScreen from '../../src/screens/auth/RegisterScreen';
import CameraScreen from '../../src/screens/main/CameraScreen';
import AnalysisScreen from '../../src/screens/main/AnalysisScreen';
import FeedbackScreen from '../../src/screens/main/FeedbackScreen';
import HistoryScreen from '../../src/screens/main/HistoryScreen';
import InsightsScreen from '../../src/screens/main/InsightsScreen';
import ConsentScreen from '../../src/screens/ConsentScreen';
import OnboardingScreen from '../../src/screens/OnboardingScreen';

// Mock API service
const mockApiService = {
  login: jest.fn(),
  register: jest.fn(),
  uploadMealImage: jest.fn(),
  getMealAnalysis: jest.fn(),
  getMealHistory: jest.fn(),
  getWeeklyInsights: jest.fn(),
  updateConsent: jest.fn(),
};

jest.mock('../../src/services/api', () => mockApiService);

describe('Complete User Workflows E2E Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    AsyncStorage.clear();
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <NavigationContainer>
        <AppProvider>
          {component}
        </AppProvider>
      </NavigationContainer>
    );
  };

  describe('User Registration and Onboarding Flow', () => {
    it('should complete full registration and onboarding workflow', async () => {
      // Mock successful registration
      mockApiService.register.mockResolvedValue({
        success: true,
        user: {
          id: 'user123',
          email: 'student@university.edu.ng',
          name: 'Test Student',
        },
        token: 'mock-jwt-token',
      });

      const { getByTestId, getByText } = renderWithProviders(<RegisterScreen />);

      // Fill registration form
      const nameInput = getByTestId('name-input');
      const emailInput = getByTestId('email-input');
      const passwordInput = getByTestId('password-input');
      const confirmPasswordInput = getByTestId('confirm-password-input');
      const registerButton = getByTestId('register-button');

      fireEvent.changeText(nameInput, 'Test Student');
      fireEvent.changeText(emailInput, 'student@university.edu.ng');
      fireEvent.changeText(passwordInput, 'SecurePassword123!');
      fireEvent.changeText(confirmPasswordInput, 'SecurePassword123!');

      // Submit registration
      fireEvent.press(registerButton);

      await waitFor(() => {
        expect(mockApiService.register).toHaveBeenCalledWith({
          name: 'Test Student',
          email: 'student@university.edu.ng',
          password: 'SecurePassword123!',
        });
      });

      // Should navigate to onboarding
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('Onboarding');
      });
    });

    it('should complete onboarding tutorial', async () => {
      const { getByTestId, getByText } = renderWithProviders(<OnboardingScreen />);

      // Navigate through onboarding steps
      const nextButton = getByTestId('next-button');

      // Step 1: Welcome
      expect(getByText(/Welcome to Nutrition Feedback/i)).toBeTruthy();
      fireEvent.press(nextButton);

      // Step 2: Camera feature
      await waitFor(() => {
        expect(getByText(/Take photos of your meals/i)).toBeTruthy();
      });
      fireEvent.press(nextButton);

      // Step 3: AI analysis
      await waitFor(() => {
        expect(getByText(/AI will analyze your food/i)).toBeTruthy();
      });
      fireEvent.press(nextButton);

      // Step 4: Feedback
      await waitFor(() => {
        expect(getByText(/Get personalized feedback/i)).toBeTruthy();
      });

      const finishButton = getByTestId('finish-button');
      fireEvent.press(finishButton);

      // Should navigate to consent screen
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('Consent');
      });
    });

    it('should handle consent management', async () => {
      mockApiService.updateConsent.mockResolvedValue({ success: true });

      const { getByTestId } = renderWithProviders(<ConsentScreen />);

      // Toggle consent options
      const dataStorageToggle = getByTestId('data-storage-toggle');
      const analyticsToggle = getByTestId('analytics-toggle');
      const continueButton = getByTestId('continue-button');

      fireEvent(dataStorageToggle, 'onValueChange', true);
      fireEvent(analyticsToggle, 'onValueChange', false);

      fireEvent.press(continueButton);

      await waitFor(() => {
        expect(mockApiService.updateConsent).toHaveBeenCalledWith({
          dataStorage: true,
          analytics: false,
          marketing: false,
        });
      });

      // Should navigate to main app
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('Main');
      });
    });
  });

  describe('Meal Analysis Workflow', () => {
    it('should complete full meal capture and analysis workflow', async () => {
      // Mock camera response
      const mockImageResponse = {
        assets: [{
          uri: 'file://mock-image.jpg',
          type: 'image/jpeg',
          fileName: 'meal.jpg',
        }],
      };

      const { launchCamera } = require('react-native-image-picker');
      launchCamera.mockImplementation((options, callback) => {
        callback(mockImageResponse);
      });

      // Mock API responses
      mockApiService.uploadMealImage.mockResolvedValue({
        success: true,
        analysisId: 'analysis123',
      });

      mockApiService.getMealAnalysis.mockResolvedValue({
        success: true,
        analysis: {
          detectedFoods: [
            { name: 'jollof_rice', confidence: 0.95, foodClass: 'carbohydrates' },
            { name: 'chicken', confidence: 0.88, foodClass: 'proteins' },
          ],
          feedback: {
            text: 'Great meal! You have good protein and carbohydrates. Try adding some vegetables.',
            recommendations: ['Add leafy greens for vitamins', 'Include fruits for fiber'],
            balanceScore: 0.75,
          },
        },
      });

      const { getByTestId } = renderWithProviders(<CameraScreen />);

      // Take photo
      const cameraButton = getByTestId('camera-button');
      fireEvent.press(cameraButton);

      // Should show image preview
      await waitFor(() => {
        expect(getByTestId('image-preview')).toBeTruthy();
      });

      // Confirm image
      const confirmButton = getByTestId('confirm-image-button');
      fireEvent.press(confirmButton);

      // Should navigate to analysis screen
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('Analysis', {
          imageUri: 'file://mock-image.jpg',
        });
      });

      // Test analysis screen
      const analysisScreen = renderWithProviders(
        <AnalysisScreen route={{ params: { imageUri: 'file://mock-image.jpg' } }} />
      );

      await waitFor(() => {
        expect(mockApiService.uploadMealImage).toHaveBeenCalled();
      });

      // Should show analysis results
      await waitFor(() => {
        expect(analysisScreen.getByText(/Analysis Complete/i)).toBeTruthy();
      });

      // Navigate to feedback
      const viewFeedbackButton = analysisScreen.getByTestId('view-feedback-button');
      fireEvent.press(viewFeedbackButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('Feedback', {
          analysisId: 'analysis123',
        });
      });
    });

    it('should handle offline meal capture and sync', async () => {
      // Mock offline state
      const { fetch } = require('@react-native-community/netinfo');
      fetch.mockResolvedValue({ isConnected: false });

      const mockImageResponse = {
        assets: [{
          uri: 'file://offline-meal.jpg',
          type: 'image/jpeg',
          fileName: 'offline_meal.jpg',
        }],
      };

      const { launchCamera } = require('react-native-image-picker');
      launchCamera.mockImplementation((options, callback) => {
        callback(mockImageResponse);
      });

      const { getByTestId, getByText } = renderWithProviders(<CameraScreen />);

      // Take photo while offline
      const cameraButton = getByTestId('camera-button');
      fireEvent.press(cameraButton);

      await waitFor(() => {
        expect(getByText(/Saved for later analysis/i)).toBeTruthy();
      });

      // Verify offline storage
      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        expect.stringContaining('offline_meals'),
        expect.any(String)
      );

      // Mock going back online
      fetch.mockResolvedValue({ isConnected: true });

      // Should trigger sync
      await waitFor(() => {
        expect(getByText(/Syncing offline meals/i)).toBeTruthy();
      });
    });

    it('should handle analysis errors gracefully', async () => {
      const mockImageResponse = {
        assets: [{
          uri: 'file://error-image.jpg',
          type: 'image/jpeg',
          fileName: 'error.jpg',
        }],
      };

      const { launchCamera } = require('react-native-image-picker');
      launchCamera.mockImplementation((options, callback) => {
        callback(mockImageResponse);
      });

      // Mock API error
      mockApiService.uploadMealImage.mockRejectedValue(new Error('Analysis failed'));

      const { getByTestId, getByText } = renderWithProviders(<CameraScreen />);

      const cameraButton = getByTestId('camera-button');
      fireEvent.press(cameraButton);

      const confirmButton = getByTestId('confirm-image-button');
      fireEvent.press(confirmButton);

      // Should show error message
      await waitFor(() => {
        expect(getByText(/Analysis failed/i)).toBeTruthy();
      });

      // Should offer retry option
      const retryButton = getByTestId('retry-button');
      expect(retryButton).toBeTruthy();
    });
  });

  describe('Feedback and History Workflow', () => {
    it('should display feedback with Nigerian food context', async () => {
      const mockFeedback = {
        text: 'Excellent Nigerian meal! Your amala with efo riro provides good carbohydrates and vitamins.',
        recommendations: [
          'Consider adding moimoi for extra protein',
          'Include fruits like orange or banana',
        ],
        culturalContext: 'Traditional Yoruba meal combination',
        balanceScore: 0.85,
        detectedFoods: [
          { name: 'amala', confidence: 0.95, foodClass: 'carbohydrates' },
          { name: 'efo_riro', confidence: 0.90, foodClass: 'vitamins' },
        ],
      };

      const { getByText, getByTestId } = renderWithProviders(
        <FeedbackScreen route={{ params: { feedback: mockFeedback } }} />
      );

      // Should display Nigerian food names
      expect(getByText(/amala/i)).toBeTruthy();
      expect(getByText(/efo riro/i)).toBeTruthy();

      // Should display cultural context
      expect(getByText(/Traditional Yoruba meal/i)).toBeTruthy();

      // Should display recommendations
      expect(getByText(/moimoi/i)).toBeTruthy();
      expect(getByText(/orange or banana/i)).toBeTruthy();

      // Should show balance score
      expect(getByText(/85%/)).toBeTruthy();

      // Test save to history
      const saveButton = getByTestId('save-to-history-button');
      fireEvent.press(saveButton);

      await waitFor(() => {
        expect(AsyncStorage.setItem).toHaveBeenCalled();
      });
    });

    it('should display meal history with filtering', async () => {
      const mockHistory = [
        {
          id: 'meal1',
          timestamp: '2024-01-01T12:00:00Z',
          detectedFoods: ['jollof_rice', 'chicken'],
          balanceScore: 0.8,
          imageUri: 'file://meal1.jpg',
        },
        {
          id: 'meal2',
          timestamp: '2024-01-02T18:00:00Z',
          detectedFoods: ['beans', 'plantain'],
          balanceScore: 0.7,
          imageUri: 'file://meal2.jpg',
        },
      ];

      mockApiService.getMealHistory.mockResolvedValue({
        success: true,
        meals: mockHistory,
      });

      const { getByTestId, getByText } = renderWithProviders(<HistoryScreen />);

      await waitFor(() => {
        expect(getByText(/jollof_rice/i)).toBeTruthy();
        expect(getByText(/beans/i)).toBeTruthy();
      });

      // Test date filtering
      const filterButton = getByTestId('filter-button');
      fireEvent.press(filterButton);

      const thisWeekFilter = getByTestId('this-week-filter');
      fireEvent.press(thisWeekFilter);

      // Should filter results
      await waitFor(() => {
        expect(mockApiService.getMealHistory).toHaveBeenCalledWith({
          dateRange: 'thisWeek',
        });
      });
    });

    it('should generate and display weekly insights', async () => {
      const mockInsights = {
        weekPeriod: 'Jan 1-7, 2024',
        mealsAnalyzed: 12,
        nutritionBalance: {
          carbohydrates: 0.8,
          proteins: 0.7,
          vitamins: 0.4,
          minerals: 0.3,
          fats: 0.6,
          water: 0.5,
        },
        recommendations: [
          'Include more vegetables in your meals',
          'Add fruits for better vitamin intake',
        ],
        positiveTrends: [
          'Good protein intake this week',
          'Consistent meal timing',
        ],
        improvementAreas: [
          'Low vegetable consumption',
          'Need more mineral-rich foods',
        ],
      };

      mockApiService.getWeeklyInsights.mockResolvedValue({
        success: true,
        insights: mockInsights,
      });

      const { getByText, getByTestId } = renderWithProviders(<InsightsScreen />);

      await waitFor(() => {
        expect(getByText(/Jan 1-7, 2024/)).toBeTruthy();
        expect(getByText(/12 meals analyzed/i)).toBeTruthy();
      });

      // Should display nutrition balance
      expect(getByText(/80%/)).toBeTruthy(); // Carbohydrates
      expect(getByText(/70%/)).toBeTruthy(); // Proteins

      // Should display recommendations
      expect(getByText(/Include more vegetables/i)).toBeTruthy();

      // Should display positive trends
      expect(getByText(/Good protein intake/i)).toBeTruthy();

      // Test sharing insights
      const shareButton = getByTestId('share-insights-button');
      fireEvent.press(shareButton);

      // Should trigger share functionality
      // (This would depend on actual share implementation)
    });
  });

  describe('User Settings and Privacy Workflow', () => {
    it('should manage privacy settings', async () => {
      const { getByTestId } = renderWithProviders(<ConsentScreen />);

      // Test privacy toggles
      const dataStorageToggle = getByTestId('data-storage-toggle');
      const analyticsToggle = getByTestId('analytics-toggle');
      const marketingToggle = getByTestId('marketing-toggle');

      // Change settings
      fireEvent(dataStorageToggle, 'onValueChange', false);
      fireEvent(analyticsToggle, 'onValueChange', true);
      fireEvent(marketingToggle, 'onValueChange', false);

      const saveButton = getByTestId('save-settings-button');
      fireEvent.press(saveButton);

      await waitFor(() => {
        expect(mockApiService.updateConsent).toHaveBeenCalledWith({
          dataStorage: false,
          analytics: true,
          marketing: false,
        });
      });
    });

    it('should handle data export request', async () => {
      const mockExportData = {
        user: { id: 'user123', email: 'test@example.com' },
        meals: [],
        feedback: [],
        insights: [],
      };

      mockApiService.exportUserData = jest.fn().mockResolvedValue({
        success: true,
        data: mockExportData,
      });

      const { getByTestId } = renderWithProviders(<ConsentScreen />);

      const exportButton = getByTestId('export-data-button');
      fireEvent.press(exportButton);

      await waitFor(() => {
        expect(mockApiService.exportUserData).toHaveBeenCalled();
      });

      // Should show export confirmation
      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Data Export',
          expect.stringContaining('exported successfully'),
          expect.any(Array)
        );
      });
    });

    it('should handle account deletion', async () => {
      mockApiService.deleteAccount = jest.fn().mockResolvedValue({
        success: true,
      });

      const { getByTestId } = renderWithProviders(<ConsentScreen />);

      const deleteButton = getByTestId('delete-account-button');
      fireEvent.press(deleteButton);

      // Should show confirmation dialog
      expect(Alert.alert).toHaveBeenCalledWith(
        'Delete Account',
        expect.stringContaining('permanently delete'),
        expect.arrayContaining([
          expect.objectContaining({ text: 'Cancel' }),
          expect.objectContaining({ text: 'Delete' }),
        ])
      );
    });
  });

  describe('Network and Performance Scenarios', () => {
    it('should handle slow network conditions', async () => {
      // Mock slow API response
      mockApiService.uploadMealImage.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({
          success: true,
          analysisId: 'slow-analysis',
        }), 5000))
      );

      const { getByTestId, getByText } = renderWithProviders(
        <AnalysisScreen route={{ params: { imageUri: 'file://test.jpg' } }} />
      );

      // Should show loading indicator
      expect(getByText(/Analyzing your meal/i)).toBeTruthy();

      // Should show progress updates
      await waitFor(() => {
        expect(getByText(/This may take a moment/i)).toBeTruthy();
      }, { timeout: 3000 });
    });

    it('should handle app backgrounding and foregrounding', async () => {
      const { AppState } = require('react-native');
      
      const { getByTestId } = renderWithProviders(<CameraScreen />);

      // Simulate app going to background
      act(() => {
        AppState.currentState = 'background';
      });

      // Simulate app coming to foreground
      act(() => {
        AppState.currentState = 'active';
      });

      // Should maintain state and functionality
      const cameraButton = getByTestId('camera-button');
      expect(cameraButton).toBeTruthy();
    });

    it('should handle memory pressure scenarios', async () => {
      // Mock multiple large images
      const largeImages = Array.from({ length: 10 }, (_, i) => ({
        uri: `file://large-image-${i}.jpg`,
        type: 'image/jpeg',
        fileName: `large_${i}.jpg`,
      }));

      const { getByTestId } = renderWithProviders(<HistoryScreen />);

      // Should handle large image lists efficiently
      // This would test lazy loading and image optimization
      expect(getByTestId('meal-history-list')).toBeTruthy();
    });
  });

  describe('Accessibility and Usability', () => {
    it('should support screen reader accessibility', async () => {
      const { getByLabelText } = renderWithProviders(<CameraScreen />);

      // Should have proper accessibility labels
      expect(getByLabelText(/Take photo of meal/i)).toBeTruthy();
      expect(getByLabelText(/Select from gallery/i)).toBeTruthy();
    });

    it('should support large text sizes', async () => {
      // Mock large text setting
      const { getByTestId } = renderWithProviders(<FeedbackScreen />);

      // Should adapt to large text sizes
      // This would test dynamic text scaling
      expect(getByTestId('feedback-text')).toBeTruthy();
    });

    it('should work with limited digital literacy', async () => {
      const { getByTestId, getByText } = renderWithProviders(<OnboardingScreen />);

      // Should have clear, simple instructions
      expect(getByText(/Tap the camera button/i)).toBeTruthy();
      expect(getByText(/Wait for analysis/i)).toBeTruthy();

      // Should have visual cues
      expect(getByTestId('camera-icon')).toBeTruthy();
      expect(getByTestId('analysis-icon')).toBeTruthy();
    });
  });
});