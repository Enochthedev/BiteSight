/**
 * Main app navigation structure
 */

import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { useAppContext } from '@/context/AppContext';
import { AuthNavigator } from './AuthNavigator';
import { MainNavigator } from './MainNavigator';
import { OnboardingScreen } from '@/screens/OnboardingScreen';
import { LoadingScreen } from '@/screens/LoadingScreen';
import { NavigationParamList } from '@/types';

const Stack = createStackNavigator<NavigationParamList>();

export const AppNavigator: React.FC = () => {
  const { state } = useAppContext();

  if (state.isLoading) {
    return <LoadingScreen />;
  }

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {!state.isAuthenticated ? (
        <>
          <Stack.Screen name="Onboarding" component={OnboardingScreen} />
          <Stack.Screen name="Auth" component={AuthNavigator} />
        </>
      ) : (
        <Stack.Screen name="Main" component={MainNavigator} />
      )}
    </Stack.Navigator>
  );
};