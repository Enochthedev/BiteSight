/**
 * Tests for CameraScreen component
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { CameraScreen } from '@/screens/main/CameraScreen';
import { cameraService } from '@/services/cameraService';

// Mock navigation
const mockNavigate = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

// Mock camera service
jest.mock('@/services/cameraService', () => ({
  cameraService: {
    checkPermissions: jest.fn(),
    requestPermissions: jest.fn(),
    selectFromGallery: jest.fn(),
    validateImageQuality: jest.fn(),
  },
}));

// Mock react-native-vector-icons
jest.mock('react-native-vector-icons/MaterialIcons', () => 'Icon');

// Mock components
jest.mock('@/components/ImagePreview', () => {
  const React = require('react');
  const { View, Text, TouchableOpacity } = require('react-native');
  
  return {
    ImagePreview: ({ onConfirm, onRetake }: any) => 
      React.createElement(View, {}, [
        React.createElement(TouchableOpacity, { key: 'confirm', onPress: onConfirm }, 
          React.createElement(Text, {}, 'Confirm Image')
        ),
        React.createElement(TouchableOpacity, { key: 'retake', onPress: onRetake }, 
          React.createElement(Text, {}, 'Retake Photo')
        )
      ])
  };
});

jest.mock('@/components/CameraCapture', () => {
  const React = require('react');
  const { View, Text, TouchableOpacity } = require('react-native');
  
  return {
    CameraCapture: ({ onImageCaptured, onClose }: any) => 
      React.createElement(View, {}, [
        React.createElement(TouchableOpacity, { 
          key: 'capture', 
          onPress: () => onImageCaptured({ uri: 'test://image.jpg', type: 'image/jpeg', fileName: 'test.jpg' })
        }, React.createElement(Text, {}, 'Capture Image')),
        React.createElement(TouchableOpacity, { key: 'close', onPress: onClose }, 
          React.createElement(Text, {}, 'Close Camera')
        )
      ])
  };
});

describe('CameraScreen', () => {
  const mockCameraService = cameraService as jest.Mocked<typeof cameraService>;

  beforeEach(() => {
    jest.clearAllMocks();
    mockCameraService.checkPermissions.mockResolvedValue({
      camera: true,
      storage: true,
    });
    mockCameraService.requestPermissions.mockResolvedValue({
      camera: true,
      storage: true,
    });
    mockCameraService.selectFromGallery.mockResolvedValue(null);
    mockCameraService.validateImageQuality.mockReturnValue({
      isValid: true,
      issues: [],
    });
  });

  it('should render camera selection screen by default', async () => {
    const { getByText } = render(<CameraScreen />);

    await waitFor(() => {
      expect(getByText('Capture Your Meal')).toBeTruthy();
      expect(getByText('Take Photo')).toBeTruthy();
      expect(getByText('Choose from Gallery')).toBeTruthy();
    });
  });

  it('should display tips for better results', async () => {
    const { getByText } = render(<CameraScreen />);

    await waitFor(() => {
      expect(getByText('For best results:')).toBeTruthy();
      expect(getByText('Use good lighting')).toBeTruthy();
      expect(getByText('Keep food in center of frame')).toBeTruthy();
      expect(getByText('Hold camera steady')).toBeTruthy();
      expect(getByText('Ensure all food is visible')).toBeTruthy();
    });
  });

  it('should show permission notice when permissions are not granted', async () => {
    mockCameraService.checkPermissions.mockResolvedValue({
      camera: false,
      storage: false,
    });

    const { getByText } = render(<CameraScreen />);

    await waitFor(() => {
      expect(getByText(/Camera and storage permissions are required/)).toBeTruthy();
    });
  });

  it('should handle gallery selection', async () => {
    const mockImage = {
      uri: 'file://test-image.jpg',
      type: 'image/jpeg',
      fileName: 'test-image.jpg',
      fileSize: 1024 * 1024,
    };

    mockCameraService.selectFromGallery.mockResolvedValue(mockImage);

    const { getByText } = render(<CameraScreen />);

    await waitFor(() => {
      fireEvent.press(getByText('Choose from Gallery'));
    });

    await waitFor(() => {
      expect(mockCameraService.selectFromGallery).toHaveBeenCalled();
    });
  });

  it('should handle gallery selection error', async () => {
    mockCameraService.selectFromGallery.mockRejectedValue(new Error('Gallery error'));

    const { getByText } = render(<CameraScreen />);

    await waitFor(() => {
      fireEvent.press(getByText('Choose from Gallery'));
    });

    await waitFor(() => {
      expect(mockCameraService.selectFromGallery).toHaveBeenCalled();
    });
  });

  it('should request permissions when camera button is pressed without permissions', async () => {
    mockCameraService.checkPermissions.mockResolvedValue({
      camera: false,
      storage: true,
    });

    mockCameraService.requestPermissions.mockResolvedValue({
      camera: true,
      storage: true,
    });

    const { getByText } = render(<CameraScreen />);

    await waitFor(() => {
      fireEvent.press(getByText('Take Photo'));
    });

    await waitFor(() => {
      expect(mockCameraService.requestPermissions).toHaveBeenCalled();
    });
  });

  it('should request permissions when gallery button is pressed without permissions', async () => {
    mockCameraService.checkPermissions.mockResolvedValue({
      camera: true,
      storage: false,
    });

    mockCameraService.requestPermissions.mockResolvedValue({
      camera: true,
      storage: true,
    });

    const { getByText } = render(<CameraScreen />);

    await waitFor(() => {
      fireEvent.press(getByText('Choose from Gallery'));
    });

    await waitFor(() => {
      expect(mockCameraService.requestPermissions).toHaveBeenCalled();
    });
  });

  it('should navigate to analysis screen when image is confirmed', async () => {
    const mockImage = {
      uri: 'file://test-image.jpg',
      type: 'image/jpeg',
      fileName: 'test-image.jpg',
      fileSize: 1024 * 1024,
    };

    mockCameraService.selectFromGallery.mockResolvedValue(mockImage);

    const { getByText } = render(<CameraScreen />);

    // Select image from gallery
    await waitFor(() => {
      fireEvent.press(getByText('Choose from Gallery'));
    });

    // Wait for preview to appear and confirm
    await waitFor(() => {
      const confirmButton = getByText('Confirm Image');
      fireEvent.press(confirmButton);
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('Analysis', {
        mealId: expect.stringMatching(/^temp_\d+$/),
        imageUri: 'file://test-image.jpg',
      });
    });
  });
});