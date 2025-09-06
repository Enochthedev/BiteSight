/**
 * Tests for FeedbackScreen component
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { FeedbackScreen } from '@/screens/main/FeedbackScreen';
import { NutritionFeedback } from '@/types';

// Mock navigation
const mockNavigate = jest.fn();

jest.mock('@react-navigation/native', () => ({
  useRoute: () => ({
    params: {
      feedbackData: {
        mealId: 'test-meal-id',
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
        missingFoodGroups: ['vitamins', 'minerals'],
        recommendations: [
          'Add some vegetables like spinach (efo) or ugwu to get more vitamins',
          'Include fruits like oranges or bananas for additional minerals',
        ],
        overallBalanceScore: 65,
        feedbackMessage: 'Good start! Your meal has carbohydrates and proteins, but could use more vegetables and fruits for a complete nutritional balance.',
      } as NutritionFeedback,
    },
  }),
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

// Mock Share API
jest.mock('react-native/Libraries/Share/Share', () => ({
  share: jest.fn().mockResolvedValue({ action: 'sharedAction' }),
}));

describe('FeedbackScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render nutrition balance score', () => {
    const { getByText } = render(<FeedbackScreen />);

    expect(getByText('65%')).toBeTruthy();
    expect(getByText('Good, but can improve')).toBeTruthy();
    expect(getByText('Nutrition Balance')).toBeTruthy();
  });

  it('should display detected foods', () => {
    const { getByText } = render(<FeedbackScreen />);

    expect(getByText('What We Found')).toBeTruthy();
    expect(getByText('Jollof Rice')).toBeTruthy();
    expect(getByText('Fried Chicken')).toBeTruthy();
  });

  it('should show missing food groups', () => {
    const { getByText } = render(<FeedbackScreen />);

    expect(getByText('Missing Food Groups')).toBeTruthy();
    expect(getByText('Vitamins')).toBeTruthy();
    expect(getByText('Minerals')).toBeTruthy();
  });

  it('should display recommendations', () => {
    const { getByText } = render(<FeedbackScreen />);

    expect(getByText('Recommendations')).toBeTruthy();
    expect(getByText('Add some vegetables like spinach (efo) or ugwu to get more vitamins')).toBeTruthy();
    expect(getByText('Include fruits like oranges or bananas for additional minerals')).toBeTruthy();
  });

  it('should navigate to history when View History button is pressed', () => {
    const { getByText } = render(<FeedbackScreen />);

    const historyButton = getByText('View History');
    fireEvent.press(historyButton);

    expect(mockNavigate).toHaveBeenCalledWith('History');
  });

  it('should navigate to camera when Take Another Photo button is pressed', () => {
    const { getByText } = render(<FeedbackScreen />);

    const cameraButton = getByText('Take Another Photo');
    fireEvent.press(cameraButton);

    expect(mockNavigate).toHaveBeenCalledWith('Camera');
  });
});