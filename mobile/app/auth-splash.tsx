import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { normalize } from './AnimatedSplashScreen';

export default function AuthSplash() {
  const router = useRouter();
  const opacity = useRef(new Animated.Value(1)).current;
  const hasNavigated = useRef(false);

  useEffect(() => {
    // Pre-navigate to home BEFORE starting fade animation
    // This loads the home screen in the background
    const preNavigateTimeout = setTimeout(() => {
      if (!hasNavigated.current) {
        hasNavigated.current = true;
        router.replace("/(tabs)/home");
      }
    }, 2500); // Navigate 500ms before fade starts

    // Start fade animation
    const fadeTimeout = setTimeout(() => {
      Animated.timing(opacity, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }).start();
    }, 3000);
    
    return () => {
      clearTimeout(preNavigateTimeout);
      clearTimeout(fadeTimeout);
    };
  }, []);

  return (
    <Animated.View style={[styles.container, { opacity }]}>
      <Image
        source={require("../assets/logo.png")}
        style={styles.logo}
        resizeMode="contain"
      />
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "#5E7E98",
    justifyContent: "center",
    alignItems: "center",
    zIndex: 9999,
  },
  logo: {
    width: 200,
    height: 200,
    marginLeft: normalize(40),
    marginBottom: normalize(60),
  },
});