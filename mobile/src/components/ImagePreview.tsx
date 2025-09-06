/**
 * Image preview component for confirming captured/selected images
 */

import React from 'react';
import {
  View,
  Image,
  StyleSheet,
  Dimensions,
  Text,
  ScrollView,
} from 'react-native';
import { Button } from './Button';
import { colors, typography, spacing } from '@/styles';
import { MealImage } from '@/types';
import Icon from 'react-native-vector-icons/MaterialIcons';

interface ImagePreviewProps {
  image: MealImage;
  onConfirm: () => void;
  onRetake: () => void;
  isLoading?: boolean;
  qualityIssues?: string[];
}

const { width: screenWidth } = Dimensions.get('window');
const imageSize = screenWidth - (spacing.screenPadding * 2);

export const ImagePreview: React.FC<ImagePreviewProps> = ({
  image,
  onConfirm,
  onRetake,
  isLoading = false,
  qualityIssues = [],
}) => {
  const hasQualityIssues = qualityIssues.length > 0;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <View style={styles.header}>
        <Text style={styles.title}>Preview Your Meal</Text>
        <Text style={styles.subtitle}>
          Make sure your meal is clearly visible and well-lit
        </Text>
      </View>

      <View style={styles.imageContainer}>
        <Image source={{ uri: image.uri }} style={styles.image} resizeMode="cover" />
        
        {hasQualityIssues && (
          <View style={styles.qualityOverlay}>
            <Icon name="warning" size={24} color={colors.warning} />
          </View>
        )}
      </View>

      <View style={styles.imageInfo}>
        <Text style={styles.fileName}>{image.fileName}</Text>
        {image.fileSize && (
          <Text style={styles.fileSize}>
            {(image.fileSize / 1024 / 1024).toFixed(2)} MB
          </Text>
        )}
      </View>

      {hasQualityIssues && (
        <View style={styles.qualityIssues}>
          <View style={styles.issueHeader}>
            <Icon name="info" size={20} color={colors.warning} />
            <Text style={styles.issueTitle}>Image Quality Issues</Text>
          </View>
          {qualityIssues.map((issue, index) => (
            <Text key={index} style={styles.issueText}>
              • {issue}
            </Text>
          ))}
        </View>
      )}

      <View style={styles.tips}>
        <Text style={styles.tipsTitle}>Tips for better results:</Text>
        <Text style={styles.tipText}>• Ensure good lighting</Text>
        <Text style={styles.tipText}>• Keep the camera steady</Text>
        <Text style={styles.tipText}>• Include the entire meal in the frame</Text>
        <Text style={styles.tipText}>• Avoid shadows on the food</Text>
      </View>

      <View style={styles.actions}>
        <Button
          title="Retake Photo"
          onPress={onRetake}
          variant="outline"
          style={styles.retakeButton}
          disabled={isLoading}
        />
        <Button
          title={hasQualityIssues ? "Use Anyway" : "Analyze Meal"}
          onPress={onConfirm}
          variant="primary"
          style={styles.confirmButton}
          loading={isLoading}
          disabled={isLoading}
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
  contentContainer: {
    padding: spacing.screenPadding,
  },
  header: {
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  title: {
    ...typography.h2,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  subtitle: {
    ...typography.body2,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  imageContainer: {
    alignItems: 'center',
    marginBottom: spacing.md,
    position: 'relative',
  },
  image: {
    width: imageSize,
    height: imageSize,
    borderRadius: 12,
    backgroundColor: colors.lightGray,
  },
  qualityOverlay: {
    position: 'absolute',
    top: spacing.md,
    right: spacing.md,
    backgroundColor: colors.white,
    borderRadius: 20,
    padding: spacing.sm,
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  imageInfo: {
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  fileName: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  fileSize: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  qualityIssues: {
    backgroundColor: colors.warning + '10',
    borderRadius: 8,
    padding: spacing.md,
    marginBottom: spacing.lg,
    borderLeftWidth: 4,
    borderLeftColor: colors.warning,
  },
  issueHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  issueTitle: {
    ...typography.subtitle2,
    color: colors.warning,
    marginLeft: spacing.sm,
  },
  issueText: {
    ...typography.body2,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  tips: {
    backgroundColor: colors.surface,
    borderRadius: 8,
    padding: spacing.md,
    marginBottom: spacing.xl,
  },
  tipsTitle: {
    ...typography.subtitle2,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  tipText: {
    ...typography.body2,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  actions: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  retakeButton: {
    flex: 1,
  },
  confirmButton: {
    flex: 1,
  },
});