import React, { useEffect, useState } from "react";
import { Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import { useFonts } from "expo-font";
import AnimatedSplashScreen from "./AnimatedSplashScreen";
import { Text, View } from "react-native";
import { SettingsProvider } from "../src/context/SettingsContext";

// Keep splash screen visible
SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [splashVisible, setSplashVisible] = useState(true);

  const [fontsLoaded] = useFonts({
    "Nunito-Light": require("../assets/fonts/Nunito-Light.ttf"),
    "Nunito-Regular": require("../assets/fonts/Nunito-Regular.ttf"),
    "Nunito-SemiBold": require("../assets/fonts/Nunito-SemiBold.ttf"),
    "Nunito-Bold": require("../assets/fonts/Nunito-Bold.ttf"),
    "Nunito-ExtraBold": require("../assets/fonts/Nunito-ExtraBold.ttf"),
    "Nunito-Medium": require("../assets/fonts/Nunito-Medium.ttf"),
    "Nunito-LightItalic": require("../assets/fonts/Nunito-LightItalic.ttf"),
    "Nunito-SemiBoldItalic": require("../assets/fonts/Nunito-SemiBoldItalic.ttf"),
    "Nunito-BoldItalic": require("../assets/fonts/Nunito-BoldItalic.ttf"),
    "Nunito-ExtraBoldItalic": require("../assets/fonts/Nunito-ExtraBoldItalic.ttf"),
    "Nunito-MediumItalic": require("../assets/fonts/Nunito-MediumItalic.ttf"),
    "Nunito-ExtraLight": require("../assets/fonts/Nunito-ExtraLight.ttf"),
  });

  useEffect(() => {
    if (fontsLoaded) {
      (async () => {
        await SplashScreen.hideAsync();
      })();
    }

    (Text as any).defaultProps = (Text as any).defaultProps || {};
    (Text as any).defaultProps.style = { fontFamily: "Nunito-Regular" };
  }, [fontsLoaded]);

  if (!fontsLoaded) return null;

  return (
    <SettingsProvider>
      <>
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="index" />
          <Stack.Screen name="welcome" />
          <Stack.Screen name="signup" />
          <Stack.Screen name="login" />
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="meal-detail" />
        </Stack>

        {splashVisible && (
          <AnimatedSplashScreen onFadeComplete={() => setSplashVisible(false)} />
        )}
      </>
    </SettingsProvider>
  );
}