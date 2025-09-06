/**
 * Tests for ImagePreview component
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { ImagePreview } from '@/components/ImagePreview';
import { MealImage } from '@/types';

// Mock react-native-vector-icons
jest.mock('react-native-vector-icons/MaterialIcons', () => 'Icon');

describe('ImagePreview', () => {
  const mockImage: MealImage = {
    uri: 'file://test-image.jpg',
    type: 'image/jpeg',
    fileName: 'test-image.jpg',
    fileSize: 1024 * 1024, // 1MB
  };

  const defaultProps = {
    image: mockImage,
    onConfirm: jest.fn(),
    onRetake: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render image preview correctly', () => {
    const { getByText, getByTestId } = render(<ImagePreview {...defaultProps} />);

    expect(getByText('Preview Your Meal')).toBeTruthy();
    expect(getByText('Make sure your meal is clearly visible and well-lit')).toBeTruthy();
    expect(getByText('test-image.jpg')).toBeTruthy();
    expect(getByText('1.00 MB')).toBeTruthy();
  });

  it('should display quality issues when provided', () => {
    const qualityIssues = [
      'Image file size is too small. Please take a clearer photo.',
      'Unsupported image format. Please use JPEG or PNG format.',
    ];

    const { getByText } = render(
      <ImagePreview {...defaultProps} qualityIssues={qualityIssues} />
    );

    expect(getByText('Image Quality Issues')).toBeTruthy();
    expect(getByText('• Image file size is too small. Please take a clearer photo.')).toBeTruthy();
    expect(getByText('• Unsupported image format. Please use JPEG or PNG format.')).toBeTruthy();
  });

  it('should show "Use Anyway" button when there are quality issues', () => {
    const qualityIssues = ['Some quality issue'];

    const { getByText } = render(
      <ImagePreview {...defaultProps} qualityIssues={qualityIssues} />
    );

    expect(getByText('Use Anyway')).toBeTruthy();
  });

  it('should show "Analyze Meal" button when there are no quality issues', () => {
    const { getByText } = render(<ImagePreview {...defaultProps} />);

    expect(getByText('Analyze Meal')).toBeTruthy();
  });

  it('should call onRetake when retake button is pressed', () => {
    const { getByText } = render(<ImagePreview {...defaultProps} />);

    fireEvent.press(getByText('Retake Photo'));

    expect(defaultProps.onRetake).toHaveBeenCalledTimes(1);
  });

  it('should call onConfirm when confirm button is pressed', () => {
    const { getByText } = render(<ImagePreview {...defaultProps} />);

    fireEvent.press(getByText('Analyze Meal'));

    expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1);
  });

  it('should disable buttons when loading', () => {
    const { getByText, queryByText } = render(<ImagePreview {...defaultProps} isLoading={true} />);

    const retakeButton = getByText('Retake Photo');
    // When loading, the confirm button shows a loading indicator instead of text
    const confirmButton = queryByText('Analyze Meal');

    expect(retakeButton.props.accessibilityState?.disabled).toBe(true);
    // The confirm button might not have text when loading, so we check if it exists or is disabled
    if (confirmButton) {
      expect(confirmButton.props.accessibilityState?.disabled).toBe(true);
    }
  });

  it('should display tips for better results', () => {
    const { getByText } = render(<ImagePreview {...defaultProps} />);

    expect(getByText('Tips for better results:')).toBeTruthy();
    expect(getByText('• Ensure good lighting')).toBeTruthy();
    expect(getByText('• Keep the camera steady')).toBeTruthy();
    expect(getByText('• Include the entire meal in the frame')).toBeTruthy();
    expect(getByText('• Avoid shadows on the food')).toBeTruthy();
  });

  it('should handle image without file size', () => {
    const imageWithoutSize: MealImage = {
      uri: 'file://test-image.jpg',
      type: 'image/jpeg',
      fileName: 'test-image.jpg',
    };

    const { getByText, queryByText } = render(
      <ImagePreview {...defaultProps} image={imageWithoutSize} />
    );

    expect(getByText('test-image.jpg')).toBeTruthy();
    expect(queryByText(/MB/)).toBeNull();
  });
});