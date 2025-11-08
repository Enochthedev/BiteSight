import React, { useRef, useState, useEffect } from "react";
import {
  View,
  StyleSheet,
  Text,
  Animated,
  Easing,
  Alert,
  Image,
  Dimensions,
  Modal,
  ViewStyle, 
  TextStyle, 
  TouchableOpacity,
  PixelRatio,
  Platform,
} from "react-native";
import { Ionicons, MaterialIcons } from "@expo/vector-icons";
import { LinearGradient } from 'expo-linear-gradient';
import * as ImagePicker from "expo-image-picker";
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import COLORS from "../../styles/colors";
import { RadialGradientMask } from "../../components/GradientIcon";
import CameraGradientIcon from "../../components/CameraGradientIcon";
import AnimatedButton from "../../components/AnimatedButton";
import { useRouter, useLocalSearchParams } from "expo-router";
import AsyncStorage from "@react-native-async-storage/async-storage";


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

export default function HomeScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const route = useLocalSearchParams();

  const [imageUri, setImageUri] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isAnalyzed, setIsAnalyzed] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<string>("");
  const [showTipsModal, setShowTipsModal] = useState(false);
  const progress = useRef(new Animated.Value(0)).current;
  const imageScale = useRef(new Animated.Value(1)).current;

  const [isReturningUser] = useState(false);
const [firstName, setFirstName] = useState('John'); //default name

  React.useEffect(() => {
    if (route?.reset) {
      setImageUri(null);
      setIsAnalyzed(false);
      setAnalysisResult("");
    }
  }, [route?.reset]);

  useEffect(() => {
  const loadName = async () => {
    try {
      const stored = await AsyncStorage.getItem('userName');

      if (stored) {
        // Extract the first word before the first space
        const first = stored.trim().split(" ")[0];
        setFirstName(first);
      }
    } catch (error) {
      console.log("Error loading name", error);
    }
  };

  loadName();
}, []);


  const pickFromGallery = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") {
      Alert.alert("Permission required", "Media library permission is required.");
      return;
    }
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
      allowsEditing: false,
    });
    if (!res.canceled && res.assets.length > 0) {
      setImageUri(res.assets[0].uri);
      setIsAnalyzed(false);
    }
  };

  const takePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== "granted") {
      Alert.alert("Permission required", "Camera permission is required.");
      return;
    }
    const res = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });
    if (!res.canceled && res.assets.length > 0) {
      setImageUri(res.assets[0].uri);
      setIsAnalyzed(false);
    }
  };

  const startAnalysis = () => {
    if (!imageUri) {
      Alert.alert("No image", "Please take or select a photo first.");
      return;
    }
    setIsAnalyzing(true);
    progress.setValue(0);
    Animated.timing(progress, {
      toValue: 1,
      duration: 3000,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false,
    }).start(({ finished }) => {
      if (finished) {
        Animated.sequence([
          Animated.timing(imageScale, {
            toValue: 0.95,
            duration: 200,
            useNativeDriver: true,
          }),
          Animated.timing(imageScale, {
            toValue: 1,
            duration: 200,
            useNativeDriver: true,
          }),
        ]).start();
        setIsAnalyzing(false);
        setIsAnalyzed(true);
        setAnalysisResult("AI textual analysis...");
      }
    });
  };

  const proceedToCamera = () => {
    setShowTipsModal(false);
    takePhoto();
  };

  const progressWidth = progress.interpolate({
    inputRange: [0, 1],
    outputRange: ["0%", "100%"],
  });

  const getTopText = () => {
    if (isReturningUser) {
      return {
        greeting: "Welcome back,",
        subtitle: "Ready to analyze your next meal?",
        description: "Take or Upload a photo of your plate of food and let PlateLensAI reveal what's on it and how to make it balanced.",
      };
    } else {
      return {
        greeting: "Hello,",
        subtitle: "Let's analyze your first meal!",
        description: "Take or Upload a photo of your plate of food and let PlateLensAI reveal what's on it and how to make it balanced.",
      };
    }
  };

  const topText = getTopText();

  const renderDescription = () => {
    const parts = topText.description.split('PlateLensAI');
    return (
      <View style={styles.descriptionContainer}>
        <Text style={styles.descriptionText}>
          {parts[0]}
          <View style={styles.gradientTextWrapper}>
            <RadialGradientMask colors={['#A4A75F', '#764C8D']} width={moderateScale(115)} height={moderateScale(22)}>
              <Text style={styles.plateLensText}>PlateLensAI</Text>
            </RadialGradientMask>
          </View>
          {parts[1]}
        </Text>
      </View>
    );
  };


  //STYLES
  const styles = StyleSheet.create({
    screen: { 
      flex: 1, 
      backgroundColor: COLORS.screenBackground,
    },

    container: { 
      flex: 1, 
      paddingHorizontal: normalize(16),
      paddingTop: insets.top,
      paddingBottom: insets.bottom,
    },

    topSection: { 
      marginTop: normalizeVertical(20), 
      marginBottom: normalizeVertical(40),
    },

    greetingRow: { 
      flexDirection: "row", 
      flexWrap: "wrap", 
      alignItems: "center",
    },

    greetingText: { 
      fontSize: moderateScale(24), 
      fontWeight: "600", 
      color: COLORS.textColor, 
      fontFamily: "Nunito-SemiBold", 
      letterSpacing: -1,
    },

    subtitleText: { 
      fontSize: moderateScale(16), 
      fontWeight: "300", 
      color: COLORS.textColor,
      fontFamily: "Nunito-Light",
    },

    descriptionContainer: { 
      marginTop: normalizeVertical(15), 
    },

    descriptionText: { 
      fontSize: moderateScale(16), 
      color: COLORS.textColor, 
      lineHeight: moderateScale(16) * 1.3, 
      fontFamily: "Nunito-LightItalic",
    },

    gradientTextWrapper: { 
      height: moderateScale(19),
    },

    plateLensText: { 
      fontSize: moderateScale(16),  
      fontFamily: "Nunito-LightItalic", 
      lineHeight: moderateScale(16) * 1.3, 
      marginTop: normalizeVertical(3.5),    
    },

    uploadCard: {
      backgroundColor: COLORS.cardBg,
      borderRadius: normalize(10),
      borderWidth: 1,
      borderStyle: "dashed",
      borderColor: COLORS.secondaryColor,
      paddingVertical: normalizeVertical(30),
      paddingHorizontal: normalize(20),
      alignItems: "center",
      minHeight: normalizeVertical(300),
      justifyContent: "center",
    },

    uploadCardWithImage: {
      paddingVertical: 0,
      paddingHorizontal: 0,
      overflow: "hidden",
      borderWidth: 1,
      borderColor: COLORS.secondaryColor,
      borderStyle: "dashed",
      borderRadius: normalize(10),
    },

    uploadedImage: {
      width: SCREEN_WIDTH - normalize(32),
      height: (SCREEN_WIDTH - normalize(2)) * 0.85,
      borderRadius: normalize(10),
    },

    analysisSummaryContainer: {
      marginTop: normalizeVertical(30),
      marginBottom: normalizeVertical(30),
      backgroundColor: COLORS.white,
      paddingVertical: normalizeVertical(10),
      paddingHorizontal: normalize(10),
      borderRadius: normalize(10),
    },

    analysisSummaryText: {
      fontSize: moderateScale(14),
      color: COLORS.textColor,
      fontWeight: "300",
      fontFamily: "Nunito-Regular",
    },

    cameraIconContainer: { 
      marginBottom: normalizeVertical(10), 
    },

    cameraIconFrame: { 
      width: normalize(70), 
      height: normalize(70), 
      borderRadius: normalize(35), 
      backgroundColor: COLORS.white, 
      justifyContent: "center", 
      alignItems: "center", 
      shadowColor: "#764C8D", 
      shadowOffset: { width: 0, height: 2 }, 
      shadowOpacity: 0.2, 
      shadowRadius: 6, 
      elevation: 0.1,
    },

    takePhotoButton: { 
      marginTop: normalizeVertical(8), 
      backgroundColor: COLORS.buttonColor, 
      paddingVertical: normalizeVertical(10), 
      paddingHorizontal: normalize(20), 
      borderRadius: normalize(10), 
      shadowColor: COLORS.secondaryColor, 
      shadowOffset: { width: 0, height: 2 }, 
      shadowOpacity: 0.2, 
      shadowRadius: 6, 
      elevation: 3,
    },
    
    takePhotoText: { 
      fontSize: moderateScale(16), 
      color: COLORS.white, 
      fontWeight: "500", 
      fontFamily: "Nunito-Regular",
    },

    bottomSection: { 
      marginTop: normalizeVertical(30), 
      alignItems: "center", 
      gap: normalizeVertical(10),
    },

    orText: { 
      fontSize: moderateScale(16),
      fontWeight: "300", 
      color: COLORS.textColor, 
      fontFamily: "Nunito-Light",
    },

    chooseFileButton: { 
      backgroundColor: COLORS.white, 
      borderWidth: 1, 
      borderColor: COLORS.buttonColor, 
      paddingVertical: normalizeVertical(8), 
      paddingHorizontal: normalize(20), 
      borderRadius: normalize(10), 
      shadowColor: COLORS.secondaryColor, 
      shadowOffset: { width: 0, height: 2 }, 
      shadowOpacity: 0.2, 
      shadowRadius: 6, 
      elevation: 2,
    },

    chooseFileText: { 
      fontSize: moderateScale(16), 
      fontWeight: "500", 
      color: COLORS.buttonColor, 
      fontFamily: "Nunito-Regular",
    },

    fileInfoText: { 
      fontSize: moderateScale(12), 
      fontWeight: "400", 
      color: COLORS.textColor, 
      fontFamily: "Nunito-Regular",
    },

    actionSection: { 
      marginTop: normalizeVertical(30), 
      alignItems: "center", 
      gap: normalizeVertical(15),
    },

    analyzeButton: { 
      backgroundColor: COLORS.buttonColor, 
      paddingVertical: normalizeVertical(12), 
      paddingHorizontal: normalize(20), 
      borderRadius: normalize(10), 
      flexDirection: "row", 
      alignItems: "center", 
      justifyContent: "center", 
      width: SCREEN_WIDTH - normalize(32), 
      shadowColor: COLORS.secondaryColor, 
      shadowOffset: { width: 0, height: 2 }, 
      shadowOpacity: 0.2, 
      shadowRadius: 6, 
      elevation: 3,
    },

    analyzeButtonDisabled: { 
      backgroundColor: COLORS.backgroundMuted, 
      shadowOpacity: 0, 
      elevation: 0,
    },

    tipsButton: { 
      backgroundColor: COLORS.buttonColor, 
      paddingVertical: normalizeVertical(12), 
      paddingHorizontal: normalize(20), 
      borderRadius: normalize(10), 
      flexDirection: "row", 
      alignItems: "center", 
      justifyContent: "center", 
      width: SCREEN_WIDTH - normalize(32), 
      shadowColor: COLORS.secondaryColor, 
      shadowOffset: { width: 0, height: 2 }, 
      shadowOpacity: 0.2, 
      shadowRadius: 6, 
      elevation: 3,
    },

    analyzeAgainBtn: {
      marginTop: normalizeVertical(15),
      borderWidth: 1,
      borderColor: COLORS.buttonColor,
      borderRadius: normalize(8),
      paddingVertical: normalizeVertical(10),
      flexDirection: "row",
      justifyContent: "center",
      alignItems: "center",
      gap: normalize(2),
    },

    analyzeAgainText: {
      color: COLORS.buttonColor,
      fontSize: moderateScale(16),
      fontWeight: "500",
      fontFamily: "Nunito-Medium",
    },

    analyzeAgainIcon: {
      marginTop: normalizeVertical(-4),
    },

    buttonIcon: { 
      marginRight: normalize(3.5),
      marginTop: normalizeVertical(-4),
    },

    buttonText: { 
      fontSize: moderateScale(16), 
      color: COLORS.white, 
      fontWeight: "500", 
      fontFamily: "Nunito-Medium", 
    },

    gtipsText: {
        fontSize: moderateScale(16), 
        color: COLORS.white, 
        fontWeight: "500", 
        fontFamily: "Nunito-Medium",
        marginLeft: normalize(-3),
    },

    progressBarContainer: { 
      width: SCREEN_WIDTH - normalize(32), 
      alignItems: "center",
    },

    progressBackground: { 
      width: "100%", 
      height: normalizeVertical(48), 
      borderRadius: normalize(10), 
      overflow: "hidden", 
      justifyContent: "center", 
      shadowColor: COLORS.secondaryColor, 
      shadowOffset: { width: 0, height: 2 }, 
      shadowOpacity: 0.2, 
      shadowRadius: 6, 
      elevation: 3,
    },

    progressFill: { 
      height: "100%", 
      backgroundColor: "rgba(255,255,255,0.3)",
    },

    analyzingText: { 
      marginTop: normalizeVertical(10), 
      fontSize: moderateScale(14), 
      color: COLORS.textColor, 
      fontWeight: "300", 
      fontFamily: "Nunito-Light",
    },

    modalOverlay: { 
      flex: 1, 
      backgroundColor: "rgba(0, 0, 0, 0.5)", 
      justifyContent: "center", 
      alignItems: "center", 
      paddingHorizontal: normalize(20),
    },

    modalContent: { 
      backgroundColor: COLORS.white, 
      borderRadius: normalize(20), 
      padding: normalize(24), 
      width: "100%", 
      maxWidth: normalize(400),
    },

    tipsTitle: { 
      fontSize: moderateScale(18), 
      fontWeight: "600", 
      color: COLORS.textColor, 
      marginBottom: normalizeVertical(15), 
      fontFamily: "Nunito-SemiBold",
    },

    tipItem: { 
      flexDirection: "row", 
      alignItems: "center", 
      marginBottom: normalizeVertical(3),
    },

    tipText: { 
      fontSize: moderateScale(14), 
      color: COLORS.textColor, 
      marginLeft: normalize(8), 
      fontWeight: "400", 
      fontFamily: "Nunito-Regular",
    },

    modalButton: { 
      backgroundColor: COLORS.buttonColor, 
      paddingVertical: normalizeVertical(10), 
      paddingHorizontal: normalize(20), 
      borderRadius: normalize(12), 
      alignItems: "center", 
      marginTop: normalizeVertical(10), 
      shadowColor: COLORS.secondaryColor, 
      shadowOffset: { width: 0, height: 2 }, 
      shadowOpacity: 0.2, 
      shadowRadius: 6, 
      elevation: 3,
    },
  });


  // RESULTS
  return (
    <View style={styles.screen}>
      <View style={styles.container}>
        {!isAnalyzed && (
          <View style={styles.topSection}>
            <View style={styles.greetingRow}>
              <Text style={styles.greetingText}>
                {topText.greeting}{' '}
                <Text style={[styles.greetingText, { color: COLORS.secondaryColor }]}>
                  {firstName}👋🏿
                </Text>
              </Text>
            </View>
            <Text style={styles.subtitleText}>{topText.subtitle}</Text>
            {renderDescription()}
          </View>
        )}

        {!isAnalyzed && (
          <View style={[styles.uploadCard, imageUri ? styles.uploadCardWithImage : null]}>
            {!imageUri ? (
              <>
                <View style={styles.cameraIconContainer}>
                  <View style={styles.cameraIconFrame}>
                    <CameraGradientIcon />
                  </View>
                </View>

                <AnimatedButton
                  title="Take Photo"
                  onPress={() => setShowTipsModal(true)}
                  style={styles.takePhotoButton}
                  textStyle={styles.takePhotoText}
                />

                <View style={styles.bottomSection}>
                  <Text style={styles.orText}>or upload from gallery</Text>

                  <AnimatedButton
                    title="Choose File"
                    onPress={pickFromGallery}
                    style={styles.chooseFileButton}
                    textStyle={styles.chooseFileText}
                  />

                  <Text style={styles.fileInfoText}>
                    JPG/JPEG, PNG, WEBP, HEIC/HEIF (Max 5MB)
                  </Text>
                </View>
              </>
            ) : (
              <Animated.Image
                source={{ uri: imageUri }}
                style={[styles.uploadedImage, { transform: [{ scale: imageScale }] }]}
                resizeMode="cover"
              />
            )}
          </View>
        )}

        {isAnalyzed && (
          <>
            <Animated.Image
              source={{ uri: imageUri! }}
              style={[styles.uploadedImage, { marginTop: normalizeVertical(10), transform: [{ scale: imageScale }] }]}
              resizeMode="cover"
            />
            <View style={styles.analysisSummaryContainer}>
              <Text style={styles.analysisSummaryText}>{analysisResult}</Text>
            </View>
          </>
        )}

        {!isAnalyzed && (
          <View style={styles.actionSection}>
            {!isAnalyzing && (
              <AnimatedButton
                title="Start Analysis"
                onPress={startAnalysis}
                style={[styles.analyzeButton, !imageUri && styles.analyzeButtonDisabled].filter(Boolean) as ViewStyle[]}
                textStyle={styles.buttonText}
                disabled={!imageUri}
              >
                <Ionicons
                  name="sparkles-outline"
                  size={moderateScale(20)}
                  color={COLORS.white}
                  style={styles.buttonIcon}
                />
              </AnimatedButton>
            )}
            {isAnalyzing && (
              <View style={styles.progressBarContainer}>
                <LinearGradient
                  colors={[COLORS.gradientStart, COLORS.gradientEnd]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={styles.progressBackground}
                >
                  <Animated.View style={[styles.progressFill, { width: progressWidth }]} />
                </LinearGradient>
                <Text style={styles.analyzingText}>Analyzing...</Text>
              </View>
            )}
          </View>
        )}

        {isAnalyzed && (
          <>
            <AnimatedButton
              title="Generate Tips"
              onPress={() => router.push("/tips-screen")}
              style={styles.tipsButton}
              textStyle={styles.gtipsText}
            >
              <Ionicons
                name="bulb-outline"
                size={moderateScale(20)}
                color={COLORS.white}
                style={styles.buttonIcon}
              />
            </AnimatedButton>

            <AnimatedButton
              title="Analyze Again"
              onPress={() => {
                setImageUri(null);
                setIsAnalyzed(false);
                setAnalysisResult("");
              }}
              style={styles.analyzeAgainBtn}
              textStyle={styles.analyzeAgainText}
            >
              <Ionicons name="sparkles-outline" size={moderateScale(20)} color={COLORS.buttonColor} style={styles.analyzeAgainIcon} />
            </AnimatedButton>
          </>
        )}
      </View>

      <Modal
        visible={showTipsModal}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setShowTipsModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.tipsTitle}>For best results:</Text>
            <View style={styles.tipItem}>
              <MaterialIcons name="wb-sunny" size={moderateScale(16)} color={COLORS.textColor} />
              <Text style={styles.tipText}>Use good lighting</Text>
            </View>
            <View style={styles.tipItem}>
              <MaterialIcons name="center-focus-strong" size={moderateScale(16)} color={COLORS.textColor} />
              <Text style={styles.tipText}>Keep food in center of frame</Text>
            </View>
            <View style={styles.tipItem}>
              <MaterialIcons name="straighten" size={moderateScale(16)} color={COLORS.textColor} />
              <Text style={styles.tipText}>Hold camera steady</Text>
            </View>
            <View style={styles.tipItem}>
              <MaterialIcons name="visibility" size={moderateScale(16)} color={COLORS.textColor} />
              <Text style={styles.tipText}>Ensure all food is visible</Text>
            </View>
            <AnimatedButton
              title="OK"
              onPress={proceedToCamera}
              style={styles.modalButton}
              textStyle={styles.takePhotoText}
            />
          </View>
        </View>
      </Modal>
    </View>
  );
}