/**
 * Input component tests
 */

import React from 'react';
import { render } from '@testing-library/react-native';
import { Input } from '../../src/components/Input';

describe('Input Component', () => {
  it('renders correctly with label', () => {
    const { getByText } = render(
      <Input label="Test Label" value="" onChangeText={() => {}} />
    );
    
    expect(getByText('Test Label')).toBeTruthy();
  });

  it('shows error message when error prop is provided', () => {
    const { getByText } = render(
      <Input value="" onChangeText={() => {}} error="This field is required" />
    );
    
    expect(getByText('This field is required')).toBeTruthy();
  });

  it('shows helper text when provided', () => {
    const { getByText } = render(
      <Input 
        value="" 
        onChangeText={() => {}} 
        helperText="Enter your email address" 
      />
    );
    
    expect(getByText('Enter your email address')).toBeTruthy();
  });
});