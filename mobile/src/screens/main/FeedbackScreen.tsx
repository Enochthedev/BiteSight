/**
 * Feedback screen - displays nutrition feedback and recommendations
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Share,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { colors, typography, spacing } from '@/styles';
import { NavigationParamList, NutritionFeedback, FoodClass } from '@/types';
import { apiService } from '@/services/api';
import { MaterialIcons } from '@expo/vector-icons';

const NIGERIAN_FOOD_EXAMPLES: Record<FoodClass, string[]> = {
  carbohydrates: ['Rice', 'Yam', 'Plantain', 'Cassava', 'Bread'],
  proteins: ['Beans', 'Fish', 'Chicken', 'Beef', 'Eggs'],
  fats: ['Palm oil', 'Groundnut oil', 'Avocado', 'Nuts'],
  vitamins: ['Spinach (Efo)', 'Tomatoes', 'Oranges', 'Carrots'],
  minerals: ['Leafy vegetables', 'Fish', 'Milk', 'Beans'],
  water: ['Water', 'Fresh juice', 'Coconut water'],
};

const FOOD_CLASS_COLORS: Record<FoodClass, string> = {
  carbohydrates: colors.carbohydrates,
  proteins: colors.proteins,
  fats: colors.fats,
  vitamins: colors.vitamins,
  minerals: colors.minerals,
  water: colors.water,
};

export const FeedbackScreen: React.FC = () => {
  const params = useLocalSearchParams<{
    mealId?: string;
    detectedFoods?: string;
    missingFoodGroups?: string;
    recommendations?: string;
    overallBalanceScore?: string;
    feedbackMessage?: string;
  }>();

  // Parse the feedback data from params
  const feedbackData = params.mealId ? {
    mealId: params.mealId,
    detectedFoods: params.detectedFoods ? JSON.parse(params.detectedFoods) : [],
    missingFoodGroups: params.missingFoodGroups ? JSON.parse(params.missingFoodGroups) : [],
    recommendations: params.recommendations ? JSON.parse(params.recommendations) : [],
    overallBalanceScore: params.overallBalanceScore ? parseFloat(params.overallBalanceScore) : 0,
    feedbackMessage: params.feedbackMessage || '',
  } : null;

  const [feedback, setFeedback] = useState<NutritionFeedback | null>(feedbackData);
  const [loading, setLoading] = useState(!feedbackData);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!feedbackData) {
      fetchFeedback();
    }
  }, []);

  const fetchFeedback = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // In a real implementation, we would get the meal ID from navigation params
      // For now, we'll simulate the feedback generation
      const mockFeedback: NutritionFeedback = {
        mealId: 'mock-meal-id',
        detectedFoods: [
          { foodName: 'Jollof Rice', confidence: 0.95, foodClass: 'carbohydrates' },
          { foodName: 'Fried Chicken', confidence: 0.88, foodClass: 'proteins' },
        ],
        missingFoodGroups: ['vitamins', 'minerals'],
        recommendations: [
          'Add some vegetables like spinach (efo) or ugwu to get more vitamins',
          'Include fruits like oranges or bananas for additional minerals',
          'Consider adding a side of beans for more protein variety',
        ],
        overallBalanceScore: 65,
        feedbackMessage: 'Good start! Your meal has carbohydrates and proteins, but could use more vegetables and fruits for a complete nutritional balance.',
      };

      setTimeout(() => {
        setFeedback(mockFeedback);
        setLoading(false);
      }, 1500);

    } catch (err: any) {
      setLoading(false);
      setError(err.userMessage || 'Failed to generate feedback');
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return colors.success;
    if (score >= 60) return colors.warning;
    return colors.error;
  };

  const getScoreMessage = (score: number) => {
    if (score >= 80) return 'Excellent balance!';
    if (score >= 60) return 'Good, but can improve';
    return 'Needs improvement';
  };

  const handleShare = async () => {
    if (!feedback) return;

    try {
      const shareMessage = `My meal analysis:\n\nBalance Score: ${feedback.overallBalanceScore}%\n\n${feedback.feedbackMessage}\n\nDetected foods: ${feedback.detectedFoods.map(f => f.foodName).join(', ')}\n\nShared from Nutrition Feedback App`;
      
      await Share.share({
        message: shareMessage,
        title: 'My Nutrition Feedback',
      });
    } catch (error) {
      console.error('Error sharing feedback:', error);
    }
  };

  const renderBalanceScore = () => {
    if (!feedback) return null;

    const scoreColor = getScoreColor(feedback.overallBalanceScore);
    const scoreMessage = getScoreMessage(feedback.overallBalanceScore);

    return (
      <Card style={styles.scoreCard}>
        <View style={styles.scoreHeader}>
          <Text style={styles.scoreTitle}>Nutrition Balance</Text>
          <TouchableOpacity onPress={handleShare} style={styles.shareButton}>
            <MaterialIcons name="share" size={24} color={colors.primary} />
          </TouchableOpacity>
        </View>
        <View style={styles.scoreContainer}>
          <View style={[styles.scoreCircle, { borderColor: scoreColor }]}>
            <Text style={[styles.scoreText, { color: scoreColor }]}>
              {feedback.overallBalanceScore}%
            </Text>
          </View>
          <Text style={[styles.scoreMessage, { color: scoreColor }]}>
            {scoreMessage}
          </Text>
        </View>
      </Card>
    );
  };

  const renderDetectedFoods = () => {
    if (!feedback?.detectedFoods?.length) return null;

    return (
      <Card style={styles.detectedFoodsCard}>
        <Text style={styles.sectionTitle}>What We Found</Text>
        <View style={styles.foodGrid}>
          {feedback.detectedFoods.map((food, index) => (
            <View key={index} style={styles.foodChip}>
              <View
                style={[
                  styles.foodColorIndicator,
                  { backgroundColor: FOOD_CLASS_COLORS[food.foodClass as FoodClass] },
                ]}
              />
              <Text style={styles.foodChipText}>{food.foodName}</Text>
            </View>
          ))}
        </View>
      </Card>
    );
  };

  const renderMissingGroups = () => {
    if (!feedback?.missingFoodGroups?.length) return null;

    return (
      <Card style={styles.missingGroupsCard}>
        <Text style={styles.sectionTitle}>Missing Food Groups</Text>
        {feedback.missingFoodGroups.map((group, index) => (
          <View key={index} style={styles.missingGroupItem}>
            <View style={styles.missingGroupHeader}>
              <View
                style={[
                  styles.groupColorIndicator,
                  { backgroundColor: FOOD_CLASS_COLORS[group as FoodClass] },
                ]}
              />
              <Text style={styles.missingGroupName}>
                {group.charAt(0).toUpperCase() + group.slice(1)}
              </Text>
            </View>
            <Text style={styles.missingGroupSuggestion}>
              Try: {NIGERIAN_FOOD_EXAMPLES[group as FoodClass]?.join(', ')}
            </Text>
          </View>
        ))}
      </Card>
    );
  };

  const renderRecommendations = () => {
    if (!feedback?.recommendations?.length) return null;

    return (
      <Card style={styles.recommendationsCard}>
        <Text style={styles.sectionTitle}>Recommendations</Text>
        {feedback.recommendations.map((recommendation, index) => (
          <View key={index} style={styles.recommendationItem}>
            <MaterialIcons name="lightbulb-outline" size={20} color={colors.secondary} />
            <Text style={styles.recommendationText}>{recommendation}</Text>
          </View>
        ))}
      </Card>
    );
  };

  const renderFeedbackMessage = () => {
    if (!feedback?.feedbackMessage) return null;

    return (
      <Card style={styles.messageCard}>
        <MaterialIcons name="chat-bubble-outline" size={24} color={colors.primary} />
        <Text style={styles.messageText}>{feedback.feedbackMessage}</Text>
      </Card>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <LoadingSpinner message="Generating your personalized feedback..." />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Card style={styles.errorCard}>
          <MaterialIcons name="error-outline" size={48} color={colors.error} />
          <Text style={styles.errorTitle}>Failed to Generate Feedback</Text>
          <Text style={styles.errorMessage}>{error}</Text>
          <Button
            title="Try Again"
            onPress={fetchFeedback}
            style={styles.retryButton}
          />
        </Card>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {renderBalanceScore()}
      {renderDetectedFoods()}
      {renderMissingGroups()}
      {renderRecommendations()}
      {renderFeedbackMessage()}
      
      <View style={styles.actions}>
        <Button
          title="View History"
          onPress={() => router.push('/history')}
          variant="outline"
          style={styles.actionButton}
        />
        <Button
          title="Take Another Photo"
          onPress={() => router.push('/camera')}
          style={styles.actionButton}
        />
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.md,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    backgroundColor: colors.background,
  },
  errorCard: {
    alignItems: 'center',
    padding: spacing.xl,
    margin: spacing.md,
  },
  errorTitle: {
    ...typography.h4,
    marginTop: spacing.md,
    marginBottom: spacing.sm,
    color: colors.error,
  },
  errorMessage: {
    ...typography.body1,
    textAlign: 'center',
    color: colors.textSecondary,
    marginBottom: spacing.lg,
  },
  retryButton: {
    paddingHorizontal: spacing.xl,
  },
  scoreCard: {
    marginBottom: spacing.md,
  },
  scoreHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  scoreTitle: {
    ...typography.h5,
  },
  shareButton: {
    padding: spacing.sm,
  },
  scoreContainer: {
    alignItems: 'center',
  },
  scoreCircle: {
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  scoreText: {
    ...typography.h2,
    fontWeight: 'bold',
  },
  scoreMessage: {
    ...typography.subtitle1,
    fontWeight: '600',
  },
  detectedFoodsCard: {
    marginBottom: spacing.md,
  },
  sectionTitle: {
    ...typography.h5,
    marginBottom: spacing.md,
  },
  foodGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  foodChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.lightGray,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 20,
    marginBottom: spacing.sm,
  },
  foodColorIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: spacing.sm,
  },
  foodChipText: {
    ...typography.body2,
    fontWeight: '500',
  },
  missingGroupsCard: {
    marginBottom: spacing.md,
  },
  missingGroupItem: {
    marginBottom: spacing.md,
  },
  missingGroupHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  groupColorIndicator: {
    width: 16,
    height: 16,
    borderRadius: 8,
    marginRight: spacing.sm,
  },
  missingGroupName: {
    ...typography.subtitle1,
    fontWeight: '600',
  },
  missingGroupSuggestion: {
    ...typography.body2,
    color: colors.textSecondary,
    marginLeft: spacing.lg,
  },
  recommendationsCard: {
    marginBottom: spacing.md,
  },
  recommendationItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: spacing.md,
  },
  recommendationText: {
    ...typography.body1,
    marginLeft: spacing.sm,
    flex: 1,
  },
  messageCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: spacing.lg,
  },
  messageText: {
    ...typography.body1,
    marginLeft: spacing.sm,
    flex: 1,
    fontStyle: 'italic',
  },
  actions: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.md,
  },
  actionButton: {
    flex: 1,
  },
});