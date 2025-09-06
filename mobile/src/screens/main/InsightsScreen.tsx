/**
 * Insights screen - displays weekly insights and nutrition visualization
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Dimensions,
  TouchableOpacity,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { Card } from '@/components/Card';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { colors, typography, spacing } from '@/styles';
import { WeeklyInsight, FoodClass } from '@/types';
import { apiService } from '@/services/api';
import Icon from 'react-native-vector-icons/MaterialIcons';

const { width: screenWidth } = Dimensions.get('window');

const FOOD_CLASS_COLORS: Record<FoodClass, string> = {
  carbohydrates: colors.carbohydrates,
  proteins: colors.proteins,
  fats: colors.fats,
  vitamins: colors.vitamins,
  minerals: colors.minerals,
  water: colors.water,
};

const FOOD_CLASS_ICONS: Record<FoodClass, string> = {
  carbohydrates: 'grain',
  proteins: 'egg',
  fats: 'opacity',
  vitamins: 'local-florist',
  minerals: 'diamond',
  water: 'water-drop',
};

export const InsightsScreen: React.FC = () => {
  const [insights, setInsights] = useState<WeeklyInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedWeek, setSelectedWeek] = useState(0);

  useFocusEffect(
    useCallback(() => {
      loadWeeklyInsights();
    }, [])
  );

  const loadWeeklyInsights = async () => {
    try {
      setLoading(true);
      setError(null);

      // Mock data for demonstration - in real app this would come from API
      const mockInsights: WeeklyInsight[] = [
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

      setInsights(mockInsights);
      setLoading(false);
      setRefreshing(false);

    } catch (err: any) {
      console.error('Error loading weekly insights:', err);
      setLoading(false);
      setRefreshing(false);
      setError(err.userMessage || 'Failed to load insights');
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadWeeklyInsights();
  };

  const renderNutritionChart = (nutritionBalance: WeeklyInsight['nutritionBalance']) => {
    const chartWidth = screenWidth - (spacing.md * 4); // Account for card padding
    const maxBarWidth = chartWidth - 100; // Leave space for labels

    return (
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>Nutrition Balance</Text>
        {Object.entries(nutritionBalance).map(([foodClass, percentage]) => (
          <View key={foodClass} style={styles.chartRow}>
            <View style={styles.chartLabel}>
              <Icon
                name={FOOD_CLASS_ICONS[foodClass as FoodClass]}
                size={16}
                color={FOOD_CLASS_COLORS[foodClass as FoodClass]}
              />
              <Text style={styles.chartLabelText}>
                {foodClass.charAt(0).toUpperCase() + foodClass.slice(1)}
              </Text>
            </View>
            <View style={styles.chartBarContainer}>
              <View
                style={[
                  styles.chartBar,
                  {
                    width: (percentage / 100) * maxBarWidth,
                    backgroundColor: FOOD_CLASS_COLORS[foodClass as FoodClass],
                  },
                ]}
              />
              <Text style={styles.chartPercentage}>{percentage}%</Text>
            </View>
          </View>
        ))}
      </View>
    );
  };

  const renderTrends = (insight: WeeklyInsight) => {
    return (
      <View style={styles.trendsContainer}>
        <Text style={styles.sectionTitle}>This Week's Trends</Text>
        
        {insight.positiveTrends.length > 0 && (
          <View style={styles.trendSection}>
            <View style={styles.trendHeader}>
              <Icon name="trending-up" size={20} color={colors.success} />
              <Text style={[styles.trendTitle, { color: colors.success }]}>
                Improving
              </Text>
            </View>
            <View style={styles.trendItems}>
              {insight.positiveTrends.map((trend, index) => (
                <View key={index} style={styles.trendChip}>
                  <Text style={styles.trendChipText}>
                    {trend.charAt(0).toUpperCase() + trend.slice(1)}
                  </Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {insight.improvementAreas.length > 0 && (
          <View style={styles.trendSection}>
            <View style={styles.trendHeader}>
              <Icon name="trending-down" size={20} color={colors.warning} />
              <Text style={[styles.trendTitle, { color: colors.warning }]}>
                Needs Attention
              </Text>
            </View>
            <View style={styles.trendItems}>
              {insight.improvementAreas.map((area, index) => (
                <View key={index} style={[styles.trendChip, styles.improvementChip]}>
                  <Text style={[styles.trendChipText, styles.improvementChipText]}>
                    {area.charAt(0).toUpperCase() + area.slice(1)}
                  </Text>
                </View>
              ))}
            </View>
          </View>
        )}
      </View>
    );
  };

  const renderWeekSelector = () => {
    return (
      <View style={styles.weekSelector}>
        {insights.map((insight, index) => (
          <TouchableOpacity
            key={insight.id}
            style={[
              styles.weekButton,
              selectedWeek === index && styles.weekButtonActive,
            ]}
            onPress={() => setSelectedWeek(index)}
          >
            <Text
              style={[
                styles.weekButtonText,
                selectedWeek === index && styles.weekButtonTextActive,
              ]}
            >
              {insight.weekPeriod}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    );
  };

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Icon name="insights" size={80} color={colors.gray} />
      <Text style={styles.emptyTitle}>No Insights Yet</Text>
      <Text style={styles.emptyMessage}>
        Take photos of your meals for a week to see your nutrition insights and trends!
      </Text>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <LoadingSpinner message="Loading your nutrition insights..." />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Card style={styles.errorCard}>
          <Icon name="error-outline" size={48} color={colors.error} />
          <Text style={styles.errorTitle}>Failed to Load Insights</Text>
          <Text style={styles.errorMessage}>{error}</Text>
        </Card>
      </View>
    );
  }

  if (insights.length === 0) {
    return (
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.emptyContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
      >
        {renderEmptyState()}
      </ScrollView>
    );
  }

  const currentInsight = insights[selectedWeek];

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
      }
    >
      {renderWeekSelector()}

      <Card style={styles.summaryCard}>
        <View style={styles.summaryHeader}>
          <Text style={styles.summaryTitle}>{currentInsight.weekPeriod}</Text>
          <View style={styles.mealsCount}>
            <Icon name="restaurant" size={16} color={colors.primary} />
            <Text style={styles.mealsCountText}>
              {currentInsight.mealsAnalyzed} meals
            </Text>
          </View>
        </View>
        {renderNutritionChart(currentInsight.nutritionBalance)}
      </Card>

      <Card style={styles.trendsCard}>
        {renderTrends(currentInsight)}
      </Card>

      <Card style={styles.recommendationsCard}>
        <Text style={styles.sectionTitle}>Recommendations</Text>
        <View style={styles.recommendationContent}>
          <Icon name="lightbulb-outline" size={24} color={colors.secondary} />
          <Text style={styles.recommendationText}>
            {currentInsight.recommendations}
          </Text>
        </View>
      </Card>

      <Card style={styles.statsCard}>
        <Text style={styles.sectionTitle}>Weekly Stats</Text>
        <View style={styles.statsGrid}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{currentInsight.mealsAnalyzed}</Text>
            <Text style={styles.statLabel}>Meals Analyzed</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>
              {Math.round(
                Object.values(currentInsight.nutritionBalance).reduce((a, b) => a + b, 0) / 6
              )}%
            </Text>
            <Text style={styles.statLabel}>Avg Balance</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{currentInsight.positiveTrends.length}</Text>
            <Text style={styles.statLabel}>Improvements</Text>
          </View>
        </View>
      </Card>
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
  emptyContent: {
    flexGrow: 1,
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
    padding: spacing.md,
  },
  errorCard: {
    alignItems: 'center',
    padding: spacing.xl,
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
  },
  weekSelector: {
    flexDirection: 'row',
    marginBottom: spacing.md,
    gap: spacing.sm,
  },
  weekButton: {
    flex: 1,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.lightGray,
  },
  weekButtonActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  weekButtonText: {
    ...typography.body2,
    textAlign: 'center',
    color: colors.textPrimary,
  },
  weekButtonTextActive: {
    color: colors.white,
    fontWeight: '600',
  },
  summaryCard: {
    marginBottom: spacing.md,
  },
  summaryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  summaryTitle: {
    ...typography.h5,
  },
  mealsCount: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  mealsCountText: {
    ...typography.body2,
    color: colors.primary,
    fontWeight: '500',
  },
  chartContainer: {
    marginTop: spacing.md,
  },
  chartTitle: {
    ...typography.subtitle1,
    marginBottom: spacing.md,
    fontWeight: '600',
  },
  chartRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  chartLabel: {
    flexDirection: 'row',
    alignItems: 'center',
    width: 100,
    gap: spacing.xs,
  },
  chartLabelText: {
    ...typography.caption,
    fontWeight: '500',
  },
  chartBarContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  chartBar: {
    height: 8,
    borderRadius: 4,
  },
  chartPercentage: {
    ...typography.caption,
    fontWeight: '600',
    minWidth: 35,
  },
  trendsCard: {
    marginBottom: spacing.md,
  },
  trendsContainer: {
    gap: spacing.md,
  },
  sectionTitle: {
    ...typography.h6,
    marginBottom: spacing.md,
  },
  trendSection: {
    gap: spacing.sm,
  },
  trendHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  trendTitle: {
    ...typography.subtitle2,
    fontWeight: '600',
  },
  trendItems: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  trendChip: {
    backgroundColor: colors.success + '20',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 16,
  },
  improvementChip: {
    backgroundColor: colors.warning + '20',
  },
  trendChipText: {
    ...typography.caption,
    color: colors.success,
    fontWeight: '500',
  },
  improvementChipText: {
    color: colors.warning,
  },
  recommendationsCard: {
    marginBottom: spacing.md,
  },
  recommendationContent: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
  },
  recommendationText: {
    ...typography.body1,
    flex: 1,
    lineHeight: 24,
  },
  statsCard: {
    marginBottom: spacing.md,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    ...typography.h4,
    color: colors.primary,
    fontWeight: 'bold',
  },
  statLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },
  emptyTitle: {
    ...typography.h4,
    marginTop: spacing.lg,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  emptyMessage: {
    ...typography.body1,
    textAlign: 'center',
    color: colors.textSecondary,
  },
});