const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

config.resolver.alias = {
    '@': './src',
};

// Enable support for Expo Router
config.resolver.unstable_enableSymlinks = true;

module.exports = config;