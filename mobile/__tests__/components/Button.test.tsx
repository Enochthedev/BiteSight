/**
 * Button component tests
 */

import React from 'react';
import { render } from '@testing-library/react-native';
import { Button } from '../../src/components/Button';

describe('Button Component', () => {
  it('renders correctly with title', () => {
    const { getByText } = render(
      <Button title="Test Button" onPress={() => {}} />
    );
    
    expect(getByText('Test Button')).toBeTruthy();
  });

  it('renders with different variants', () => {
    const { getByText } = render(
      <Button title="Test Button" onPress={() => {}} variant="secondary" />
    );
    
    expect(getByText('Test Button')).toBeTruthy();
  });

  it('renders when disabled', () => {
    const { getByText } = render(
      <Button title="Test Button" onPress={() => {}} disabled />
    );
    
    expect(getByText('Test Button')).toBeTruthy();
  });
});