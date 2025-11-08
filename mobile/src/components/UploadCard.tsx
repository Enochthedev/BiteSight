import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image, Dimensions, PixelRatio } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import GradientIcon from '@/components/GradientIcon';
import COLORS from '@/styles/colors';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// Responsive scaling
const scale = SCREEN_WIDTH / 375;
const verticalScale = SCREEN_HEIGHT / 812;

const normalize = (size: number) => {
  const newSize = size * scale;
  return Math.round(PixelRatio.roundToNearestPixel(newSize));
};

const normalizeVertical = (size: number) => {
  const newSize = size * verticalScale;
  return Math.round(PixelRatio.roundToNearestPixel(newSize));
};

const moderateScale = (size: number, factor = 0.5) => {
  return size + (normalize(size) - size) * factor;
};

interface UploadCardProps {
  imageUri?: string | null;
  onTakePhoto: () => Promise<void>;
  onChooseFile: () => Promise<void>;
  username: string;
  isReturning: boolean;
}

const UploadCard: React.FC<UploadCardProps> = ({
  imageUri,
  onTakePhoto,
  onChooseFile,
  username,
  isReturning,
}) => {
  const insets = useSafeAreaInsets();

  const title = isReturning ? `Welcome back, ${username}!` : `Welcome, ${username}!`;
  const subtitle = isReturning
    ? `Let's see what's on your plate today.`
    : `Let's analyze your first meal.`;
  const description = isReturning
    ? `Ready to analyze your meal? Let PlateLensAI show you what's on it and how to make it balanced.`
    : `Take or Upload a photo of your plate of food and let PlateLensAI reveal what's on it and how to make it balanced.`;

  const styles = StyleSheet.create({
    container: {
      backgroundColor: COLORS.screenBackground,
      flex: 1,
      padding: normalize(16),
      paddingTop: insets.top + normalizeVertical(16),
      alignItems: 'center',
    },
    headerTextContainer: {
      marginBottom: normalizeVertical(20),
      alignItems: 'center',
      paddingHorizontal: normalize(12),
    },
    title: {
      fontSize: moderateScale(22),
      fontWeight: '600',
      color: COLORS.secondaryColor,
    },
    subtitle: {
      fontSize: moderateScale(18),
      fontWeight: '500',
      color: COLORS.textColor,
      marginTop: normalizeVertical(4),
    },
    description: {
      fontSize: moderateScale(14),
      color: COLORS.textColor,
      textAlign: 'center',
      marginTop: normalizeVertical(8),
    },
    uploadBox: {
      borderStyle: 'dashed',
      borderWidth: 1,
      borderRadius: normalize(20),
      borderColor: COLORS.secondaryColor,
      paddingVertical: normalizeVertical(24),
      alignItems: 'center',
      width: '90%',
      backgroundColor: COLORS.white,
      elevation: 2,
      opacity: 0.9,
    },
    cameraContainer: {
      shadowColor: COLORS.secondaryColor,
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.2,
      shadowRadius: 6,
      marginBottom: normalizeVertical(12),
    },
    cameraCircle: {
      width: normalize(70),
      height: normalize(70),
      borderRadius: normalize(35),
      borderWidth: 1,
      borderColor: COLORS.secondaryColor,
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: COLORS.white,
    },
    uploadedImage: {
      width: normalize(150),
      height: normalize(150),
      borderRadius: normalize(15),
      marginTop: normalizeVertical(8),
    },
    text: {
      color: COLORS.textColor,
      fontSize: moderateScale(14),
      textAlign: 'center',
      width: '80%',
    },
    chooseButton: {
      marginTop: normalizeVertical(16),
      borderWidth: 1,
      borderColor: COLORS.buttonColor,
      borderRadius: normalize(12),
      paddingVertical: normalizeVertical(10),
      paddingHorizontal: normalize(20),
    },
    chooseButtonText: {
      color: COLORS.buttonColor,
      fontSize: moderateScale(14),
      fontWeight: '500',
    },
  });

  return (
    <View style={styles.container}>
      {/* Greeting */}
      <View style={styles.headerTextContainer}>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.subtitle}>{subtitle}</Text>
        <Text style={styles.description}>{description}</Text>
      </View>

      {/* Upload Card */}
      <TouchableOpacity
        style={styles.uploadBox}
        onPress={onTakePhoto}
        activeOpacity={0.8}
      >
        <View style={styles.cameraContainer}>
          <View style={styles.cameraCircle}>
            <GradientIcon
              name="camera-outline"
              size={32}
              active
              outlined
            />
          </View>
        </View>

        {imageUri ? (
          <Image source={{ uri: imageUri }} style={styles.uploadedImage} />
        ) : (
          <Text style={styles.text}>Tap to upload or capture your plate.</Text>
        )}
      </TouchableOpacity>

      {/* Choose File Button */}
      <TouchableOpacity style={styles.chooseButton} onPress={onChooseFile}>
        <Text style={styles.chooseButtonText}>Choose from gallery</Text>
      </TouchableOpacity>
    </View>
  );
};

export default UploadCard;