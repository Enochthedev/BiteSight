# Expo Setup Guide

This mobile app has been converted from React Native CLI to Expo. Follow these steps to get started:

## Prerequisites

1. Install Node.js (16 or later)
2. Install Expo CLI globally:
   ```bash
   npm install -g @expo/cli
   ```

## Installation

1. Install dependencies:

   ```bash
   npm install
   ```

2. Install Expo development build (if needed):
   ```bash
   npx expo install --fix
   ```

## Running the App

### Development

```bash
# Start the development server
npm start

# Run on iOS simulator
npm run ios

# Run on Android emulator
npm run android

# Run on web
npm run web
```

### Building for Production

```bash
# Build for Android
npm run build:android

# Build for iOS
npm run build:ios
```

## Key Changes Made

### Dependencies Updated

- Replaced `react-native-camera` with `expo-camera`
- Replaced `react-native-image-picker` with `expo-image-picker`
- Replaced `react-native-image-resizer` with `expo-image-manipulator`
- Replaced `react-native-vector-icons` with `@expo/vector-icons`
- Removed `react-native-permissions` (handled by Expo)

### Configuration Files

- Updated `package.json` with Expo scripts and dependencies
- Created `app.json` for Expo configuration
- Updated `babel.config.js` to use `babel-preset-expo`
- Updated `metro.config.js` for Expo
- Updated `jest.config.js` to use `jest-expo`

### Code Changes

- Updated camera service to use Expo Camera APIs
- Updated all icon imports to use `@expo/vector-icons`
- Updated permission handling to use Expo APIs
- Added `expo-status-bar` to App.tsx

## Assets Required

Add the following assets to the `assets/` directory:

- `icon.png` (1024x1024) - App icon
- `splash.png` (1242x2436 recommended) - Splash screen
- `adaptive-icon.png` (1024x1024) - Android adaptive icon
- `favicon.png` (48x48) - Web favicon

## Permissions

The app automatically handles the following permissions through Expo:

- Camera access
- Photo library access
- Media library access

## Development Tools

- Use Expo Go app for quick testing on physical devices
- Use Expo DevTools for debugging
- Use EAS Build for production builds

## Troubleshooting

1. If you encounter permission issues, make sure you have the latest Expo CLI
2. Clear Metro cache if you see bundling issues: `npx expo start --clear`
3. For iOS builds, ensure you have Xcode installed
4. For Android builds, ensure you have Android Studio and SDK installed

## Next Steps

1. Add actual asset images to the `assets/` directory
2. Test camera functionality on physical devices
3. Configure EAS Build for production deployments
4. Set up app store configurations in `app.json`
