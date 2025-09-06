/**
 * Tests for InsightsScreen component
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { InsightsScreen } from '@/screens/main/InsightsScreen';
import { apiService } from '@/services/api';

// Mock the API service
jest.mock('@/services/api');
const mockApiService = apiService as jest.Mocked<typeof apiService>;

// Mock navigation
jest.mock('@react-navigation/native', () => ({
  ...jest.requireActual('@react-navigation/native'),
  useFocusEffect: (callback: () => void) => {
    React.useEffect(callback, []);
  },
}));

const Stack = createStackNavigator();

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <NavigationContainer>
    <Stack.Navigator>
      <Stack.Screen name="Insights" component={() => <>{children}</>} />
    </Stack.Navigator>
  </NavigationContainer>
);

const mockWeeklyInsights = [
  {
    id: '1',
    studentId: 'student-1',
    weekPeriod: 'Dec 2-8, 2024',
    mealsAnalyzed: 18,
    nutritionBalance: {
      carbohydrates: 85,
      proteins: 72,
      fats: 65,
      vitamins: 45,
      minerals: 38,
      water: 90,
    },
    improvementAreas: ['vitamins', 'minerals'],
    positiveTrends: ['carbohydrates', 'water'],
    recommendations: 'Great job maintaining good carbohydrate and water intake! Try to include more leafy vegetables like spinach (efo) and fruits for better vitamin and mineral balance.',
    generatedAt: new Date().toISOString(),
  },
  {
    id: '2',
    studentId: 'student-1',
    weekPeriod: 'Nov 25 - Dec 1, 2024',
    mealsAnalyzed: 15,
    nutritionBalance: {
      carbohydrates: 78,
      proteins: 68,
      fats: 70,
      vitamins: 52,
      minerals: 45,
      water: 85,
    },
    improvementAreas: ['proteins', 'minerals'],
    positiveTrends: ['fats', 'vitamins'],
    recommendations: 'You\'ve improved your vitamin intake this week! Consider adding more beans and fish for better protein and mineral content.',
    generatedAt: new Date().toISOString(),
  },
];

describe('InsightsScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render loading state initially', () => {
    mockApiService.getWeeklyInsights.mockImplementation(() => new Promise(() => {})); // Never resolves

    const { getByText } = render(
      <TestWrapper>
        <InsightsScreen />
      </TestWrapper>
    );

    expect(getByText('Loading your nutrition insights...')).toBeTruthy();
  });

  it('should display weekly insights when loaded', async () => {
    mockApiService.getWeeklyInsights.mockResolvedValue(mockWeeklyInsights);

    const { getByText } = render(
      <TestWrapper>
        <InsightsScreen />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(getByText('Dec 2-8, 2024')).toBeTruthy();
      expect(getByText('18 meals')).toBeTruthy();
      expect(getByText('Nutrition Balance')).toBeTruthy();
    });
  });

  it('should show empty state when no insights exist', async () => {
    mockApiService.getWeeklyInsights.mockResolvedValue([]);

    const { getByText } = render(
      <TestWrapper>
        <InsightsScreen />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(getByText('No Insights Yet')).toBeTruthy();
      expect(getByText('Take photos of your meals for a week to see your nutrition insights and trends!')).toBeTruthy();
    });
  });

  it('should display nutrition balance chart', async () => {
    mockApiService.getWeeklyInsights.mockResolvedValue(mockWeeklyInsights);

    const { getByText } = render(
      <TestWrapper>
        <InsightsScreen />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(getByText('Carbohydrates')).toBeTruthy();
      expect(getByText('Proteins')).toBeTruthy();
      expect(getByText('Fats')).toBeTruthy();
      expect(getByText('Vitamins')).toBeTruthy();
      expect(getByText('Minerals')).toBeTruthy();
      expect(getByText('Water')).toBeTruthy();
      
      // Check percentages
      expect(getByText('85%')).toBeTruthy();
      expect(getByText('72%')).toBeTruthy();
      expect(getByText('90%')).toBeTruthy();
    });
  });

  it('should show positive trends and improvement areas', async () => {
    mockApiService.getWeeklyInsights.mockResolvedValue(mockWeeklyInsights);

    const { getByText } = render(
      <TestWrapper>
        <InsightsScreen />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(getByText('This Week\'s Trends')).toBeTruthy();
      expect(getByText('Improving')).toBeTruthy();
      expect(getByText('Needs Attention')).toBeTruthy();
      
      // Check trend items
      expect(getByText('Carbohydrates')).toBeTruthy();
      expect(getByText('Water')).toBeTruthy();
      expect(getByText('Vitamins')).toBeTruthy();
      expect(getByText('Minerals')).toBeTruthy();
    });
  });

  it('should display recommendations', async () => {
    mockApiService.getWeeklyInsights.mockResolvedValue(mockWeeklyInsights);

    const { getByText } = render(
      <TestWrapper>
        <InsightsScreen />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(getByText('Recommendations')).toBeTruthy();
      expect(getByText('Great job maintaining good carbohydrate and water intake! Try to include more leafy vegetables like spinach (efo) and fruits for better vitamin and mineral balance.')).toBeTruthy();
    });
  });

  it('should show weekly stats', async () => {
    mockApiService.getWeeklyInsights.mockResolvedValue(mockWeeklyInsights);

    const { getByText } = render(
      <TestWrapper>
        <InsightsScreen />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(getByText('Weekly Stats')).toBeTruthy();
      expect(getByText('18')).toBeTruthy(); // Meals analyzed
      expect(getByText('Meals Analyzed')).toBeTruthy();
      expect(getByText('Avg Balance')).toBeTruthy();
      expect(getByText('Improvements')).toBeTruthy();
    });
  });

  it('should allow switching between weeks', async () => {
    mockApiService.getWeeklyInsights.mockResolvedValue(mockWeeklyInsights);

    const { getByText } = render(
      <TestWrapper>
        <InsightsScreen />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(getByText('Dec 2-8, 2024')).toBeTruthy();
      expect(getByText('Nov 25 - Dec 1, 2024')).toBeTruthy();
    });

    // Switch to previous week
    const previousWeekButton = getByText('Nov 25 - Dec 1, 2024');
    fireEvent.press(previousWeekButton);

    await waitFor(() => {
      expect(getByText('15 meals')).toBeTruthy(); // Should show previous week's data
    });
  });

  it('should handle error state', async () => {
    mockApiService.getWeeklyInsights.mockRejectedValue({
      userMessage: 'Failed to load insights',
    });

    const { getByText } = render(
      <TestWrapper>
        <InsightsScreen />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(getByText('Failed to Load Insights')).toBeTruthy();
      expect(getByText('Failed to load insights')).toBeTruthy();
    });
  });

  it('should calculate average balance correctly', async () => {
    mockApiService.getWeeklyInsights.mockResolvedValue(mockWeeklyInsights);

    const { getByText } = render(
      <TestWrapper>
        <InsightsScreen />
      </TestWrapper>
    );

    await waitFor(() => {
      // Average of 85+72+65+45+38+90 = 395/6 = 65.83, rounded to 66%
      expect(getByText('66%')).toBeTruthy();
    });
  });

  it('should show correct number of improvements', async () => {
    mockApiService.getWeeklyInsights.mockResolvedValue(mockWeeklyInsights);

    const { getByText } = render(
      <TestWrapper>
        <InsightsScreen />
      </TestWrapper>
    );

    await waitFor(() => {
      // Should show 2 improvements (carbohydrates, water)
      expect(getByText('2')).toBeTruthy();
    });
  });
});