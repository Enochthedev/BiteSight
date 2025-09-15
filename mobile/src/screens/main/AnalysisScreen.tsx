/**
 * Analysis screen - displays meal analysis progress and results
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  Alert,
  Animated,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { colors, typography, spacing } from '@/styles';
import { NavigationParamList, MealAnalysis, FoodDetection, AnalysisStatus } from '@/types';
import { apiService } from '@/services/api';
import { MaterialIcons } from '@expo/vector-icons';

export const AnalysisScreen: React.FC = () => {
  const { mealId, imageUri } = useLocalSearchParams<{
    mealId: string;
    imageUri: string;
  }>();

  const [analysis, setAnalysis] = useState<MealAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [progress] = useState(new Animated.Value(0));

  useEffect(() => {
    startAnalysis();
    startProgressAnimation();
  }, [mealId]);

  const startProgressAnimation = () => {
    Animated.timing(progress, {
      toValue: 1,
      duration: 5000, // 5 seconds to match expected analysis time
      useNativeDriver: false,
    }).start();
  };

  const startAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);

      // Poll for analysis results
      const pollInterval = setInterval(async () => {
        try {
          const result = await apiService.get<MealAnalysis>(`/meals/${mealId}/analysis`);
          setAnalysis(result);

          if (result.analysisStatus === 'completed') {
            clearInterval(pollInterval);
            setLoading(false);
            // Navigate to feedback screen after a short delay
            setTimeout(() => {
              router.push({
                pathname: '/feedback',
                params: {
                  mealId: result.id,
                  detectedFoods: result.detectedFoods,
                  missingFoodGroups: [],
                  recommendations: [],
                  overallBalanceScore: 0,
                  feedbackMessage: ''
                }
              });
            }, 1500);
          } else if (result.analysisStatus === 'failed') {
            clearInterval(pollInterval);
            setLoading(false);
            setError('Analysis failed. Please try again.');
          }
        } catch (err: any) {
          console.error('Error polling analysis:', err);
          if (err.errorCode !== 'NETWORK_ERROR') {
            clearInterval(pollInterval);
            setLoading(false);
            setError(err.userMessage || 'Failed to analyze meal');
          }
        }
      }, 2000);

      // Cleanup interval after 30 seconds
      setTimeout(() => {
        clearInterval(pollInterval);
        if (loading) {
          setLoading(false);
          setError('Analysis is taking longer than expected. Please try again.');
        }
      }, 30000);

    } catch (err: any) {
      setLoading(false);
      setError(err.userMessage || 'Failed to start analysis');
    }
  };

  const handleRetry = () => {
    setAnalysis(null);
    setError(null);
    progress.setValue(0);
    startAnalysis();
    startProgressAnimation();
  };

  const handleCancel = () => {
    Alert.alert(
      'Cancel Analysis',
      'Are you sure you want to cancel the meal analysis?',
      [
        { text: 'Continue Analysis', style: 'cancel' },
        { 
          text: 'Cancel', 
          style: 'destructive',
          onPress: () => router.back()
        },
      ]
    );
  };

  const renderProgressBar = () => {
    return (
      <View style={styles.progressContainer}>
        <Text style={styles.progressLabel}>Analyzing your meal...</Text>
        <View style={styles.progressBar}>
          <Animated.View
            style={[
              styles.progressFill,
              {
                width: progress.interpolate({
                  inputRange: [0, 1],
                  outputRange: ['0%', '100%'],
                }),
              },
            ]}
          />
        </View>
        <Text style={styles.progressText}>
          {analysis?.analysisStatus === 'processing' ? 'Processing image...' : 'Starting analysis...'}
        </Text>
      </View>
    );
  };

  const renderDetectedFoods = () => {
    if (!analysis?.detectedFoods?.length) return null;

    return (
      <Card style={styles.detectedFoodsCard}>
        <Text style={styles.sectionTitle}>Detected Foods</Text>
        {analysis.detectedFoods.map((food, index) => (
          <View key={index} style={styles.foodItem}>
            <View style={styles.foodInfo}>
              <Text style={styles.foodName}>{food.foodName}</Text>
              <Text style={styles.foodClass}>{food.foodClass}</Text>
            </View>
            <View style={styles.confidenceContainer}>
              <Text style={styles.confidenceText}>
                {Math.round(food.confidence * 100)}%
              </Text>
            </View>
          </View>
        ))}
      </Card>
    );
  };

  if (error) {
    return (
      <View style={styles.container}>
        <Card style={styles.errorCard}>
          <MaterialIcons name="error-outline" size={48} color={colors.error} />
          <Text style={styles.errorTitle}>Analysis Failed</Text>
          <Text style={styles.errorMessage}>{error}</Text>
          <View style={styles.errorActions}>
            <Button
              title="Try Again"
              onPress={handleRetry}
              style={styles.retryButton}
            />
            <Button
              title="Go Back"
              onPress={() => router.back()}
              variant="outline"
              style={styles.backButton}
            />
          </View>
        </Card>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {imageUri && (
        <Card style={styles.imageCard}>
          <Image source={{ uri: imageUri }} style={styles.mealImage} />
        </Card>
      )}

      {loading ? (
        <Card style={styles.analysisCard}>
          <LoadingSpinner message="Analyzing your meal..." />
          {renderProgressBar()}
          <Button
            title="Cancel"
            onPress={handleCancel}
            variant="outline"
            style={styles.cancelButton}
          />
        </Card>
      ) : (
        <>
          {renderDetectedFoods()}
          <Card style={styles.completedCard}>
            <MaterialIcons name="check-circle" size={48} color={colors.success} />
            <Text style={styles.completedTitle}>Analysis Complete!</Text>
            <Text style={styles.completedMessage}>
              Your meal has been analyzed. Preparing your personalized feedback...
            </Text>
          </Card>
        </>
      )}
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
  imageCard: {
    marginBottom: spacing.md,
  },
  mealImage: {
    width: '100%',
    height: 200,
    borderRadius: 8,
  },
  analysisCard: {
    alignItems: 'center',
    padding: spacing.xl,
  },
  progressContainer: {
    width: '100%',
    marginTop: spacing.lg,
    marginBottom: spacing.md,
  },
  progressLabel: {
    ...typography.subtitle1,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  progressBar: {
    height: 8,
    backgroundColor: colors.lightGray,
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: spacing.sm,
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: 4,
  },
  progressText: {
    ...typography.body2,
    textAlign: 'center',
    color: colors.textSecondary,
  },
  cancelButton: {
    marginTop: spacing.lg,
    paddingHorizontal: spacing.xl,
  },
  detectedFoodsCard: {
    marginBottom: spacing.md,
  },
  sectionTitle: {
    ...typography.h5,
    marginBottom: spacing.md,
  },
  foodItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.lightGray,
  },
  foodInfo: {
    flex: 1,
  },
  foodName: {
    ...typography.subtitle1,
    marginBottom: 2,
  },
  foodClass: {
    ...typography.caption,
    color: colors.textSecondary,
    textTransform: 'capitalize',
  },
  confidenceContainer: {
    backgroundColor: colors.primaryLight,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: 12,
  },
  confidenceText: {
    ...typography.caption,
    color: colors.white,
    fontWeight: '600',
  },
  completedCard: {
    alignItems: 'center',
    padding: spacing.xl,
  },
  completedTitle: {
    ...typography.h4,
    marginTop: spacing.md,
    marginBottom: spacing.sm,
    color: colors.success,
  },
  completedMessage: {
    ...typography.body1,
    textAlign: 'center',
    color: colors.textSecondary,
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
  errorActions: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  retryButton: {
    flex: 1,
  },
  backButton: {
    flex: 1,
  },
});