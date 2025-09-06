/**
 * AppContext tests
 */

import React from 'react';
import { render } from '@testing-library/react-native';
import { Text } from 'react-native';
import { AppProvider, useAppContext } from '../../src/context/AppContext';

const TestComponent: React.FC = () => {
  const { state } = useAppContext();
  
  return (
    <>
      <Text testID="auth-status">
        {state.isAuthenticated ? 'authenticated' : 'not-authenticated'}
      </Text>
      <Text testID="user-name">
        {state.user?.name || 'no-user'}
      </Text>
    </>
  );
};

describe('AppContext', () => {
  it('provides initial state', () => {
    const { getByTestId } = render(
      <AppProvider>
        <TestComponent />
      </AppProvider>
    );
    
    expect(getByTestId('auth-status')).toBeTruthy();
    expect(getByTestId('user-name')).toBeTruthy();
  });
});