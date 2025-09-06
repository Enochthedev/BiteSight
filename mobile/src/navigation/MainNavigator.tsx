/**
 * Main app navigation with bottom tabs
 */

import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { HomeScreen } from '@/screens/main/HomeScreen';
import { CameraScreen } from '@/screens/main/CameraScreen';
import { HistoryScreen } from '@/screens/main/HistoryScreen';
import { ProfileScreen } from '@/screens/main/ProfileScreen';
import { AnalysisScreen } from '@/screens/main/AnalysisScreen';
import { FeedbackScreen } from '@/screens/main/FeedbackScreen';
import { InsightsScreen } from '@/screens/main/InsightsScreen';
import { colors } from '@/styles/colors';

type MainTabParamList = {
  HomeTab: undefined;
  CameraTab: undefined;
  HistoryTab: undefined;
  ProfileTab: undefined;
};

type MainStackParamList = {
  MainTabs: undefined;
  Analysis: { mealId: string };
  Feedback: { feedbackData: any };
  Insights: undefined;
};

const Tab = createBottomTabNavigator<MainTabParamList>();
const Stack = createStackNavigator<MainStackParamList>();

const MainTabs: React.FC = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;

          switch (route.name) {
            case 'HomeTab':
              iconName = 'home';
              break;
            case 'CameraTab':
              iconName = 'camera-alt';
              break;
            case 'HistoryTab':
              iconName = 'history';
              break;
            case 'ProfileTab':
              iconName = 'person';
              break;
            default:
              iconName = 'help';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.gray,
        tabBarStyle: {
          backgroundColor: colors.white,
          borderTopWidth: 1,
          borderTopColor: colors.lightGray,
          paddingBottom: 5,
          paddingTop: 5,
          height: 60,
        },
        headerShown: false,
      })}
    >
      <Tab.Screen
        name="HomeTab"
        component={HomeScreen}
        options={{ tabBarLabel: 'Home' }}
      />
      <Tab.Screen
        name="CameraTab"
        component={CameraScreen}
        options={{ tabBarLabel: 'Camera' }}
      />
      <Tab.Screen
        name="HistoryTab"
        component={HistoryScreen}
        options={{ tabBarLabel: 'History' }}
      />
      <Tab.Screen
        name="ProfileTab"
        component={ProfileScreen}
        options={{ tabBarLabel: 'Profile' }}
      />
    </Tab.Navigator>
  );
};

export const MainNavigator: React.FC = () => {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="MainTabs" component={MainTabs} />
      <Stack.Screen name="Analysis" component={AnalysisScreen} />
      <Stack.Screen name="Feedback" component={FeedbackScreen} />
      <Stack.Screen name="Insights" component={InsightsScreen} />
    </Stack.Navigator>
  );
};