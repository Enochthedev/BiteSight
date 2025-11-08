import React from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  Image, 
  Dimensions, 
  PixelRatio,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AnimatedButton from '../src/components/AnimatedButton';
import COLORS from '../src/styles/colors';
import DiamondGradient from "../src/components/DiamondGradient";
import { useRouter } from 'expo-router';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

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

export default function WelcomeScreen() {  
  const insets = useSafeAreaInsets();
  const router = useRouter();

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: COLORS.screenBackground,
      alignItems: 'center',
      paddingTop: insets.top + normalizeVertical(100),
    },
    logoImage: {
      width: normalize(180),
      height: normalize(180),
      marginLeft: normalizeVertical(50),
      marginBottom: normalizeVertical(-10),
      marginTop: normalizeVertical(20),
    },
    appNameContainer: {
      width: '100%',            
      alignItems: 'center',
      fontFamily: 'Nunito-ExtraBold',
    },
    tagline: {
      fontSize: moderateScale(16),
      fontFamily: 'Nunito-Light',
      color: COLORS.textColor,
      textAlign: 'center',
      marginBottom: normalizeVertical(35),
      marginTop: normalizeVertical(-10),
      paddingHorizontal: normalize(20),
    },
    getStartedButton: {
      flexDirection: 'row',
      backgroundColor: COLORS.buttonColor,
      paddingVertical: normalizeVertical(10),
      paddingHorizontal: SCREEN_WIDTH * 0.25,
      borderRadius: normalize(10),
      alignItems: 'center',
      justifyContent: 'center',
      shadowColor: COLORS.secondaryColor,
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.2,
      shadowRadius: 6,
      elevation: 3,
    },
    getStartedText: {
      fontSize: moderateScale(18),
      fontFamily: "Nunito-Medium",
      color: COLORS.white,
      marginRight: normalize(5),
    },
  });

  return (
    <View style={styles.container}>
      <Image
        source={require('../assets/logo.png')}
        style={styles.logoImage}
        resizeMode="contain"
      />
      <View style={styles.appNameContainer}>
        <DiamondGradient size={38}>PlateLensAI</DiamondGradient> 
      </View>
      <Text style={styles.tagline}>
        Upload meals → Get instant analysis & tips
      </Text>
      <AnimatedButton 
        onPress={() => router.push('/signup')} 
        style={styles.getStartedButton}
      >
        <Text style={styles.getStartedText}>Get Started</Text>
        <Ionicons
          name="arrow-forward"
          size={moderateScale(20)}
          color={COLORS.white}
        />
      </AnimatedButton>
    </View>
  );
}