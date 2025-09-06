/**
 * Reusable Card component
 */

import React, { ReactNode } from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import { colors, spacing } from '@/styles';

interface CardProps {
  children: ReactNode;
  style?: ViewStyle;
  padding?: number;
  margin?: number;
  elevation?: number;
}

export const Card: React.FC<CardProps> = ({
  children,
  style,
  padding = spacing.cardPadding,
  margin = 0,
  elevation = 2,
}) => {
  const cardStyle = [
    styles.card,
    {
      padding,
      margin,
      elevation,
      shadowOpacity: elevation * 0.1,
      shadowRadius: elevation * 2,
    },
    style,
  ];

  return <View style={cardStyle}>{children}</View>;
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: 8,
    shadowColor: colors.black,
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 2,
  },
});