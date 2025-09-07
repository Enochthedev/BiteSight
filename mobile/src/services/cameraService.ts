/**
 * Camera service for handling image capture, gallery selection, and permissions
 * Includes image compression and optimization for performance
 */

import { Platform, Alert, Linking } from 'react-native';
import { check, request, PERMISSIONS, RESULTS, Permission } from 'react-native-permissions';
import { launchCamera, launchImageLibrary, ImagePickerResponse, MediaType } from 'react-native-image-picker';
import ImageResizer from 'react-native-image-resizer';
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

export interface CompressionOptions {
    maxWidth: number;
    maxHeight: number;
    quality: number;
    format: 'JPEG' | 'PNG';
    compressImageMaxWidth?: number;
    compressImageMaxHeight?: number;
}

export interface OptimizedImage extends MealImage {
    originalSize?: number;
    compressedSize: number;
    compressionRatio?: number;
}

class CameraService {
    private defaultOptions: CameraOptions = {
        mediaType: 'photo',
        quality: 0.8,
        maxWidth: 1024,
        maxHeight: 1024,
        includeBase64: false,
    };

    private compressionOptions: CompressionOptions = {
        maxWidth: 1024,
        maxHeight: 1024,
        quality: 80,
        format: 'JPEG',
        compressImageMaxWidth: 800,
        compressImageMaxHeight: 800,
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
     * Compress and optimize image for upload
     */
    async compressImage(image: MealImage, options?: Partial<CompressionOptions>): Promise<OptimizedImage> {
        const compressionSettings = { ...this.compressionOptions, ...options };

        try {
            const resizedImage = await ImageResizer.createResizedImage(
                image.uri,
                compressionSettings.maxWidth,
                compressionSettings.maxHeight,
                compressionSettings.format,
                compressionSettings.quality,
                0, // rotation
                undefined, // outputPath
                false, // keepMeta
                {
                    mode: 'contain',
                    onlyScaleDown: true,
                }
            );

            const originalSize = image.fileSize || 0;
            const compressedSize = resizedImage.size;
            const compressionRatio = originalSize > 0 ? (originalSize - compressedSize) / originalSize : 0;

            return {
                uri: resizedImage.uri,
                type: `image/${compressionSettings.format.toLowerCase()}`,
                fileName: image.fileName.replace(/\.[^/.]+$/, `.${compressionSettings.format.toLowerCase()}`),
                fileSize: compressedSize,
                originalSize,
                compressedSize,
                compressionRatio,
            };
        } catch (error) {
            console.error('Image compression failed:', error);
            // Return original image if compression fails
            return {
                ...image,
                compressedSize: image.fileSize || 0,
            };
        }
    }

    /**
     * Create thumbnail for image preview
     */
    async createThumbnail(image: MealImage, size: number = 200): Promise<OptimizedImage> {
        try {
            const thumbnail = await ImageResizer.createResizedImage(
                image.uri,
                size,
                size,
                'JPEG',
                60, // Lower quality for thumbnails
                0,
                undefined,
                false,
                {
                    mode: 'cover',
                }
            );

            return {
                uri: thumbnail.uri,
                type: 'image/jpeg',
                fileName: `thumb_${image.fileName}`,
                fileSize: thumbnail.size,
                originalSize: image.fileSize,
                compressedSize: thumbnail.size,
                compressionRatio: image.fileSize ? (image.fileSize - thumbnail.size) / image.fileSize : 0,
            };
        } catch (error) {
            console.error('Thumbnail creation failed:', error);
            return {
                ...image,
                compressedSize: image.fileSize || 0,
            };
        }
    }

    /**
     * Optimize image based on network conditions
     */
    async optimizeForNetwork(image: MealImage, networkType: 'wifi' | 'cellular' | 'slow'): Promise<OptimizedImage> {
        let compressionOptions: Partial<CompressionOptions>;

        switch (networkType) {
            case 'wifi':
                compressionOptions = {
                    maxWidth: 1024,
                    maxHeight: 1024,
                    quality: 85,
                };
                break;
            case 'cellular':
                compressionOptions = {
                    maxWidth: 800,
                    maxHeight: 800,
                    quality: 75,
                };
                break;
            case 'slow':
                compressionOptions = {
                    maxWidth: 600,
                    maxHeight: 600,
                    quality: 60,
                };
                break;
            default:
                compressionOptions = this.compressionOptions;
        }

        return this.compressImage(image, compressionOptions);
    }

    /**
     * Batch compress multiple images
     */
    async compressImages(images: MealImage[], options?: Partial<CompressionOptions>): Promise<OptimizedImage[]> {
        const compressionPromises = images.map(image => this.compressImage(image, options));
        return Promise.all(compressionPromises);
    }

    /**
     * Get compression statistics
     */
    getCompressionStats(optimizedImages: OptimizedImage[]): {
        totalOriginalSize: number;
        totalCompressedSize: number;
        totalSavings: number;
        averageCompressionRatio: number;
    } {
        const totalOriginalSize = optimizedImages.reduce((sum, img) => sum + (img.originalSize || 0), 0);
        const totalCompressedSize = optimizedImages.reduce((sum, img) => sum + img.compressedSize, 0);
        const totalSavings = totalOriginalSize - totalCompressedSize;
        const averageCompressionRatio = optimizedImages.length > 0
            ? optimizedImages.reduce((sum, img) => sum + (img.compressionRatio || 0), 0) / optimizedImages.length
            : 0;

        return {
            totalOriginalSize,
            totalCompressedSize,
            totalSavings,
            averageCompressionRatio,
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

    /**
     * Get optimized camera options based on device capabilities
     */
    getOptimizedCameraOptions(): CameraOptions {
        // Adjust quality based on platform and device capabilities
        const isLowEndDevice = Platform.OS === 'android'; // Simplified check

        return {
            mediaType: 'photo',
            quality: isLowEndDevice ? 0.7 : 0.8,
            maxWidth: isLowEndDevice ? 800 : 1024,
            maxHeight: isLowEndDevice ? 800 : 1024,
            includeBase64: false,
        };
    }
}

export const cameraService = new CameraService();