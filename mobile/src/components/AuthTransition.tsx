import React, { useEffect, useRef } from 'react';
import { View, Animated, Dimensions, StyleSheet } from 'react-native';
import COLORS from '../styles/colors';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

interface AuthTransitionProps {
  onAnimationEnd: () => void;
}

export default function AuthTransition({ onAnimationEnd }: AuthTransitionProps) {
  const opacity = useRef(new Animated.Value(0)).current;
  const scale = useRef(new Animated.Value(0.8)).current;

  useEffect(() => {
    Animated.sequence([
      Animated.parallel([
        Animated.timing(opacity, {
          toValue: 1,
          duration: 400,
          useNativeDriver: true,
        }),
        Animated.spring(scale, {
          toValue: 1,
          useNativeDriver: true,
        }),
      ]),
      Animated.delay(200),
      Animated.parallel([
        Animated.timing(opacity, {
          toValue: 0,
          duration: 400,
          useNativeDriver: true,
        }),
        Animated.timing(scale, {
          toValue: 1.2,
          duration: 400,
          useNativeDriver: true,
        }),
      ]),
    ]).start(() => {
      onAnimationEnd();
    });
  }, []);

  return (
    <Animated.View
      style={[
        StyleSheet.absoluteFill,
        {
          backgroundColor: COLORS.screenBackground,
          justifyContent: 'center',
          alignItems: 'center',
          opacity,
          transform: [{ scale }],
          zIndex: 9999,
        },
      ]}
    >
      <View style={{ width: SCREEN_WIDTH * 0.4, height: SCREEN_WIDTH * 0.4, borderRadius: SCREEN_WIDTH * 0.2, backgroundColor: COLORS.buttonColor }} />
    </Animated.View>
  );
}
