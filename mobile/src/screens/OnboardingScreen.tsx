/**
 * Onboarding screen with tutorial for new users
 */

import React, { useState, useRef } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  Dimensions, 
  FlatList,
  ViewToken
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { colors, typography, spacing } from '@/styles';
import Icon from 'react-native-vector-icons/MaterialIcons';

const { width } = Dimensions.get('window');

interface OnboardingStep {
  id: string;
  icon: string;
  title: string;
  description: string;
  details: string[];
}

const onboardingSteps: OnboardingStep[] = [
  {
    id: '1',
    icon: 'camera-alt',
    title: 'Capture Your Meals',
    description: 'Take photos of your Nigerian dishes for instant analysis',
    details: [
      'Use your camera to snap photos of meals',
      'Upload existing photos from your gallery',
      'Works with popular Nigerian foods like jollof rice, amala, efo riro',
      'Get the best results with clear, well-lit photos'
    ]
  },
  {
    id: '2',
    icon: 'psychology',
    title: 'AI-Powered Recognition',
    description: 'Advanced AI identifies foods and analyzes nutrition',
    details: [
      'Recognizes over 50 common Nigerian foods',
      'Classifies foods into 6 major nutritional groups',
      'Provides confidence scores for accuracy',
      'Analysis completes in under 5 seconds'
    ]
  },
  {
    id: '3',
    icon: 'feedback',
    title: 'Get Personalized Feedback',
    description: 'Receive culturally relevant nutrition advice',
    details: [
      'Simple, encouraging feedback in plain language',
      'Suggestions using familiar Nigerian foods',
      'Identifies missing food groups in your meal',
      'Positive reinforcement for balanced meals'
    ]
  },
  {
    id: '4',
    icon: 'history',
    title: 'Track Your Progress',
    description: 'Monitor eating patterns and see improvements',
    details: [
      'View your meal history over time',
      'Weekly insights and nutrition trends',
      'Privacy-first: you control your data',
      'Delete history anytime you want'
    ]
  },
  {
    id: '5',
    icon: 'security',
    title: 'Your Privacy Matters',
    description: 'Complete control over your personal data',
    details: [
      'Explicit consent before storing any data',
      'All data encrypted and secure',
      'Easy data deletion options',
      'No sharing without your permission'
    ]
  }
];

export const OnboardingScreen: React.FC = () => {
  const navigation = useNavigation();
  const [currentStep, setCurrentStep] = useState(0);
  const flatListRef = useRef<FlatList>(null);

  const handleGetStarted = () => {
    (navigation as any).navigate('Auth');
  };

  const handleNext = () => {
    if (currentStep < onboardingSteps.length - 1) {
      const nextStep = currentStep + 1;
      setCurrentStep(nextStep);
      try {
        flatListRef.current?.scrollToIndex({ index: nextStep, animated: true });
      } catch (error) {
        // Fallback for testing environment
        console.warn('ScrollToIndex failed:', error);
      }
    } else {
      handleGetStarted();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      const prevStep = currentStep - 1;
      setCurrentStep(prevStep);
      try {
        flatListRef.current?.scrollToIndex({ index: prevStep, animated: true });
      } catch (error) {
        // Fallback for testing environment
        console.warn('ScrollToIndex failed:', error);
      }
    }
  };

  const handleSkip = () => {
    handleGetStarted();
  };

  const onViewableItemsChanged = ({ viewableItems }: { viewableItems: ViewToken[] }) => {
    if (viewableItems.length > 0) {
      const index = viewableItems[0].index;
      if (index !== null) {
        setCurrentStep(index);
      }
    }
  };

  const renderStep = ({ item }: { item: OnboardingStep }) => (
    <View style={styles.stepContainer}>
      <Card style={styles.stepCard}>
        <View style={styles.stepHeader}>
          <View style={styles.iconContainer}>
            <Icon name={item.icon} size={60} color={colors.primary} />
          </View>
          <Text style={styles.stepTitle}>{item.title}</Text>
          <Text style={styles.stepDescription}>{item.description}</Text>
        </View>
        
        <View style={styles.stepDetails}>
          {item.details.map((detail, index) => (
            <View key={index} style={styles.detailItem}>
              <Icon name="check-circle" size={20} color={colors.success} />
              <Text style={styles.detailText}>{detail}</Text>
            </View>
          ))}
        </View>
      </Card>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Welcome to Nutrition Feedback</Text>
        <Text style={styles.subtitle}>
          Learn how to get the most out of your nutrition journey
        </Text>
      </View>

      <FlatList
        ref={flatListRef}
        data={onboardingSteps}
        renderItem={renderStep}
        keyExtractor={(item) => item.id}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onViewableItemsChanged={onViewableItemsChanged}
        viewabilityConfig={{ itemVisiblePercentThreshold: 50 }}
        getItemLayout={(data, index) => ({
          length: width,
          offset: width * index,
          index,
        })}
        style={styles.stepsList}
      />

      <View style={styles.pagination}>
        {onboardingSteps.map((_, index) => (
          <View
            key={index}
            style={[
              styles.paginationDot,
              index === currentStep && styles.paginationDotActive
            ]}
          />
        ))}
      </View>

      <View style={styles.navigation}>
        <Button
          title="Skip"
          onPress={handleSkip}
          variant="text"
          style={styles.skipButton}
        />
        
        <View style={styles.navigationButtons}>
          {currentStep > 0 && (
            <Button
              title="Previous"
              onPress={handlePrevious}
              variant="outline"
              style={styles.navButton}
            />
          )}
          
          <Button
            title={currentStep === onboardingSteps.length - 1 ? "Get Started" : "Next"}
            onPress={handleNext}
            style={styles.navButton}
          />
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    alignItems: 'center',
    paddingHorizontal: spacing.screenPadding,
    paddingTop: spacing.xxl,
    paddingBottom: spacing.lg,
  },
  title: {
    ...typography.h2,
    textAlign: 'center',
    marginBottom: spacing.sm,
    color: colors.primary,
  },
  subtitle: {
    ...typography.body1,
    textAlign: 'center',
    color: colors.textSecondary,
  },
  stepsList: {
    flex: 1,
  },
  stepContainer: {
    width,
    paddingHorizontal: spacing.screenPadding,
  },
  stepCard: {
    flex: 1,
    padding: spacing.lg,
    marginHorizontal: spacing.sm,
  },
  stepHeader: {
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  iconContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  stepTitle: {
    ...typography.h3,
    textAlign: 'center',
    marginBottom: spacing.sm,
    color: colors.text,
  },
  stepDescription: {
    ...typography.body1,
    textAlign: 'center',
    color: colors.textSecondary,
  },
  stepDetails: {
    flex: 1,
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: spacing.md,
  },
  detailText: {
    ...typography.body2,
    marginLeft: spacing.sm,
    flex: 1,
    color: colors.text,
  },
  pagination: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: spacing.lg,
  },
  paginationDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.gray,
    marginHorizontal: 4,
  },
  paginationDotActive: {
    backgroundColor: colors.primary,
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  navigation: {
    paddingHorizontal: spacing.screenPadding,
    paddingBottom: spacing.xl,
  },
  skipButton: {
    alignSelf: 'flex-end',
    marginBottom: spacing.md,
  },
  navigationButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  navButton: {
    flex: 1,
    marginHorizontal: spacing.xs,
  },
});