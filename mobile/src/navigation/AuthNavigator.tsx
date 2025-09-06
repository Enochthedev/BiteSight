/**
 * Authentication flow navigation
 */

import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { LoginScreen } from '@/screens/auth/LoginScreen';
import { RegisterScreen } from '@/screens/auth/RegisterScreen';
import { ConsentScreen } from '@/screens/ConsentScreen';

type AuthParamList = {
  Login: undefined;
  Register: undefined;
  Consent: {
    isInitialSetup?: boolean;
    onConsentComplete?: () => void;
  };
};

const Stack = createStackNavigator<AuthParamList>();

export const AuthNavigator: React.FC = () => {
  return (
    <Stack.Navigator
      initialRouteName="Login"
      screenOptions={{
        headerShown: false,
        cardStyle: { backgroundColor: '#ffffff' },
      }}
    >
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Register" component={RegisterScreen} />
      <Stack.Screen name="Consent" component={ConsentScreen} />
    </Stack.Navigator>
  );
};