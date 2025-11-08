import React, { useRef } from 'react';
import { View, Text, StyleSheet, Animated, TouchableWithoutFeedback, Dimensions, PixelRatio } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { RadialGradientMask } from './GradientIcon';
import COLORS from '../styles/colors';
import { useRouter, usePathname } from 'expo-router';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// Responsive scaling
const scale = SCREEN_WIDTH / 375;
const verticalScale = SCREEN_HEIGHT / 812;

const normalize = (size: number) => Math.round(PixelRatio.roundToNearestPixel(size * scale));
const normalizeVertical = (size: number) => Math.round(PixelRatio.roundToNearestPixel(size * verticalScale));
const moderateScale = (size: number, factor = 0.5) => size + (normalize(size) - size) * factor;

// Shared type for tab IDs
export type TabId = 'home' | 'history' | 'settings';

interface NavItem {
  id: TabId;
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  iconOutline: keyof typeof Ionicons.glyphMap;
  route: string;
}

const navItems: NavItem[] = [
  { id: 'home', label: 'Home', icon: 'home', iconOutline: 'home-outline', route: '/home' },
  { id: 'history', label: 'History', icon: 'time', iconOutline: 'time-outline', route: '/history' },
  { id: 'settings', label: 'Settings', icon: 'settings', iconOutline: 'settings-outline', route: '/settings' },
];

// No props needed since active tab comes from pathname
const BottomNavBar: React.FC = () => {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const pathname = usePathname();

  // Determine active tab based on current route
  const currentTab = navItems.find(item => pathname.startsWith(item.route))?.id;

  const styles = StyleSheet.create({
    container: {
      position: 'absolute',
      bottom: 0,
      left: 0,
      right: 0,
      flexDirection: 'row',
      justifyContent: 'space-around',
      alignItems: 'center',
      backgroundColor: COLORS.white,
      paddingVertical: normalizeVertical(10),
      paddingHorizontal: normalize(20),
      paddingBottom: Math.max(insets.bottom, normalizeVertical(10)),
      borderTopWidth: 1,
      borderTopColor: '#E0E0E0',
      shadowColor: '#000',
      shadowOffset: { width: 0, height: -2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
      elevation: 8,
    },
    navItem: {
      alignItems: 'center',
      justifyContent: 'center',
    },
    navLabel: {
      fontSize: moderateScale(16),
    },
    
    navLabelActive: {
      color: COLORS.secondaryColor,
      fontFamily: 'Nunito-SemiBold',
    },

    navLabelInactive: {
      color: COLORS.textColor,
      fontWeight: '300',
      fontFamily: 'Nunito-Light',
    },
  });

  return (
    <View style={styles.container}>
      {navItems.map(item => {
        const isActive = currentTab === item.id;
        const scaleAnim = useRef(new Animated.Value(1)).current;

        const onPressIn = () => {
          Animated.spring(scaleAnim, {
            toValue: 0.95,
            useNativeDriver: true,
            speed: 20,
            bounciness: 10,
          }).start();
        };

        const onPressOut = () => {
          Animated.spring(scaleAnim, {
            toValue: 1,
            useNativeDriver: true,
            speed: 20,
            bounciness: 10,
          }).start();
        };

        const onPress = () => {
          router.push(item.route);
        };

        return (
          <TouchableWithoutFeedback
            key={item.id}
            onPress={onPress}
            onPressIn={onPressIn}
            onPressOut={onPressOut}
          >
            <Animated.View style={[styles.navItem, { transform: [{ scale: scaleAnim }] }]}>
              {isActive ? (
                <RadialGradientMask colors={['#A4A75F', '#764C8D']} width={normalize(32)} height={normalize(32)}>
                  <Ionicons name={item.icon} size={moderateScale(28)} color="black" />
                </RadialGradientMask>
              ) : (
                <Ionicons name={item.iconOutline} size={moderateScale(28)} color={COLORS.textColor} />
              )}
              <Text style={[styles.navLabel, isActive ? styles.navLabelActive : styles.navLabelInactive]}>
                {item.label}
              </Text>
            </Animated.View>
          </TouchableWithoutFeedback>
        );
      })}
    </View>
  );
};

export default BottomNavBar;
