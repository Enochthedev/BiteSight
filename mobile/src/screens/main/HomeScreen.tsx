/**
 * Home screen - main dashboard
 */

import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { useAppContext } from '@/context/AppContext';
import { colors, typography, spacing } from '@/styles';
import { MaterialIcons } from '@expo/vector-icons';

export const HomeScreen: React.FC = () => {
  const { state } = useAppContext();

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.greeting}>Hello, {state.user?.name}!</Text>
        <Text style={styles.subtitle}>Ready to analyze your next meal?</Text>
      </View>

      <Card style={styles.quickActionCard}>
        <MaterialIcons name="camera-alt" size={48} color={colors.primary} />
        <Text style={styles.quickActionTitle}>Analyze Your Meal</Text>
        <Text style={styles.quickActionDescription}>
          Take a photo of your food to get instant nutrition feedback
        </Text>
        <Button
          title="Open Camera"
          onPress={() => {/* TODO: Navigate to camera */}}
          style={styles.quickActionButton}
        />
      </Card>

      <View style={styles.statsSection}>
        <Text style={styles.sectionTitle}>This Week</Text>
        
        <View style={styles.statsGrid}>
          <Card style={styles.statCard}>
            <Text style={styles.statNumber}>12</Text>
            <Text style={styles.statLabel}>Meals Analyzed</Text>
          </Card>
          
          <Card style={styles.statCard}>
            <Text style={styles.statNumber}>85%</Text>
            <Text style={styles.statLabel}>Balance Score</Text>
          </Card>
        </View>
      </View>

      <View style={styles.recentSection}>
        <Text style={styles.sectionTitle}>Recent Activity</Text>
        
        <Card style={styles.activityCard}>
          <View style={styles.activityItem}>
            <MaterialIcons name="restaurant" size={24} color={colors.secondary} />
            <View style={styles.activityContent}>
              <Text style={styles.activityTitle}>Jollof Rice & Chicken</Text>
              <Text style={styles.activityTime}>2 hours ago</Text>
            </View>
            <Text style={styles.activityScore}>Good</Text>
          </View>
        </Card>
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
    padding: spacing.screenPadding,
  },
  header: {
    marginBottom: spacing.xl,
    paddingTop: spacing.lg,
  },
  greeting: {
    ...typography.h3,
    marginBottom: spacing.xs,
  },
  subtitle: {
    ...typography.body1,
    color: colors.textSecondary,
  },
  quickActionCard: {
    alignItems: 'center',
    marginBottom: spacing.xl,
    padding: spacing.xl,
  },
  quickActionTitle: {
    ...typography.h5,
    marginTop: spacing.md,
    marginBottom: spacing.sm,
  },
  quickActionDescription: {
    ...typography.body2,
    textAlign: 'center',
    color: colors.textSecondary,
    marginBottom: spacing.lg,
  },
  quickActionButton: {
    paddingHorizontal: spacing.xl,
  },
  statsSection: {
    marginBottom: spacing.xl,
  },
  sectionTitle: {
    ...typography.h5,
    marginBottom: spacing.md,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statCard: {
    flex: 1,
    alignItems: 'center',
    marginHorizontal: spacing.xs,
    padding: spacing.lg,
  },
  statNumber: {
    ...typography.h3,
    color: colors.primary,
    marginBottom: spacing.xs,
  },
  statLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  recentSection: {
    marginBottom: spacing.xl,
  },
  activityCard: {
    padding: 0,
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
  },
  activityContent: {
    flex: 1,
    marginLeft: spacing.md,
  },
  activityTitle: {
    ...typography.body1,
    marginBottom: spacing.xs,
  },
  activityTime: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  activityScore: {
    ...typography.label,
    color: colors.success,
  },
});