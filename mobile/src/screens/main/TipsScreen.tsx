import React from "react";
import { View, Text, ScrollView, StyleSheet, Dimensions, TouchableOpacity, PixelRatio } from "react-native";
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from "@expo/vector-icons";
import { useRouter, useLocalSearchParams } from "expo-router";
import COLORS from "../../styles/colors";

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get("window");

// Responsive scaling functions
const scale = SCREEN_WIDTH / 375;
const verticalScale = SCREEN_HEIGHT / 812;

const normalize = (size: number) => Math.round(PixelRatio.roundToNearestPixel(size * scale));
const normalizeVertical = (size: number) => Math.round(PixelRatio.roundToNearestPixel(size * verticalScale));
const moderateScale = (size: number, factor = 0.5) => size + (normalize(size) - size) * factor;

export default function TipsScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { tipsText } = useLocalSearchParams<{ tipsText?: string }>();
  const defaultTips = "Tips to give a balanced type of your meal.";
  const tips = tipsText || defaultTips;

  const styles = StyleSheet.create({
    screen: {
      flex: 1,
      backgroundColor: COLORS.screenBackground,
    },
    goBackContainer: {
      flexDirection: "row",
      alignItems: "center",
      marginTop: insets.top + normalizeVertical(25),
      marginLeft: normalize(16),
    },

    goBackText: {
      fontSize: moderateScale(16),
      marginLeft: normalize(6),
      color: COLORS.textColor,
      fontFamily: "Nunito-Regular",
    },
    tipsContainer: {
      backgroundColor: COLORS.white,
      marginTop: normalizeVertical(20),
      marginBottom: normalizeVertical(30),
      marginHorizontal: normalize(16),
      paddingVertical: normalizeVertical(10),
      paddingHorizontal: normalize(10),
      borderRadius: normalize(10),
      maxHeight: SCREEN_HEIGHT * 0.6, // Limits container height
    },
    tipsText: {
      fontSize: moderateScale(14),
      color: COLORS.textColor,
      fontFamily: "Nunito-Regular",
      lineHeight: moderateScale(16) * 1.5,
    },
  });

  return (
    <ScrollView style={styles.screen}>
      {/* Go Back Section */}
      <TouchableOpacity style={styles.goBackContainer} onPress={() => router.back()}>
        <Ionicons name="arrow-back" size={moderateScale(24)} color={COLORS.textColor} />
        <Text style={styles.goBackText}>Back</Text>
      </TouchableOpacity>

      {/* Tips Section */}
      <View style={styles.tipsContainer}>
        <ScrollView
          nestedScrollEnabled={true} // Allows inner scroll within outer ScrollView
          showsVerticalScrollIndicator={true}
        >
          <Text style={styles.tipsText}>{tips}</Text>
        </ScrollView>
      </View>
    </ScrollView>
  );
}
