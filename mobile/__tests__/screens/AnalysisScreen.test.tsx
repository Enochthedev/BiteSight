/**
 * Tests for AnalysisScreen component
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { AnalysisScreen } from '@/screens/main/AnalysisScreen';
import { apiService } from '@/services/api';

// Mock the API service
jest.mock('@/services/api');
const mockApiService = apiService as jest.Mocked<typeof apiService>;

// Mock navigation
const mockNavigate = jest.fn();
const mockGoBack = jest.fn();

jest.mock('@react-navigation/native', () => ({
  useRoute: () => ({
    params: {
      mealId: 'test-meal-id',
      imageUri: 'test-image-uri',
    },
  }),
  useNavigation: () => ({
    navigate: mockNavigate,
    goBack: mockGoBack,
  }),
}));

describe('AnalysisScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render loading state initially', () => {
    mockApiService.get.mockImplementation(() => new Promise(() => {})); // Never resolves

    const { getByText } = render(<AnalysisScreen />);

    expect(getByText('Analyzing your meal...')).toBeTruthy();
    expect(getByText('Cancel')).toBeTruthy();
  });

  it('should handle analysis failure', async () => {
    mockApiService.get.mockRejectedValue({
      userMessage: 'Analysis failed. Please try again.',
    });

    const { getByText } = render(<AnalysisScreen />);

    await waitFor(() => {
      expect(getByText('Analysis Failed')).toBeTruthy();
      expect(getByText('Analysis failed. Please try again.')).toBeTruthy();
      expect(getByText('Try Again')).toBeTruthy();
    });
  });

  it('should show detected foods when analysis is complete', async () => {
    const mockAnalysis = {
      id: 'test-meal-id',
      analysisStatus: 'completed',
      detectedFoods: [
        {
          foodName: 'Jollof Rice',
          confidence: 0.95,
          foodClass: 'carbohydrates',
        },
        {
          foodName: 'Fried Chicken',
          confidence: 0.88,
          foodClass: 'proteins',
        },
      ],
    };

    mockApiService.get.mockResolvedValue(mockAnalysis);

    const { getByText } = render(<AnalysisScreen />);

    await waitFor(() => {
      expect(getByText('Analysis Complete!')).toBeTruthy();
      expect(getByText('Jollof Rice')).toBeTruthy();
      expect(getByText('Fried Chicken')).toBeTruthy();
      expect(getByText('95%')).toBeTruthy();
      expect(getByText('88%')).toBeTruthy();
    });
  });

  it('should retry analysis when retry button is pressed', async () => {
    mockApiService.get
      .mockRejectedValueOnce({
        userMessage: 'Network error',
      })
      .mockResolvedValue({
        id: 'test-meal-id',
        analysisStatus: 'completed',
        detectedFoods: [],
      });

    const { getByText } = render(<AnalysisScreen />);

    await waitFor(() => {
      expect(getByText('Try Again')).toBeTruthy();
    });

    const retryButton = getByText('Try Again');
    fireEvent.press(retryButton);

    await waitFor(() => {
      expect(getByText('Analysis Complete!')).toBeTruthy();
    });
  });
});