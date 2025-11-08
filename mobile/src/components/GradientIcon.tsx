import React from 'react';
import { View, StyleSheet, Dimensions, PixelRatio } from 'react-native';
import Svg, { Defs, RadialGradient, Stop, Rect } from 'react-native-svg';
import MaskedView from '@react-native-masked-view/masked-view';
import { Ionicons } from '@expo/vector-icons';
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

export interface GradientIconProps {
  name?: keyof typeof Ionicons.glyphMap;
  size?: number;
  active?: boolean;
  outlined?: boolean;
  children?: React.ReactNode;
  style?: any;
}

// Reusable Radial Gradient Component for any content
export const RadialGradientMask: React.FC<{
  children: React.ReactNode;
  colors?: string[];
  width?: number | string;
  height?: number | string;
}> = ({ 
  children, 
  colors = ['#A4A75F', '#764C8D'],
  width = 120,
  height = 100
}) => {
  // Handle responsive scaling for numeric values
  const responsiveWidth = typeof width === 'number' ? moderateScale(width) : width;
  const responsiveHeight = typeof height === 'number' ? moderateScale(height) : height;

  return (
    <MaskedView 
      style={{ flexDirection: 'row' }}
      maskElement={
        <View style={{ backgroundColor: 'transparent', flexDirection: 'row' }}>
          {children}
        </View>
      }
    >
      <Svg width={responsiveWidth} height={responsiveHeight} style={{ position: 'absolute' }}>
        <Defs>
          <RadialGradient id="radialGrad" cx="50%" cy="50%" r="40%">
              <Stop offset="20%" stopColor={colors[0]} />
              <Stop offset="100%" stopColor={colors[1]} />
          </RadialGradient>
        </Defs>
        <Rect width="100%" height="100%" fill="url(#radialGrad)" />
      </Svg>
      <View style={{ opacity: 0 }}>
        {children}
      </View>
    </MaskedView>
  );
};

// Icon-specific component with radial gradient
const GradientIcon: React.FC<GradientIconProps> = ({
  name,
  size = 28,
  active = false,
  outlined = false,
  children,
  style,
}) => {
  const responsiveSize = moderateScale(size);
  
  // Default color for non-active icons
  const iconColor = active ? COLORS.white : COLORS.textColor;

  const styles = StyleSheet.create({
    iconWrapper: {
      justifyContent: 'center',
      alignItems: 'center',
    },
    gradientBackground: {
      justifyContent: 'center',
      alignItems: 'center',
      borderRadius: normalize(50),
      padding: normalize(10),
    },
  });

  if (!active && !children) {
    // Outlined / inactive icons (no gradient)
    return (
      <View style={[styles.iconWrapper, style]}>
        {name && <Ionicons name={name} size={responsiveSize} color={iconColor} />}
      </View>
    );
  }

  // If custom children provided, wrap with radial gradient
  if (children) {
    return (
      <RadialGradientMask width={responsiveSize} height={responsiveSize}>
        {children}
      </RadialGradientMask>
    );
  }

  // Active icons with radial gradient
  return (
    <View style={[styles.iconWrapper, style]}>
      <RadialGradientMask width={responsiveSize + normalize(20)} height={responsiveSize + normalize(20)}>
        <View style={styles.gradientBackground}>
          {name && (
            <Ionicons
              name={name}
              size={responsiveSize}
              color={COLORS.white}
            />
          )}
        </View>
      </RadialGradientMask>
    </View>
  );
};

export default GradientIcon;