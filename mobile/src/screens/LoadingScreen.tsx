/**
 * Loading screen displayed during app initialization
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { colors, typography, spacing } from '@/styles';

export const LoadingScreen: React.FC = () => {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Nutrition Feedback</Text>
      <LoadingSpinner message="Loading..." />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
    padding: spacing.xl,
  },
  title: {
    ...typography.h2,
    color: colors.primary,
    marginBottom: spacing.xl,
    textAlign: 'center',
  },
});