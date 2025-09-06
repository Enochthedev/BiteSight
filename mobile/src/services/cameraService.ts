/**
 * Camera service for handling image capture, gallery selection, and permissions
 */

import { Platform, Alert, Linking } from 'react-native';
import { check, request, PERMISSIONS, RESULTS, Permission } from 'react-native-permissions';
import { launchCamera, launchImageLibrary, ImagePickerResponse, MediaType } from 'react-native-image-picker';
import { MealImage, CameraPermissions } from '@/types';

export interface ImageQualityResult {
    isValid: boolean;
    issues: string[];
}

export interface CameraOptions {
    mediaType: MediaType;
    quality: 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 | 0.7 | 0.8 | 0.9 | 1.0;
    maxWidth: number;
    maxHeight: number;
    includeBase64: boolean;
}

class CameraService {
    private defaultOptions: CameraOptions = {
        mediaType: 'photo',
        quality: 0.8,
        maxWidth: 1024,
        maxHeight: 1024,
        includeBase64: false,
    };

    /**
     * Check camera and storage permissions
     */
    async checkPermissions(): Promise<CameraPermissions> {
        const cameraPermission = Platform.OS === 'ios'
            ? PERMISSIONS.IOS.CAMERA
            : PERMISSIONS.ANDROID.CAMERA;

        const storagePermission = Platform.OS === 'ios'
            ? PERMISSIONS.IOS.PHOTO_LIBRARY
            : PERMISSIONS.ANDROID.READ_EXTERNAL_STORAGE;

        const [cameraStatus, storageStatus] = await Promise.all([
            check(cameraPermission),
            check(storagePermission),
        ]);

        return {
            camera: cameraStatus === RESULTS.GRANTED,
            storage: storageStatus === RESULTS.GRANTED,
        };
    }

    /**
     * Request camera and storage permissions
     */
    async requestPermissions(): Promise<CameraPermissions> {
        const cameraPermission = Platform.OS === 'ios'
            ? PERMISSIONS.IOS.CAMERA
            : PERMISSIONS.ANDROID.CAMERA;

        const storagePermission = Platform.OS === 'ios'
            ? PERMISSIONS.IOS.PHOTO_LIBRARY
            : PERMISSIONS.ANDROID.READ_EXTERNAL_STORAGE;

        try {
            const [cameraStatus, storageStatus] = await Promise.all([
                request(cameraPermission),
                request(storagePermission),
            ]);

            const permissions = {
                camera: cameraStatus === RESULTS.GRANTED,
                storage: storageStatus === RESULTS.GRANTED,
            };

            // If permissions are denied, show alert with settings option
            if (!permissions.camera || !permissions.storage) {
                this.showPermissionAlert();
            }

            return permissions;
        } catch (error) {
            console.error('Error requesting permissions:', error);
            return { camera: false, storage: false };
        }
    }

    /**
     * Show alert for permission denial with option to open settings
     */
    private showPermissionAlert(): void {
        Alert.alert(
            'Permissions Required',
            'This app needs camera and storage permissions to capture and save meal photos. Please enable them in your device settings.',
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Open Settings',
                    onPress: () => Linking.openSettings()
                },
            ]
        );
    }

    /**
     * Capture image using device camera
     */
    async captureImage(options?: Partial<CameraOptions>): Promise<MealImage | null> {
        const permissions = await this.checkPermissions();

        if (!permissions.camera) {
            const newPermissions = await this.requestPermissions();
            if (!newPermissions.camera) {
                throw new Error('Camera permission is required to take photos');
            }
        }

        return new Promise((resolve) => {
            const cameraOptions = { ...this.defaultOptions, ...options };

            launchCamera(cameraOptions, (response: ImagePickerResponse) => {
                if (response.didCancel || response.errorMessage) {
                    resolve(null);
                    return;
                }

                const asset = response.assets?.[0];
                if (!asset) {
                    resolve(null);
                    return;
                }

                const mealImage: MealImage = {
                    uri: asset.uri!,
                    type: asset.type || 'image/jpeg',
                    fileName: asset.fileName || `meal_${Date.now()}.jpg`,
                    fileSize: asset.fileSize,
                };

                resolve(mealImage);
            });
        });
    }

    /**
     * Select image from device gallery
     */
    async selectFromGallery(options?: Partial<CameraOptions>): Promise<MealImage | null> {
        const permissions = await this.checkPermissions();

        if (!permissions.storage) {
            const newPermissions = await this.requestPermissions();
            if (!newPermissions.storage) {
                throw new Error('Storage permission is required to access photos');
            }
        }

        return new Promise((resolve) => {
            const galleryOptions = { ...this.defaultOptions, ...options };

            launchImageLibrary(galleryOptions, (response: ImagePickerResponse) => {
                if (response.didCancel || response.errorMessage) {
                    resolve(null);
                    return;
                }

                const asset = response.assets?.[0];
                if (!asset) {
                    resolve(null);
                    return;
                }

                const mealImage: MealImage = {
                    uri: asset.uri!,
                    type: asset.type || 'image/jpeg',
                    fileName: asset.fileName || `meal_${Date.now()}.jpg`,
                    fileSize: asset.fileSize,
                };

                resolve(mealImage);
            });
        });
    }

    /**
     * Validate image quality for meal analysis
     */
    validateImageQuality(image: MealImage): ImageQualityResult {
        const issues: string[] = [];

        // Check file size (minimum 50KB, maximum 10MB)
        if (image.fileSize) {
            const minSize = 50 * 1024; // 50KB
            const maxSize = 10 * 1024 * 1024; // 10MB

            if (image.fileSize < minSize) {
                issues.push('Image file size is too small. Please take a clearer photo.');
            }

            if (image.fileSize > maxSize) {
                issues.push('Image file size is too large. Please compress the image or take a new photo.');
            }
        }

        // Check file type
        const supportedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
        if (!supportedTypes.includes(image.type.toLowerCase())) {
            issues.push('Unsupported image format. Please use JPEG or PNG format.');
        }

        // Check filename for basic validation
        if (!image.fileName || image.fileName.length === 0) {
            issues.push('Invalid image file. Please try again.');
        }

        return {
            isValid: issues.length === 0,
            issues,
        };
    }

    /**
     * Get recommended camera options for meal photos
     */
    getMealPhotoOptions(): CameraOptions {
        return {
            mediaType: 'photo',
            quality: 0.8,
            maxWidth: 1024,
            maxHeight: 1024,
            includeBase64: false,
        };
    }
}

export const cameraService = new CameraService();