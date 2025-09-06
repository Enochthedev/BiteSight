/**
 * History screen - displays meal history and management
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  Alert,
  Image,
} from 'react-native';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { colors, typography, spacing } from '@/styles';
import { NavigationParamList, MealHistory, MealAnalysis } from '@/types';
import { apiService } from '@/services/api';
import { offlineStorage } from '@/services/offlineStorage';
import Icon from 'react-native-vector-icons/MaterialIcons';

type HistoryScreenNavigationProp = StackNavigationProp<NavigationParamList, 'History'>;

interface MealHistoryItem extends MealAnalysis {
  feedbackScore?: number;
  thumbnail?: string;
}

export const HistoryScreen: React.FC = () => {
  const navigation = useNavigation<HistoryScreenNavigationProp>();

  const [meals, setMeals] = useState<MealHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  useFocusEffect(
    useCallback(() => {
      loadMealHistory(true);
    }, [])
  );

  const loadMealHistory = async (refresh: boolean = false) => {
    try {
      if (refresh) {
        setLoading(true);
        setError(null);
      }

      const offset = refresh ? 0 : meals.length;
      const limit = 20;

      const history = await apiService.getMealHistory(limit, offset);
      
      // Transform meals to include additional UI data
      const transformedMeals: MealHistoryItem[] = history.meals.map(meal => ({
        ...meal,
        feedbackScore: Math.floor(Math.random() * 40) + 60, // Mock score 60-100
        thumbnail: meal.imagePath, // In real app, this would be a thumbnail URL
      }));

      if (refresh) {
        setMeals(transformedMeals);
      } else {
        setMeals(prev => [...prev, ...transformedMeals]);
      }

      setHasMore(history.hasMore);
      setLoading(false);
      setRefreshing(false);
      setLoadingMore(false);

    } catch (err: any) {
      console.error('Error loading meal history:', err);
      
      if (refresh) {
        setLoading(false);
        setRefreshing(false);
      } else {
        setLoadingMore(false);
      }

      // Try to load from cache if network error
      if (err.errorCode === 'NETWORK_ERROR' || err.errorCode === 'OFFLINE') {
        try {
          const cachedMeals = await offlineStorage.getCachedMeals();
          const transformedCached: MealHistoryItem[] = cachedMeals.map(cached => ({
            ...cached.analysis,
            feedbackScore: Math.floor(Math.random() * 40) + 60,
            thumbnail: cached.analysis.imagePath,
          }));
          
          if (refresh) {
            setMeals(transformedCached);
          }
          setError(null);
        } catch (cacheError) {
          setError(err.userMessage || 'Failed to load meal history');
        }
      } else {
        setError(err.userMessage || 'Failed to load meal history');
      }
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadMealHistory(true);
  };

  const handleLoadMore = () => {
    if (!loadingMore && hasMore && !loading) {
      setLoadingMore(true);
      loadMealHistory(false);
    }
  };

  const handleMealPress = (meal: MealHistoryItem) => {
    // Navigate to feedback screen with meal data
    navigation.navigate('Feedback', {
      feedbackData: {
        mealId: meal.id,
        detectedFoods: meal.detectedFoods,
        missingFoodGroups: [],
        recommendations: [],
        overallBalanceScore: meal.feedbackScore || 0,
        feedbackMessage: 'View your previous meal analysis and feedback.',
      },
    });
  };

  const handleDeleteMeal = (mealId: string) => {
    Alert.alert(
      'Delete Meal',
      'Are you sure you want to delete this meal from your history?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => deleteMeal(mealId),
        },
      ]
    );
  };

  const deleteMeal = async (mealId: string) => {
    try {
      await apiService.delete(`/meals/${mealId}`);
      setMeals(prev => prev.filter(meal => meal.id !== mealId));
    } catch (err: any) {
      Alert.alert('Error', err.userMessage || 'Failed to delete meal');
    }
  };

  const handleClearHistory = () => {
    Alert.alert(
      'Clear History',
      'Are you sure you want to clear all your meal history? This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear All',
          style: 'destructive',
          onPress: clearAllHistory,
        },
      ]
    );
  };

  const clearAllHistory = async () => {
    try {
      await apiService.delete('/meals/history');
      setMeals([]);
    } catch (err: any) {
      Alert.alert('Error', err.userMessage || 'Failed to clear history');
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) return 'Today';
    if (diffDays === 2) return 'Yesterday';
    if (diffDays <= 7) return `${diffDays - 1} days ago`;
    
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    });
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return colors.success;
    if (score >= 60) return colors.warning;
    return colors.error;
  };

  const renderMealItem = ({ item }: { item: MealHistoryItem }) => (
    <TouchableOpacity onPress={() => handleMealPress(item)}>
      <Card style={styles.mealCard}>
        <View style={styles.mealHeader}>
          <View style={styles.mealInfo}>
            <Text style={styles.mealDate}>{formatDate(item.uploadDate)}</Text>
            <Text style={styles.mealTime}>
              {new Date(item.uploadDate).toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
              })}
            </Text>
          </View>
          <View style={styles.mealActions}>
            {item.feedbackScore && (
              <View style={[styles.scoreChip, { backgroundColor: getScoreColor(item.feedbackScore) }]}>
                <Text style={styles.scoreChipText}>{item.feedbackScore}%</Text>
              </View>
            )}
            <TouchableOpacity
              onPress={() => handleDeleteMeal(item.id)}
              style={styles.deleteButton}
            >
              <Icon name="delete-outline" size={20} color={colors.error} />
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.mealContent}>
          {item.thumbnail && (
            <Image source={{ uri: item.thumbnail }} style={styles.mealThumbnail} />
          )}
          <View style={styles.mealDetails}>
            <Text style={styles.mealStatus}>
              {item.analysisStatus === 'completed' ? 'Analysis Complete' : 'Processing...'}
            </Text>
            {item.detectedFoods && item.detectedFoods.length > 0 && (
              <Text style={styles.detectedFoods} numberOfLines={2}>
                {item.detectedFoods.map(food => food.foodName).join(', ')}
              </Text>
            )}
          </View>
        </View>
      </Card>
    </TouchableOpacity>
  );

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Icon name="restaurant" size={80} color={colors.gray} />
      <Text style={styles.emptyTitle}>No Meals Yet</Text>
      <Text style={styles.emptyMessage}>
        Start taking photos of your meals to build your nutrition history!
      </Text>
      <Button
        title="Take First Photo"
        onPress={() => navigation.navigate('Camera')}
        style={styles.emptyButton}
      />
    </View>
  );

  const renderFooter = () => {
    if (!loadingMore) return null;
    return (
      <View style={styles.footerLoader}>
        <LoadingSpinner size="small" message="Loading more meals..." />
      </View>
    );
  };

  if (loading && meals.length === 0) {
    return (
      <View style={styles.loadingContainer}>
        <LoadingSpinner message="Loading your meal history..." />
      </View>
    );
  }

  if (error && meals.length === 0) {
    return (
      <View style={styles.errorContainer}>
        <Card style={styles.errorCard}>
          <Icon name="error-outline" size={48} color={colors.error} />
          <Text style={styles.errorTitle}>Failed to Load History</Text>
          <Text style={styles.errorMessage}>{error}</Text>
          <Button
            title="Try Again"
            onPress={() => loadMealHistory(true)}
            style={styles.retryButton}
          />
        </Card>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {meals.length > 0 && (
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Meal History</Text>
          <TouchableOpacity onPress={handleClearHistory} style={styles.clearButton}>
            <Text style={styles.clearButtonText}>Clear All</Text>
          </TouchableOpacity>
        </View>
      )}

      <FlatList
        data={meals}
        renderItem={renderMealItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={[
          styles.listContent,
          meals.length === 0 && styles.emptyListContent,
        ]}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.5}
        ListFooterComponent={renderFooter}
        ListEmptyComponent={renderEmptyState}
        showsVerticalScrollIndicator={false}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.lightGray,
  },
  headerTitle: {
    ...typography.h5,
  },
  clearButton: {
    padding: spacing.sm,
  },
  clearButtonText: {
    ...typography.body2,
    color: colors.error,
    fontWeight: '600',
  },
  listContent: {
    padding: spacing.md,
  },
  emptyListContent: {
    flexGrow: 1,
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
  mealCard: {
    marginBottom: spacing.md,
  },
  mealHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  mealInfo: {
    flex: 1,
  },
  mealDate: {
    ...typography.subtitle1,
    fontWeight: '600',
  },
  mealTime: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  mealActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  scoreChip: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: 12,
  },
  scoreChipText: {
    ...typography.caption,
    color: colors.white,
    fontWeight: '600',
  },
  deleteButton: {
    padding: spacing.sm,
  },
  mealContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  mealThumbnail: {
    width: 60,
    height: 60,
    borderRadius: 8,
    marginRight: spacing.md,
  },
  mealDetails: {
    flex: 1,
  },
  mealStatus: {
    ...typography.body2,
    fontWeight: '500',
    marginBottom: 4,
  },
  detectedFoods: {
    ...typography.caption,
    color: colors.textSecondary,
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
    marginBottom: spacing.xl,
  },
  emptyButton: {
    paddingHorizontal: spacing.xl,
  },
  footerLoader: {
    padding: spacing.lg,
  },
});