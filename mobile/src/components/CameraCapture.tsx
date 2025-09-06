/**
 * Camera capture component with live camera view and capture controls
 */

import React, { useRef, useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  Dimensions,
  Text,
  TouchableOpacity,
  Alert,
  StatusBar,
} from 'react-native';
import { RNCamera } from 'react-native-camera';
import { colors, spacing, typography } from '@/styles';
import { MealImage } from '@/types';
import Icon from 'react-native-vector-icons/MaterialIcons';

interface CameraCaptureProps {
  onImageCaptured: (image: MealImage) => void;
  onClose: () => void;
}

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

export const CameraCapture: React.FC<CameraCaptureProps> = ({
  onImageCaptured,
  onClose,
}) => {
  const cameraRef = useRef<RNCamera>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [flashMode, setFlashMode] = useState(RNCamera.Constants.FlashMode.auto);
  const [cameraType, setCameraType] = useState(RNCamera.Constants.Type.back);

  useEffect(() => {
    // Set status bar to hidden for full screen camera
    StatusBar.setHidden(true);
    
    return () => {
      StatusBar.setHidden(false);
    };
  }, []);

  const captureImage = async () => {
    if (!cameraRef.current || isCapturing) return;

    try {
      setIsCapturing(true);
      
      const options = {
        quality: 0.8,
        base64: false,
        skipProcessing: false,
        forceUpOrientation: true,
        fixOrientation: true,
      };

      const data = await cameraRef.current.takePictureAsync(options);
      
      const mealImage: MealImage = {
        uri: data.uri,
        type: 'image/jpeg',
        fileName: `meal_${Date.now()}.jpg`,
      };

      onImageCaptured(mealImage);
    } catch (error) {
      console.error('Error capturing image:', error);
      Alert.alert(
        'Capture Error',
        'Failed to capture image. Please try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setIsCapturing(false);
    }
  };

  const toggleFlash = () => {
    const modes = [
      RNCamera.Constants.FlashMode.auto,
      RNCamera.Constants.FlashMode.on,
      RNCamera.Constants.FlashMode.off,
    ];
    const currentIndex = modes.indexOf(flashMode);
    const nextIndex = (currentIndex + 1) % modes.length;
    setFlashMode(modes[nextIndex]);
  };

  const toggleCamera = () => {
    setCameraType(
      cameraType === RNCamera.Constants.Type.back
        ? RNCamera.Constants.Type.front
        : RNCamera.Constants.Type.back
    );
  };

  const getFlashIcon = () => {
    switch (flashMode) {
      case RNCamera.Constants.FlashMode.on:
        return 'flash-on';
      case RNCamera.Constants.FlashMode.off:
        return 'flash-off';
      default:
        return 'flash-auto';
    }
  };

  return (
    <View style={styles.container}>
      <RNCamera
        ref={cameraRef}
        style={styles.camera}
        type={cameraType}
        flashMode={flashMode}
        androidCameraPermissionOptions={{
          title: 'Permission to use camera',
          message: 'We need your permission to use your camera to capture meal photos',
          buttonPositive: 'Ok',
          buttonNegative: 'Cancel',
        }}
        captureAudio={false}
      >
        {/* Header with controls */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.headerButton} onPress={onClose}>
            <Icon name="close" size={24} color={colors.white} />
          </TouchableOpacity>
          
          <Text style={styles.headerTitle}>Capture Your Meal</Text>
          
          <TouchableOpacity style={styles.headerButton} onPress={toggleFlash}>
            <Icon name={getFlashIcon()} size={24} color={colors.white} />
          </TouchableOpacity>
        </View>

        {/* Camera guide overlay */}
        <View style={styles.overlay}>
          <View style={styles.guideFrame} />
          <Text style={styles.guideText}>
            Position your meal within the frame
          </Text>
        </View>

        {/* Bottom controls */}
        <View style={styles.controls}>
          <View style={styles.controlsRow}>
            <TouchableOpacity style={styles.controlButton} onPress={toggleCamera}>
              <Icon name="flip-camera-android" size={28} color={colors.white} />
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.captureButton, isCapturing && styles.captureButtonDisabled]}
              onPress={captureImage}
              disabled={isCapturing}
            >
              <View style={styles.captureButtonInner}>
                {isCapturing && (
                  <View style={styles.captureButtonLoading} />
                )}
              </View>
            </TouchableOpacity>

            <View style={styles.controlButton} />
          </View>
        </View>
      </RNCamera>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.black,
  },
  camera: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: spacing.xl,
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.md,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
  },
  headerButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
  },
  headerTitle: {
    ...typography.h3,
    color: colors.white,
    textAlign: 'center',
  },
  overlay: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  guideFrame: {
    width: screenWidth * 0.8,
    height: screenWidth * 0.8,
    borderWidth: 2,
    borderColor: colors.white,
    borderRadius: 12,
    backgroundColor: 'transparent',
  },
  guideText: {
    ...typography.body1,
    color: colors.white,
    textAlign: 'center',
    marginTop: spacing.lg,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 8,
  },
  controls: {
    paddingBottom: spacing.xl,
    paddingHorizontal: spacing.md,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
  },
  controlsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  controlButton: {
    width: 50,
    height: 50,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 25,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
  },
  captureButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.white,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 4,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  captureButtonDisabled: {
    opacity: 0.6,
  },
  captureButtonInner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  captureButtonLoading: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.white,
  },
});