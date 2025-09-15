/**
 * Camera service for handling image capture, gallery selection, and permissions
 * Includes image compression and optimization for performance
 */

import { Platform, Alert, Linking } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import * as ImageManipulator from 'expo-image-manipulator';
import { MealImage, CameraPermissions } from '@/types';

export interface ImageQualityResult {
    isValid: boolean;
    issues: string[];
}

export interface CameraOptions {
    mediaTypes: ImagePicker.MediaTypeOptions;
    quality: number;
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
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
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
        const [cameraStatus, mediaLibraryStatus] = await Promise.all([
            ImagePicker.getCameraPermissionsAsync(),
            ImagePicker.getMediaLibraryPermissionsAsync(),
        ]);

        return {
            camera: cameraStatus.status === 'granted',
            storage: mediaLibraryStatus.status === 'granted',
        };
    }

    /**
     * Request camera and storage permissions
     */
    async requestPermissions(): Promise<CameraPermissions> {
        try {
            const [cameraStatus, mediaLibraryStatus] = await Promise.all([
                ImagePicker.requestCameraPermissionsAsync(),
                ImagePicker.requestMediaLibraryPermissionsAsync(),
            ]);

            const permissions = {
                camera: cameraStatus.status === 'granted',
                storage: mediaLibraryStatus.status === 'granted',
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

        try {
            const cameraOptions = { ...this.defaultOptions, ...options };

            const result = await ImagePicker.launchCameraAsync({
                mediaTypes: cameraOptions.mediaTypes,
                quality: cameraOptions.quality,
                base64: cameraOptions.includeBase64,
                exif: false,
            });

            if (result.canceled || !result.assets || result.assets.length === 0) {
                return null;
            }

            const asset = result.assets[0];
            const mealImage: MealImage = {
                uri: asset.uri,
                type: asset.type || 'image/jpeg',
                fileName: asset.fileName || `meal_${Date.now()}.jpg`,
                fileSize: asset.fileSize,
            };

            return mealImage;
        } catch (error) {
            console.error('Error capturing image:', error);
            return null;
        }
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

        try {
            const galleryOptions = { ...this.defaultOptions, ...options };

            const result = await ImagePicker.launchImageLibraryAsync({
                mediaTypes: galleryOptions.mediaTypes,
                quality: galleryOptions.quality,
                base64: galleryOptions.includeBase64,
                exif: false,
            });

            if (result.canceled || !result.assets || result.assets.length === 0) {
                return null;
            }

            const asset = result.assets[0];
            const mealImage: MealImage = {
                uri: asset.uri,
                type: asset.type || 'image/jpeg',
                fileName: asset.fileName || `meal_${Date.now()}.jpg`,
                fileSize: asset.fileSize,
            };

            return mealImage;
        } catch (error) {
            console.error('Error selecting image from gallery:', error);
            return null;
        }
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
            const manipulatedImage = await ImageManipulator.manipulateAsync(
                image.uri,
                [
                    {
                        resize: {
                            width: compressionSettings.maxWidth,
                            height: compressionSettings.maxHeight,
                        },
                    },
                ],
                {
                    compress: compressionSettings.quality / 100,
                    format: compressionSettings.format === 'JPEG'
                        ? ImageManipulator.SaveFormat.JPEG
                        : ImageManipulator.SaveFormat.PNG,
                }
            );

            const originalSize = image.fileSize || 0;
            const compressedSize = manipulatedImage.width * manipulatedImage.height * 3; // Rough estimate
            const compressionRatio = originalSize > 0 ? (originalSize - compressedSize) / originalSize : 0;

            return {
                uri: manipulatedImage.uri,
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
            const thumbnail = await ImageManipulator.manipulateAsync(
                image.uri,
                [
                    {
                        resize: {
                            width: size,
                            height: size,
                        },
                    },
                ],
                {
                    compress: 0.6, // Lower quality for thumbnails
                    format: ImageManipulator.SaveFormat.JPEG,
                }
            );

            const thumbnailSize = size * size * 3; // Rough estimate

            return {
                uri: thumbnail.uri,
                type: 'image/jpeg',
                fileName: `thumb_${image.fileName}`,
                fileSize: thumbnailSize,
                originalSize: image.fileSize,
                compressedSize: thumbnailSize,
                compressionRatio: image.fileSize ? (image.fileSize - thumbnailSize) / image.fileSize : 0,
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
            mediaTypes: ImagePicker.MediaTypeOptions.Images,
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
            mediaTypes: ImagePicker.MediaTypeOptions.Images,
            quality: isLowEndDevice ? 0.7 : 0.8,
            maxWidth: isLowEndDevice ? 800 : 1024,
            maxHeight: isLowEndDevice ? 800 : 1024,
            includeBase64: false,
        };
    }
}

export const cameraService = new CameraService();