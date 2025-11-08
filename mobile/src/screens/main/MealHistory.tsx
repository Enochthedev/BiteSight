// MealHistory.tsx
import React, { useState } from "react";
import {
  View,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  Image,
  ScrollView,
  Dimensions,
  PixelRatio,
  ActivityIndicator,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import MaskedView from "@react-native-masked-view/masked-view";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import COLORS from "../../styles/colors";
import { useRouter } from "expo-router";
import { useSettings } from "../../context/SettingsContext";


// Import local images
const lunchImage = require("../../../assets/6.jpeg");
const dinnerImage = require("../../../assets/12.jpeg"); 
const breakfastImage = require("../../../assets/Akara and bread.jpeg"); 


const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get("window");

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

type FilterType = "This Week" | "This Month" | "All";

interface MealItem {
  id: string;
  title: string;
  info: string;
  date: string;
  time: string;
  imageUri: any;
  analysisText: string;
  tips: string;
  analyzedAt: Date;
}

// Mock data - this should come from your actual analysis data
const mockData: MealItem[] = [
  {
    id: "1",
    title: "Heading",
    info: "Balanced meal with...",
    date: "10 Oct 2025",
    time: "1:24 PM",
    imageUri: lunchImage,
    analysisText: "This meal contains a good balance of protein from the chicken, carbohydrates from the rice, and vegetables providing essential vitamins and minerals.",
    tips: "Consider adding more leafy greens to increase fiber content. The portion size looks adequate for a balanced lunch.",
    analyzedAt: new Date("2025-10-10T13:24:00"),
  },
  {
    id: "2",
    title: "Heading",
    info: "High protein content...",
    date: "10 Oct 2025",
    time: "1:24 PM",
    imageUri: lunchImage,
    analysisText: "Rich in protein and nutrients. Good balance of macronutrients.",
    tips: "Add more vegetables for better nutritional balance.",
    analyzedAt: new Date("2025-10-10T13:24:00"),
  },
  {
    id: "3",
    title: "Heading",
    info: "Comfort food with...",
    date: "10 Oct 2025",
    time: "10:24 PM",
    imageUri: dinnerImage,
    analysisText: "Hearty dinner with good carbohydrate content from rice and protein from the sauce.",
    tips: "Consider reducing portion size for evening meals. Add a side salad for better balance.",
    analyzedAt: new Date("2025-10-10T22:24:00"),
  },
  {
    id: "4",
    title: "Heading",
    info: "Savory rice bowl...",
    date: "10 Oct 2025",
    time: "10:24 PM",
    imageUri: breakfastImage,
    analysisText: "Rice-based meal with protein-rich sauce topping.",
    tips: "Add vegetables to make it more nutritionally complete.",
    analyzedAt: new Date("2025-10-10T22:24:00"),
  },
  {
    id: "5",
    title: "Heading",
    info: "Nutritious lunch plate...",
    date: "10 Sep 2025",
    time: "1:24 PM",
    imageUri: lunchImage,
    analysisText: "Well-balanced meal with protein, carbs, and vegetables.",
    tips: "Perfect balance! Keep up the good eating habits.",
    analyzedAt: new Date("2025-09-10T13:24:00"),
  },
  {
    id: "6",
    title: "Heading",
    info: "Traditional rice dish...",
    date: "10 Sep 2025",
    time: "1:24 PM",
    imageUri: breakfastImage,
    analysisText: "Classic comfort food with good energy content.",
    tips: "Consider adding protein sources like fish or chicken.",
    analyzedAt: new Date("2025-09-10T13:24:00"),
  },
];

// Helper function to determine meal type based on time (only used if autoTagMealTime is true)
const getMealType = (date: Date, autoTagMealTime: boolean): string => {
  if (!autoTagMealTime) return "Heading";
  
  const hour = date.getHours();
  if (hour >= 0 && hour < 12) return "Breakfast";
  if (hour >= 12 && hour < 17) return "Lunch";
  return "Dinner";
};

// Helper function to get first two words + "..."
const getShortInfo = (text: string): string => {
  const words = text.split(" ");
  if (words.length <= 2) return text;
  return `${words[0]} ${words[1]}...`;
};

// Gradient Icon Component
const GradientIcon = ({ name, size }: { name: any; size: number }) => {
  return (
    <MaskedView
      maskElement={<Ionicons name={name} size={size} color="white" />}
    >
      <LinearGradient
        colors={[COLORS.gradientStart, COLORS.gradientEnd]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 0 }}
      >
        <Ionicons name={name} size={size} color="transparent" />
      </LinearGradient>
    </MaskedView>
  );
};

export default function MealHistory() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [activeFilter, setActiveFilter] = useState<FilterType>("This Week");
  const [searchQuery, setSearchQuery] = useState("");

  // FROM Settings
  const { saveToHistory, autoTagMealTime, isLoading } = useSettings();


  // Filter meals based on search query and saveToHistory setting
  const filteredData = saveToHistory 
    ? mockData.filter((meal) =>
        meal.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        meal.info.toLowerCase().includes(searchQuery.toLowerCase()) ||
        meal.analysisText.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : mockData.slice(0, 1); // Only show last analyzed meal if saveToHistory is false

  const styles = StyleSheet.create({
    screen: {
      flex: 1,
      backgroundColor: COLORS.screenBackground,
    },

    container: {
      flex: 1,
      paddingTop: normalizeVertical(35),
    },

    header: {
      flexDirection: "row",
      alignItems: "center",
      paddingHorizontal: normalize(16),
      paddingVertical: normalizeVertical(16),
      gap: normalize(12),
    },

    backButton: {
      width: normalize(32),
      height: normalize(32),
      justifyContent: "center",
      alignItems: "center",
    },

    headerTitle: {
      fontSize: moderateScale(20),
      color: COLORS.textColor,
      fontFamily: "Nunito-Bold",
      flex: 1,
      textAlign: "center",
      marginRight: normalize(32),
    },

    searchContainer: {
      paddingHorizontal: normalize(16),
      marginBottom: normalizeVertical(5),
      marginTop: normalizeVertical(10),
    },

    searchInputWrapper: {
      flexDirection: "row",
      alignItems: "center",
      backgroundColor: COLORS.white,
      borderRadius: normalize(12),
      paddingHorizontal: normalize(15),
      borderWidth: 1,
      borderColor: "#B7C6D1",
    },

    searchIcon: {
      marginRight: normalize(5),
    },

    searchInput: {
      flex: 1,
      fontSize: moderateScale(16),
      fontFamily: "Nunito-Regular",
      color: COLORS.textColor,
    },

    filterContainerWrapper: {
      paddingHorizontal: normalize(16),
      marginBottom: normalizeVertical(20),
      marginTop: normalizeVertical(16),
    },

    filterContainer: {
      flexDirection: "row",
      backgroundColor: COLORS.white,
      borderRadius: normalize(12),
      padding: normalize(5),
      width: SCREEN_WIDTH - normalize(32),
    },

    filterButton: {
      flex: 1,
      paddingVertical: normalizeVertical(5),
      paddingHorizontal: normalize(10),
      borderRadius: normalize(8),
      alignItems: "center",
      justifyContent: "center",
    },

    filterButtonActive: {
      backgroundColor: COLORS.screenBackground,
    },

    filterText: {
      fontSize: moderateScale(14),
      fontFamily: "Nunito-Regular",
      color: "#B7C6D1",
    },

    filterTextActive: {
      color: COLORS.textColor,
      fontFamily: "Nunito-SemiBold",
    },

    scrollContent: {
      paddingHorizontal: normalize(16),
      paddingBottom: normalizeVertical(100),
    },

    dateSection: {
      marginTop: normalizeVertical(10),
      marginBottom: normalizeVertical(20),
    },

    dateSectionTitle: {
      fontSize: moderateScale(14),
      fontWeight: "600",
      color: COLORS.textColor,
      fontFamily: "Nunito-SemiBold",
      marginBottom: normalizeVertical(12),
    },

    mealCard: {
      flexDirection: "row",
      backgroundColor: COLORS.white,
      borderRadius: normalize(12),
      padding: normalize(10),
      marginBottom: normalizeVertical(12),
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.05,
      shadowRadius: 4,
      elevation: 2,
      alignItems: "center",
    },

    mealImage: {
      width: normalize(80),
      height: normalize(80),
      borderRadius: normalize(8),
      marginRight: normalize(12),
    },

    mealInfo: {
      flex: 1,
      justifyContent: "center",
    },

    mealTitle: {
      fontSize: moderateScale(16),
      fontWeight: "600",
      color: COLORS.textColor,
      fontFamily: "Nunito-SemiBold",
      marginBottom: normalizeVertical(4),
    },

    mealSubtitle: {
      fontSize: moderateScale(14),
      color: "#999999",
      fontFamily: "Nunito-Regular",
      marginBottom: normalizeVertical(4),
    },

    mealDateTime: {
      fontSize: moderateScale(12),
      color: "#878B8E",
      fontFamily: "Nunito-Regular",
    },

    chevronWrapper: {
      marginLeft: normalize(8),
      width: normalize(24),
      height: normalize(24),
      justifyContent: "center",
      alignItems: "center",
    },

    emptyStateContainer: {
      flex: 1,
      justifyContent: "center",
      alignItems: "center",
      paddingHorizontal: normalize(40),
      marginTop: normalizeVertical(100),
    },

    emptyStateTitle: {
      fontSize: moderateScale(18),
      fontFamily: "Nunito-SemiBold",
      color: COLORS.textColor,
      marginBottom: normalizeVertical(12),
      textAlign: "center",
    },

    emptyStateText: {
      fontSize: moderateScale(14),
      fontFamily: "Nunito-Regular",
      color: "#999999",
      textAlign: "center",
      lineHeight: moderateScale(14) * 1.5,
      marginBottom: normalizeVertical(16),
    },

    emptyStateHighlight: {
      fontSize: moderateScale(14),
      fontFamily: "Nunito-SemiBold",
      color: COLORS.secondaryColor,
    },
  });


  // LOADING CHECK HERE
  if (isLoading) {
    return (
      <View style={[styles.screen, { justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator size="large" color={COLORS.buttonColor} />
      </View>
    );
  }

  const renderDateSection = (title: string, meals: MealItem[]) => {
  const displayMeals = searchQuery ? meals : meals;
  
  if (displayMeals.length === 0) return null;

  return (
    <View style={styles.dateSection} key={title}>
      <Text style={styles.dateSectionTitle}>{title}</Text>
      {displayMeals.map((meal) => {
        const mealType = getMealType(meal.analyzedAt, autoTagMealTime);
        const shortInfo = getShortInfo(meal.analysisText);
        const formattedDate = meal.analyzedAt.toLocaleDateString("en-GB", {
          day: "numeric",
          month: "short",
          year: "numeric",
        });
        const formattedTime = meal.analyzedAt.toLocaleTimeString("en-US", {
          hour: "numeric",
          minute: "2-digit",
          hour12: true,
        });

        // Resolve image URI for navigation
        const resolvedImageUri = typeof meal.imageUri === 'string' 
          ? meal.imageUri 
          : Image.resolveAssetSource(meal.imageUri).uri;

        return (
          <TouchableOpacity
            key={meal.id}
            style={styles.mealCard}
            onPress={() => {
              router.push({
                pathname: "/meal-detail",
                params: {
                  id: meal.id,
                  imageUri: typeof meal.imageUri === 'string' ? meal.imageUri : Image.resolveAssetSource(meal.imageUri).uri,
                  analysisText: meal.analysisText,
                  tips: meal.tips,
                  mealType: mealType,
                  date: formattedDate,
                  time: formattedTime,
                },
              });
            }}
          >
            <Image
              source={typeof meal.imageUri === 'string' ? { uri: meal.imageUri } : meal.imageUri}
              style={styles.mealImage}
              resizeMode="cover"
            />
            <View style={styles.mealInfo}>
              <Text style={styles.mealTitle}>{mealType}</Text>
              <Text style={styles.mealSubtitle}>{shortInfo}</Text>
              <Text style={styles.mealDateTime}>
                {formattedDate} | {formattedTime}
              </Text>
            </View>
            <View style={styles.chevronWrapper}>
              <GradientIcon name="chevron-forward" size={moderateScale(24)} />
            </View>
          </TouchableOpacity>
        );
      })}
    </View>
  );
};

  return (
    <View style={styles.screen}>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <GradientIcon name="chevron-back" size={moderateScale(24)} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>History</Text>
        </View>

        {/* Search Bar */}
        <View style={styles.searchContainer}>
          <View style={styles.searchInputWrapper}>
            <Ionicons
              name="search"
              size={moderateScale(20)}
              color="#CCCCCC"
              style={styles.searchIcon}
            />
            <TextInput
              style={styles.searchInput}
              placeholder="Search"
              placeholderTextColor="#CCCCCC"
              value={searchQuery}
              onChangeText={setSearchQuery}
            />
          </View>
        </View>

        {/* Filter Tabs */}
        <View style={styles.filterContainerWrapper}>
          <View style={styles.filterContainer}>
            {(["This Week", "This Month", "All"] as FilterType[]).map((filter) => (
              <TouchableOpacity
                key={filter}
                style={[
                  styles.filterButton,
                  activeFilter === filter && styles.filterButtonActive,
                ]}
                onPress={() => setActiveFilter(filter)}
              >
                <Text
                  style={[
                    styles.filterText,
                    activeFilter === filter && styles.filterTextActive,
                  ]}
                >
                  {filter}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Scrollable Content or Empty State */}
        {!saveToHistory && filteredData.length === 0 ? (
          <View style={styles.emptyStateContainer}>
            <Ionicons
              name="albums-outline"
              size={moderateScale(60)}
              color="#CCCCCC"
              style={{ marginBottom: normalizeVertical(20) }}
            />
            <Text style={styles.emptyStateTitle}>No Analyzed Meals Saved</Text>
            <Text style={styles.emptyStateText}>
              Your analyzed meals are not being saved to history. {"\n\n"}
              You can turn on{" "}
              <Text style={styles.emptyStateHighlight}>"Save analyzed meals to history"</Text>
              {" "}in Settings to keep track of all your meals.
            </Text>
          </View>
        ) : (
          <ScrollView
            style={{ flex: 1 }}
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
          >
            {activeFilter === "This Week" && (
              <>
                {renderDateSection("12th - 18th October, 2025", filteredData.slice(0, 4))}
              </>
            )}

            {activeFilter === "This Month" && (
              <>
                {renderDateSection("October, 2024", filteredData.slice(0, 4))}
              </>
            )}

            {activeFilter === "All" && (
              <>
                {renderDateSection("October, 2024", filteredData.slice(0, 2))}
                {renderDateSection("September, 2024", filteredData.slice(4, 6))}
              </>
            )}

            {filteredData.length === 0 && searchQuery && (
              <View style={styles.emptyStateContainer}>
                <Ionicons
                  name="search-outline"
                  size={moderateScale(60)}
                  color="#CCCCCC"
                  style={{ marginBottom: normalizeVertical(20) }}
                />
                <Text style={styles.emptyStateTitle}>No Results Found</Text>
                <Text style={styles.emptyStateText}>
                  Try adjusting your search terms
                </Text>
              </View>
            )}
          </ScrollView>
        )}
      </View>
    </View>
  );
}