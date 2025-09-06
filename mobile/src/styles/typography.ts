/**
 * Typography styles for the application
 */

import { TextStyle } from 'react-native';
import { colors } from './colors';

export const typography = {
    // Headings
    h1: {
        fontSize: 32,
        fontWeight: 'bold' as TextStyle['fontWeight'],
        lineHeight: 40,
        color: colors.textPrimary,
    },
    h2: {
        fontSize: 28,
        fontWeight: 'bold' as TextStyle['fontWeight'],
        lineHeight: 36,
        color: colors.textPrimary,
    },
    h3: {
        fontSize: 24,
        fontWeight: '600' as TextStyle['fontWeight'],
        lineHeight: 32,
        color: colors.textPrimary,
    },
    h4: {
        fontSize: 20,
        fontWeight: '600' as TextStyle['fontWeight'],
        lineHeight: 28,
        color: colors.textPrimary,
    },
    h5: {
        fontSize: 18,
        fontWeight: '600' as TextStyle['fontWeight'],
        lineHeight: 24,
        color: colors.textPrimary,
    },
    h6: {
        fontSize: 16,
        fontWeight: '600' as TextStyle['fontWeight'],
        lineHeight: 22,
        color: colors.textPrimary,
    },

    // Body text
    body1: {
        fontSize: 16,
        fontWeight: 'normal' as TextStyle['fontWeight'],
        lineHeight: 24,
        color: colors.textPrimary,
    },
    body2: {
        fontSize: 14,
        fontWeight: 'normal' as TextStyle['fontWeight'],
        lineHeight: 20,
        color: colors.textSecondary,
    },

    // Captions and labels
    caption: {
        fontSize: 12,
        fontWeight: 'normal' as TextStyle['fontWeight'],
        lineHeight: 16,
        color: colors.textSecondary,
    },
    label: {
        fontSize: 14,
        fontWeight: '500' as TextStyle['fontWeight'],
        lineHeight: 20,
        color: colors.textPrimary,
    },

    // Button text
    button: {
        fontSize: 16,
        fontWeight: '600' as TextStyle['fontWeight'],
        lineHeight: 20,
        textTransform: 'uppercase' as TextStyle['textTransform'],
    },

    // Input text
    input: {
        fontSize: 16,
        fontWeight: 'normal' as TextStyle['fontWeight'],
        lineHeight: 24,
        color: colors.textPrimary,
    },

    // Subtitles
    subtitle1: {
        fontSize: 16,
        fontWeight: '500' as TextStyle['fontWeight'],
        lineHeight: 24,
        color: colors.textPrimary,
    },
    subtitle2: {
        fontSize: 14,
        fontWeight: '500' as TextStyle['fontWeight'],
        lineHeight: 20,
        color: colors.textPrimary,
    },

    // Navigation text
    tabLabel: {
        fontSize: 12,
        fontWeight: '500' as TextStyle['fontWeight'],
        lineHeight: 16,
    },
};