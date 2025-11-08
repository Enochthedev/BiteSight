import { useEffect, useState } from "react";
import { useRouter } from "expo-router";
import { View, ActivityIndicator } from "react-native";
import COLORS from "../src/styles/colors";
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function Index() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      // Check if user has been authenticated before
      const hasAccount = await AsyncStorage.getItem('hasAccount');
      
      if (hasAccount === 'true') {
        // Existing user - go to login
        router.replace("/login");
      } else {
        // New user - go to welcome
        router.replace("/welcome");
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
      // Default to welcome screen on error
      router.replace("/welcome");
    } finally {
      setIsChecking(false);
    }
  };

  if (isChecking) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: COLORS.screenBackground }}>
        <ActivityIndicator size="large" color={COLORS.buttonColor} />
      </View>
    );
  }

  return null;
}