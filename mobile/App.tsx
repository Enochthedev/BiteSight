/**
 * Main App component with navigation setup
 */

import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AppProvider } from '@/context/AppContext';
import { AppNavigator } from '@/navigation/AppNavigator';
import { ErrorBoundary } from '@/components/ErrorBoundary';

const App: React.FC = () => {
  return (
    <SafeAreaProvider>
      <ErrorBoundary>
        <AppProvider>
          <NavigationContainer>
            <AppNavigator />
          </NavigationContainer>
        </AppProvider>
      </ErrorBoundary>
    </SafeAreaProvider>
  );
};

export default App;