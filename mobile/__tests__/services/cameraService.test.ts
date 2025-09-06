/**
 * Tests for camera service functionality
 */

import { cameraService, ImageQualityResult } from '@/services/cameraService';
import { MealImage } from '@/types';

// Mock react-native-permissions
jest.mock('react-native-permissions', () => ({
    check: jest.fn(),
    request: jest.fn(),
    PERMISSIONS: {
        IOS: {
            CAMERA: 'ios.permission.CAMERA',
            PHOTO_LIBRARY: 'ios.permission.PHOTO_LIBRARY',
        },
        ANDROID: {
            CAMERA: 'android.permission.CAMERA',
            READ_EXTERNAL_STORAGE: 'android.permission.READ_EXTERNAL_STORAGE',
        },
    },
    RESULTS: {
        GRANTED: 'granted',
        DENIED: 'denied',
        BLOCKED: 'blocked',
    },
}));

// Mock react-native-image-picker
jest.mock('react-native-image-picker', () => ({
    launchCamera: jest.fn(),
    launchImageLibrary: jest.fn(),
}));

// Mock react-native
jest.mock('react-native', () => ({
    Platform: { OS: 'android' },
    Alert: {
        alert: jest.fn(),
    },
    Linking: {
        openSettings: jest.fn(),
    },
}));

describe('CameraService', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('validateImageQuality', () => {
        it('should validate image with good quality', () => {
            const goodImage: MealImage = {
                uri: 'file://test.jpg',
                type: 'image/jpeg',
                fileName: 'test.jpg',
                fileSize: 1024 * 1024, // 1MB
            };

            const result: ImageQualityResult = cameraService.validateImageQuality(goodImage);

            expect(result.isValid).toBe(true);
            expect(result.issues).toHaveLength(0);
        });

        it('should detect file size too small', () => {
            const smallImage: MealImage = {
                uri: 'file://test.jpg',
                type: 'image/jpeg',
                fileName: 'test.jpg',
                fileSize: 1024, // 1KB - too small
            };

            const result: ImageQualityResult = cameraService.validateImageQuality(smallImage);

            expect(result.isValid).toBe(false);
            expect(result.issues).toContain('Image file size is too small. Please take a clearer photo.');
        });

        it('should detect file size too large', () => {
            const largeImage: MealImage = {
                uri: 'file://test.jpg',
                type: 'image/jpeg',
                fileName: 'test.jpg',
                fileSize: 15 * 1024 * 1024, // 15MB - too large
            };

            const result: ImageQualityResult = cameraService.validateImageQuality(largeImage);

            expect(result.isValid).toBe(false);
            expect(result.issues).toContain('Image file size is too large. Please compress the image or take a new photo.');
        });

        it('should detect unsupported file type', () => {
            const unsupportedImage: MealImage = {
                uri: 'file://test.gif',
                type: 'image/gif',
                fileName: 'test.gif',
                fileSize: 1024 * 1024,
            };

            const result: ImageQualityResult = cameraService.validateImageQuality(unsupportedImage);

            expect(result.isValid).toBe(false);
            expect(result.issues).toContain('Unsupported image format. Please use JPEG or PNG format.');
        });

        it('should detect invalid filename', () => {
            const invalidImage: MealImage = {
                uri: 'file://test.jpg',
                type: 'image/jpeg',
                fileName: '',
                fileSize: 1024 * 1024,
            };

            const result: ImageQualityResult = cameraService.validateImageQuality(invalidImage);

            expect(result.isValid).toBe(false);
            expect(result.issues).toContain('Invalid image file. Please try again.');
        });

        it('should handle multiple issues', () => {
            const problematicImage: MealImage = {
                uri: 'file://test.gif',
                type: 'image/gif',
                fileName: '',
                fileSize: 1024, // Too small
            };

            const result: ImageQualityResult = cameraService.validateImageQuality(problematicImage);

            expect(result.isValid).toBe(false);
            expect(result.issues).toHaveLength(3);
            expect(result.issues).toContain('Image file size is too small. Please take a clearer photo.');
            expect(result.issues).toContain('Unsupported image format. Please use JPEG or PNG format.');
            expect(result.issues).toContain('Invalid image file. Please try again.');
        });
    });

    describe('getMealPhotoOptions', () => {
        it('should return correct camera options for meal photos', () => {
            const options = cameraService.getMealPhotoOptions();

            expect(options).toEqual({
                mediaType: 'photo',
                quality: 0.8,
                maxWidth: 1024,
                maxHeight: 1024,
                includeBase64: false,
            });
        });
    });

    describe('checkPermissions', () => {
        it('should check camera and storage permissions', async () => {
            const { check, PERMISSIONS, RESULTS } = require('react-native-permissions');

            check
                .mockResolvedValueOnce(RESULTS.GRANTED) // Camera permission
                .mockResolvedValueOnce(RESULTS.GRANTED); // Storage permission

            const permissions = await cameraService.checkPermissions();

            expect(check).toHaveBeenCalledWith(PERMISSIONS.ANDROID.CAMERA);
            expect(check).toHaveBeenCalledWith(PERMISSIONS.ANDROID.READ_EXTERNAL_STORAGE);
            expect(permissions).toEqual({
                camera: true,
                storage: true,
            });
        });

        it('should handle denied permissions', async () => {
            const { check, PERMISSIONS, RESULTS } = require('react-native-permissions');

            check
                .mockResolvedValueOnce(RESULTS.DENIED) // Camera permission
                .mockResolvedValueOnce(RESULTS.GRANTED); // Storage permission

            const permissions = await cameraService.checkPermissions();

            expect(permissions).toEqual({
                camera: false,
                storage: true,
            });
        });
    });

    describe('requestPermissions', () => {
        it('should request camera and storage permissions', async () => {
            const { request, PERMISSIONS, RESULTS } = require('react-native-permissions');

            request
                .mockResolvedValueOnce(RESULTS.GRANTED) // Camera permission
                .mockResolvedValueOnce(RESULTS.GRANTED); // Storage permission

            const permissions = await cameraService.requestPermissions();

            expect(request).toHaveBeenCalledWith(PERMISSIONS.ANDROID.CAMERA);
            expect(request).toHaveBeenCalledWith(PERMISSIONS.ANDROID.READ_EXTERNAL_STORAGE);
            expect(permissions).toEqual({
                camera: true,
                storage: true,
            });
        });

        it('should show permission alert when denied', async () => {
            const { request, PERMISSIONS, RESULTS } = require('react-native-permissions');
            const { Alert } = require('react-native');

            request
                .mockResolvedValueOnce(RESULTS.DENIED) // Camera permission
                .mockResolvedValueOnce(RESULTS.GRANTED); // Storage permission

            const permissions = await cameraService.requestPermissions();

            expect(Alert.alert).toHaveBeenCalledWith(
                'Permissions Required',
                'This app needs camera and storage permissions to capture and save meal photos. Please enable them in your device settings.',
                expect.any(Array)
            );
            expect(permissions).toEqual({
                camera: false,
                storage: true,
            });
        });

        it('should handle permission request errors', async () => {
            const { request } = require('react-native-permissions');

            request.mockRejectedValue(new Error('Permission request failed'));

            const permissions = await cameraService.requestPermissions();

            expect(permissions).toEqual({
                camera: false,
                storage: false,
            });
        });
    });
});