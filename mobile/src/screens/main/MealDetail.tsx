import React from "react";
import {
  View,
  StyleSheet,
  Text,
  Image,
  ScrollView,
  TouchableOpacity,
  Dimensions,
  PixelRatio,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter, useLocalSearchParams } from "expo-router";
import COLORS from "../../styles/colors";

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get("window");

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

export default function MealDetail() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const params = useLocalSearchParams();

  const { imageUri, analysisText, tips, mealType, date, time } = params;

  const styles = StyleSheet.create({
    screen: {
      flex: 1,
      backgroundColor: COLORS.screenBackground,
    },

    header: {
      flexDirection: "row",
      alignItems: "center",
      paddingHorizontal: normalize(16),
      paddingTop: insets.top + normalizeVertical(35),
      paddingBottom: normalizeVertical(16),
    },

    goBackContainer: {
      flexDirection: "row",
      alignItems: "center",
      marginTop: insets.top + normalizeVertical(25),
      marginLeft: normalize(16),
      marginBottom: normalizeVertical(20),
    },
    
    goBackText: {
      fontSize: moderateScale(16),
      marginLeft: normalize(6),
      color: COLORS.textColor,
      fontFamily: "Nunito-Regular",
    },

    scrollContent: {
      paddingHorizontal: normalize(10),
      paddingBottom: normalizeVertical(30),
    },

    contentContainer: {
      backgroundColor: COLORS.white,
      borderRadius: normalize(12),
      padding: normalize(10),
      marginBottom: normalizeVertical(20),
    },

    mealImage: {
      width: "100%",
      height: normalizeVertical(250),
      borderRadius: normalize(12),
      marginBottom: normalizeVertical(16),
    },

    sectionTitle: {
      fontSize: moderateScale(16),
      fontWeight: "600",
      color: COLORS.textColor,
      fontFamily: "Nunito-SemiBold",
      marginBottom: normalizeVertical(8),
    },

    sectionText: {
      fontSize: moderateScale(14),
      color: "#666666",
      fontFamily: "Nunito-Regular",
      lineHeight: moderateScale(14) * 1.5,
      marginBottom: normalizeVertical(16),
    },

    divider: {
      height: 1,
      backgroundColor: "#E0E0E0",
      marginVertical: normalizeVertical(12),
    },
  });

  return (
    <View style={styles.screen}>
      {/* Go Back Section */}
      <TouchableOpacity style={styles.goBackContainer} onPress={() => router.back()}>
        <Ionicons name="arrow-back" size={moderateScale(24)} color={COLORS.textColor} />
        <Text style={styles.goBackText}>Back</Text>
      </TouchableOpacity>

      {/* Scrollable Content */}
      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.contentContainer}>
          {/* Meal Image */}
          <Image
            source={{ uri: imageUri as string }}
            style={styles.mealImage}
            resizeMode="cover"
          />

          {/* Meal Type and Date/Time */}
          <Text style={styles.sectionTitle}>{mealType}</Text>
          <Text style={[styles.sectionText, { color: "#878B8E", fontSize: moderateScale(12) }]}>
            {date} | {time}
          </Text>

          <View style={styles.divider} />

          {/* Analysis Summary */}
          <Text style={styles.sectionTitle}>Analysis Summary</Text>
          <Text style={styles.sectionText}>{analysisText}</Text>

          <View style={styles.divider} />

          {/* Tips */}
          <Text style={styles.sectionTitle}>Tips to give a balanced type of meal</Text>
          <Text style={styles.sectionText}>{tips}</Text>
        </View>
      </ScrollView>
    </View>
  );
}