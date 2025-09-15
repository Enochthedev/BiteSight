/**
 * Camera screen for capturing and selecting meal images
 */

import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Button } from '@/components/Button';
import { ImagePreview } from '@/components/ImagePreview';
import { CameraCapture } from '@/components/CameraCapture';
import { colors, typography, spacing } from '@/styles';
import { MealImage, CameraPermissions } from '@/types';
import { cameraService, ImageQualityResult } from '@/services/cameraService';
import { MaterialIcons } from '@expo/vector-icons';

type CameraMode = 'selection' | 'camera' | 'preview';

export const CameraScreen: React.FC = () => {
  const [mode, setMode] = useState<CameraMode>('selection');
  const [selectedImage, setSelectedImage] = useState<MealImage | null>(null);
  const [permissions, setPermissions] = useState<CameraPermissions>({ camera: false, storage: false });
  const [isLoading, setIsLoading] = useState(false);
  const [qualityResult, setQualityResult] = useState<ImageQualityResult | null>(null);

  useEffect(() => {
    checkPermissions();
  }, []);

  const checkPermissions = async () => {
    try {
      const perms = await cameraService.checkPermissions();
      setPermissions(perms);
    } catch (error) {
      console.error('Error checking permissions:', error);
    }
  };

  const handleCameraCapture = () => {
    if (!permissions.camera) {
      requestPermissions();
      return;
    }
    setMode('camera');
  };

  const handleGallerySelect = async () => {
    if (!permissions.storage) {
      await requestPermissions();
      return;
    }

    try {
      setIsLoading(true);
      const image = await cameraService.selectFromGallery();
      
      if (image) {
        setSelectedImage(image);
        const quality = cameraService.validateImageQuality(image);
        setQualityResult(quality);
        setMode('preview');
      }
    } catch (error) {
      console.error('Error selecting from gallery:', error);
      Alert.alert(
        'Gallery Error',
        'Failed to select image from gallery. Please try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setIsLoading(false);
    }
  };

  const requestPermissions = async () => {
    try {
      const perms = await cameraService.requestPermissions();
      setPermissions(perms);
    } catch (error) {
      console.error('Error requesting permissions:', error);
    }
  };

  const handleImageCaptured = (image: MealImage) => {
    setSelectedImage(image);
    const quality = cameraService.validateImageQuality(image);
    setQualityResult(quality);
    setMode('preview');
  };

  const handleRetakePhoto = () => {
    setSelectedImage(null);
    setQualityResult(null);
    setMode('selection');
  };

  const handleConfirmImage = async () => {
    if (!selectedImage) return;

    try {
      setIsLoading(true);
      
      // Here we would typically upload the image to the backend
      // For now, we'll navigate to the analysis screen
      // This will be implemented in task 9.3 (API integration)
      
      // Simulate processing delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Navigate to analysis screen with the image
      router.push({
        pathname: '/analysis',
        params: {
          mealId: `temp_${Date.now()}`,
          imageUri: selectedImage.uri 
        }
      });
      
    } catch (error) {
      console.error('Error processing image:', error);
      Alert.alert(
        'Processing Error',
        'Failed to process the image. Please try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleCloseCamera = () => {
    setMode('selection');
  };

  if (mode === 'camera') {
    return (
      <CameraCapture
        onImageCaptured={handleImageCaptured}
        onClose={handleCloseCamera}
      />
    );
  }

  if (mode === 'preview' && selectedImage) {
    return (
      <SafeAreaView style={styles.container}>
        <ImagePreview
          image={selectedImage}
          onConfirm={handleConfirmImage}
          onRetake={handleRetakePhoto}
          isLoading={isLoading}
          qualityIssues={qualityResult?.issues}
        />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <View style={styles.header}>
          <MaterialIcons name="camera-alt" size={80} color={colors.primary} />
          <Text style={styles.title}>Capture Your Meal</Text>
          <Text style={styles.subtitle}>
            Take a photo or select from your gallery to get instant nutrition feedback
          </Text>
        </View>

        <View style={styles.options}>
          <Button
            title="Take Photo"
            onPress={handleCameraCapture}
            variant="primary"
            size="large"
            fullWidth
            style={styles.optionButton}
          />
          
          <Button
            title="Choose from Gallery"
            onPress={handleGallerySelect}
            variant="outline"
            size="large"
            fullWidth
            style={styles.optionButton}
            loading={isLoading}
          />
        </View>

        <View style={styles.tips}>
          <Text style={styles.tipsTitle}>For best results:</Text>
          <View style={styles.tipItem}>
            <MaterialIcons name="wb-sunny" size={16} color={colors.textSecondary} />
            <Text style={styles.tipText}>Use good lighting</Text>
          </View>
          <View style={styles.tipItem}>
            <MaterialIcons name="center-focus-strong" size={16} color={colors.textSecondary} />
            <Text style={styles.tipText}>Keep food in center of frame</Text>
          </View>
          <View style={styles.tipItem}>
            <MaterialIcons name="straighten" size={16} color={colors.textSecondary} />
            <Text style={styles.tipText}>Hold camera steady</Text>
          </View>
          <View style={styles.tipItem}>
            <MaterialIcons name="visibility" size={16} color={colors.textSecondary} />
            <Text style={styles.tipText}>Ensure all food is visible</Text>
          </View>
        </View>

        {(!permissions.camera || !permissions.storage) && (
          <View style={styles.permissionNotice}>
            <MaterialIcons name="info" size={20} color={colors.warning} />
            <Text style={styles.permissionText}>
              Camera and storage permissions are required to capture and save meal photos.
            </Text>
          </View>
        )}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    flex: 1,
    padding: spacing.screenPadding,
  },
  header: {
    alignItems: 'center',
    marginBottom: spacing.xxl,
    marginTop: spacing.xl,
  },
  title: {
    ...typography.h2,
    marginTop: spacing.lg,
    marginBottom: spacing.md,
    textAlign: 'center',
    color: colors.textPrimary,
  },
  subtitle: {
    ...typography.body1,
    textAlign: 'center',
    color: colors.textSecondary,
    paddingHorizontal: spacing.md,
  },
  options: {
    marginBottom: spacing.xxl,
  },
  optionButton: {
    marginBottom: spacing.md,
  },
  tips: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.lg,
    marginBottom: spacing.lg,
  },
  tipsTitle: {
    ...typography.subtitle1,
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  tipItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  tipText: {
    ...typography.body2,
    color: colors.textSecondary,
    marginLeft: spacing.sm,
  },
  permissionNotice: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: colors.warning + '10',
    borderRadius: 8,
    padding: spacing.md,
    borderLeftWidth: 4,
    borderLeftColor: colors.warning,
  },
  permissionText: {
    ...typography.body2,
    color: colors.textSecondary,
    marginLeft: spacing.sm,
    flex: 1,
  },
});