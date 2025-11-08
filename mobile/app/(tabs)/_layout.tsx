import React from "react";
import { View } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import BottomNavbar from "../../src/components/BottomNavbar";
import type { TabId } from "../../src/components/BottomNavbar";
import { useRouter, usePathname } from "expo-router";
import { Stack } from "expo-router";

export default function TabsLayout() {
  const router = useRouter();
  const pathname = usePathname();
  
  // Determine active tab based on current route
  const getActiveTab = (): TabId => {
    if (pathname.includes("home")) return "home";
    if (pathname.includes("history")) return "history";
    if (pathname.includes("settings")) return "settings";
    return "home";
  };

  const handleTabChange = (tab: TabId) => {
    switch (tab) {
      case "home":
        router.push("/(tabs)/home");
        break;
      case "history":
        router.push("/(tabs)/history");
        break;
      case "settings":
        router.push("/(tabs)/settings");
        break;
    }
  };

  const activeTab = getActiveTab();

  return (
    <SafeAreaProvider>
      <View style={{ flex: 1 }}>
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="home" />
          <Stack.Screen name="history" />
          <Stack.Screen name="settings" />
        </Stack>
        
        <BottomNavbar />

      </View>
    </SafeAreaProvider>
  );
}