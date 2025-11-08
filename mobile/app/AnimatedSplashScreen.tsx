import React, { useEffect, useRef } from "react";
import { Animated, Image, StyleSheet } from "react-native";
import { Dimensions, PixelRatio } from "react-native";

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get("window");

// Horizontal scale
export const normalize = (size: number) => {
  const scale = SCREEN_WIDTH / 375; // 375 is your base width
  const newSize = size * scale;
  return Math.round(PixelRatio.roundToNearestPixel(newSize));
};

// Vertical scale
export const normalizeVertical = (size: number) => {
  const scale = SCREEN_HEIGHT / 812; // 812 is your base height
  const newSize = size * scale;
  return Math.round(PixelRatio.roundToNearestPixel(newSize));
};

// Moderate scale (optional: smooth scaling)
export const moderateScale = (size: number, factor = 0.5) => {
  return size + (normalize(size) - size) * factor;
};


interface AnimatedSplashScreenProps {
  onFadeComplete: () => void;
}

const AnimatedSplashScreen: React.FC<AnimatedSplashScreenProps> = ({ onFadeComplete }) => {
  const opacity = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    const timeout = setTimeout(() => {
      Animated.timing(opacity, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }).start(() => onFadeComplete());
    }, 3000);
    return () => clearTimeout(timeout);
  }, []);

  return (
    <Animated.View style={[styles.container, { opacity }]}>
      <Image
        source={require("../assets/logo.png")} // adjust path if needed
        style={styles.logo}
        resizeMode="contain"
      />
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject, // cover the whole screen
    backgroundColor: "#5E7E98",
    justifyContent: "center",
    alignItems: "center",
    zIndex: 9999, // ensure it's above everything
  },
  logo: {
    width: 210,
    height: 210,
    marginLeft: normalize(40),
    marginBottom: normalize(80),

  },
});

export default AnimatedSplashScreen;
