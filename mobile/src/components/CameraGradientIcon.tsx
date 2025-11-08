import { View, StyleSheet, Dimensions, PixelRatio } from "react-native";
import MaskedView from "@react-native-masked-view/masked-view";
import { LinearGradient } from "expo-linear-gradient";
import { Camera } from "lucide-react-native";

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

export default function CameraGradientIcon() {
  const iconSize = moderateScale(28);
  const strokeWidth = 2.8;
  const gradientSize = moderateScale(30);

  const styles = StyleSheet.create({
    cameraIconFrame: {
      width: normalize(70),
      height: normalize(70),
      borderRadius: normalize(35),
      backgroundColor: "#FFFFFF",
      justifyContent: "center",
      alignItems: "center",
      shadowColor: "#764C8D",
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.2,
      shadowRadius: 6,
      elevation: 5,
    },
  });

  return (
    <View style={styles.cameraIconFrame}>
      <MaskedView
        maskElement={
          <Camera
            strokeWidth={strokeWidth}
            size={iconSize}
            color="black"
          />
        }
      >
        <LinearGradient
          colors={["#A4A75F", "#764C8D"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={{ width: gradientSize, height: gradientSize - 1 }}
        />
      </MaskedView>
    </View>
  );
}