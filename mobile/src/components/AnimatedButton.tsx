import React, { useRef } from "react";
import { TouchableOpacity, Text, Animated, ViewStyle, TextStyle } from "react-native";

interface AnimatedButtonProps {
  title?: string;
  onPress: () => void;
  style?: ViewStyle | ViewStyle[];
  textStyle?: TextStyle | TextStyle[];
  disabled?: boolean;
  children?: React.ReactNode; // allow icons or other children
}

const AnimatedButton: React.FC<AnimatedButtonProps> = ({
  title,
  onPress,
  style,
  textStyle,
  disabled = false,
  children,
}) => {
  const scale = useRef(new Animated.Value(1)).current;

  const handlePressIn = () => {
    Animated.spring(scale, {
      toValue: 0.97,
      friction: 10,
      tension: 70,
      useNativeDriver: true,
    }).start();
  };

  const handlePressOut = () => {
    Animated.spring(scale, {
      toValue: 1,
      friction: 6,
      tension: 50,
      useNativeDriver: true,
    }).start();
  };

  return (
    <Animated.View style={{ transform: [{ scale }] }}>
      <TouchableOpacity
        onPress={onPress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        activeOpacity={0.8}
        disabled={disabled}
        style={[ // 👈 apply frame styles here so the whole area is clickable
          { flexDirection: "row", alignItems: "center", justifyContent: "center" },
          style,
        ]}
      >
        {children}
        {title ? <Text style={textStyle}>{title}</Text> : null}
      </TouchableOpacity>
    </Animated.View>
  );
};

export default AnimatedButton;
