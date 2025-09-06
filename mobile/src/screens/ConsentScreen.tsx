/**
 * Consent management screen for data privacy
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Switch,
  Alert,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { colors, typography, spacing } from '@/styles';
import Icon from 'react-native-vector-icons/MaterialIcons';

interface ConsentOptions {
  mealHistory: boolean;
  dataAnalytics: boolean;
  researchParticipation: boolean;
  marketingCommunications: boolean;
}

interface ConsentScreenProps {
  isInitialSetup?: boolean;
  onConsentComplete?: (consents: ConsentOptions) => void;
}

export const ConsentScreen: React.FC<ConsentScreenProps> = ({
  isInitialSetup = false,
  onConsentComplete,
}) => {
  const navigation = useNavigation();
  
  const [consents, setConsents] = useState<ConsentOptions>({
    mealHistory: false,
    dataAnalytics: false,
    researchParticipation: false,
    marketingCommunications: false,
  });

  const [hasReadPrivacyPolicy, setHasReadPrivacyPolicy] = useState(false);

  const handleConsentChange = (key: keyof ConsentOptions, value: boolean) => {
    setConsents(prev => ({ ...prev, [key]: value }));
  };

  const handleSaveConsents = async () => {
    if (isInitialSetup && !hasReadPrivacyPolicy) {
      Alert.alert(
        'Privacy Policy Required',
        'Please confirm that you have read and understood our privacy policy.'
      );
      return;
    }

    try {
      // TODO: Implement API call to save consent preferences
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      if (onConsentComplete) {
        onConsentComplete(consents);
      }
      
      if (isInitialSetup) {
        Alert.alert(
          'Consent Saved',
          'Your privacy preferences have been saved. You can change these anytime in settings.',
          [{ text: 'Continue', onPress: () => navigation.goBack() }]
        );
      } else {
        Alert.alert('Success', 'Your consent preferences have been updated.');
        navigation.goBack();
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to save consent preferences. Please try again.');
    }
  };

  const handleViewPrivacyPolicy = () => {
    // TODO: Navigate to privacy policy screen or open web view
    Alert.alert(
      'Privacy Policy',
      'This would open the full privacy policy. For now, this is a placeholder.',
      [{ text: 'OK' }]
    );
  };

  const renderConsentItem = (
    key: keyof ConsentOptions,
    title: string,
    description: string,
    required: boolean = false,
    icon: string
  ) => (
    <View style={styles.consentItem}>
      <View style={styles.consentHeader}>
        <Icon name={icon} size={24} color={colors.primary} style={styles.consentIcon} />
        <View style={styles.consentInfo}>
          <View style={styles.titleRow}>
            <Text style={styles.consentTitle}>{title}</Text>
            {required && <Text style={styles.requiredLabel}>Required</Text>}
          </View>
          <Text style={styles.consentDescription}>{description}</Text>
        </View>
        <Switch
          value={consents[key]}
          onValueChange={(value) => handleConsentChange(key, value)}
          trackColor={{ false: colors.gray, true: colors.primaryLight }}
          thumbColor={consents[key] ? colors.primary : colors.white}
          disabled={required}
        />
      </View>
    </View>
  );

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Icon name="security" size={60} color={colors.primary} />
        <Text style={styles.title}>Your Privacy Matters</Text>
        <Text style={styles.subtitle}>
          {isInitialSetup 
            ? 'Choose what data you\'re comfortable sharing with us'
            : 'Manage your data sharing preferences'
          }
        </Text>
      </View>

      <Card style={styles.consentCard}>
        <Text style={styles.sectionTitle}>Data Collection & Usage</Text>
        
        {renderConsentItem(
          'mealHistory',
          'Meal History Storage',
          'Store your meal photos and analysis results to track your nutrition progress over time. You can delete this data anytime.',
          false,
          'history'
        )}

        {renderConsentItem(
          'dataAnalytics',
          'App Usage Analytics',
          'Help us improve the app by sharing anonymous usage data. No personal information is included.',
          false,
          'analytics'
        )}

        {renderConsentItem(
          'researchParticipation',
          'Research Participation',
          'Contribute to nutrition research by allowing anonymous analysis of your meal patterns. Helps improve AI accuracy.',
          false,
          'science'
        )}

        {renderConsentItem(
          'marketingCommunications',
          'Marketing Communications',
          'Receive updates about new features, nutrition tips, and app improvements via email or push notifications.',
          false,
          'notifications'
        )}
      </Card>

      <Card style={styles.privacyCard}>
        <Text style={styles.sectionTitle}>Privacy & Security</Text>
        
        <View style={styles.privacyInfo}>
          <Icon name="lock" size={24} color={colors.success} />
          <View style={styles.privacyText}>
            <Text style={styles.privacyTitle}>Your Data is Secure</Text>
            <Text style={styles.privacyDescription}>
              All data is encrypted in transit and at rest. We never share personal information without your explicit consent.
            </Text>
          </View>
        </View>

        <View style={styles.privacyInfo}>
          <Icon name="delete" size={24} color={colors.primary} />
          <View style={styles.privacyText}>
            <Text style={styles.privacyTitle}>Easy Data Deletion</Text>
            <Text style={styles.privacyDescription}>
              You can delete your data or entire account anytime from the settings screen.
            </Text>
          </View>
        </View>

        <View style={styles.privacyInfo}>
          <Icon name="visibility-off" size={24} color={colors.secondary} />
          <View style={styles.privacyText}>
            <Text style={styles.privacyTitle}>No Third-Party Sharing</Text>
            <Text style={styles.privacyDescription}>
              We don't sell or share your personal data with third parties for marketing purposes.
            </Text>
          </View>
        </View>
      </Card>

      {isInitialSetup && (
        <Card style={styles.policyCard}>
          <View style={styles.policyCheck}>
            <Switch
              value={hasReadPrivacyPolicy}
              onValueChange={setHasReadPrivacyPolicy}
              trackColor={{ false: colors.gray, true: colors.primaryLight }}
              thumbColor={hasReadPrivacyPolicy ? colors.primary : colors.white}
            />
            <Text style={styles.policyText}>
              I have read and understood the{' '}
              <Text style={styles.policyLink} onPress={handleViewPrivacyPolicy}>
                Privacy Policy
              </Text>
            </Text>
          </View>
        </Card>
      )}

      <View style={styles.actions}>
        <Button
          title={isInitialSetup ? 'Continue' : 'Save Preferences'}
          onPress={handleSaveConsents}
          fullWidth
          size="large"
        />
        
        {!isInitialSetup && (
          <Button
            title="Cancel"
            onPress={() => navigation.goBack()}
            variant="text"
            style={styles.cancelButton}
          />
        )}
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>
          You can change these preferences anytime in the app settings.
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.screenPadding,
  },
  header: {
    alignItems: 'center',
    marginBottom: spacing.xl,
    paddingTop: spacing.lg,
  },
  title: {
    ...typography.h2,
    marginTop: spacing.md,
    marginBottom: spacing.sm,
    textAlign: 'center',
    color: colors.primary,
  },
  subtitle: {
    ...typography.body1,
    textAlign: 'center',
    color: colors.textSecondary,
  },
  consentCard: {
    marginBottom: spacing.lg,
  },
  sectionTitle: {
    ...typography.h5,
    marginBottom: spacing.md,
    color: colors.text,
  },
  consentItem: {
    marginBottom: spacing.md,
  },
  consentHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  consentIcon: {
    marginRight: spacing.md,
    marginTop: spacing.xs,
  },
  consentInfo: {
    flex: 1,
    marginRight: spacing.md,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  consentTitle: {
    ...typography.body1,
    fontWeight: '600',
    flex: 1,
  },
  requiredLabel: {
    ...typography.caption,
    color: colors.error,
    backgroundColor: colors.errorLight,
    paddingHorizontal: spacing.xs,
    paddingVertical: 2,
    borderRadius: 4,
    marginLeft: spacing.sm,
  },
  consentDescription: {
    ...typography.body2,
    color: colors.textSecondary,
    lineHeight: 20,
  },
  privacyCard: {
    marginBottom: spacing.lg,
  },
  privacyInfo: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: spacing.md,
  },
  privacyText: {
    flex: 1,
    marginLeft: spacing.md,
  },
  privacyTitle: {
    ...typography.body1,
    fontWeight: '600',
    marginBottom: spacing.xs,
  },
  privacyDescription: {
    ...typography.body2,
    color: colors.textSecondary,
    lineHeight: 18,
  },
  policyCard: {
    marginBottom: spacing.lg,
  },
  policyCheck: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  policyText: {
    ...typography.body2,
    marginLeft: spacing.md,
    flex: 1,
  },
  policyLink: {
    color: colors.primary,
    textDecorationLine: 'underline',
  },
  actions: {
    marginBottom: spacing.lg,
  },
  cancelButton: {
    marginTop: spacing.md,
  },
  footer: {
    alignItems: 'center',
    paddingVertical: spacing.lg,
  },
  footerText: {
    ...typography.caption,
    textAlign: 'center',
    color: colors.textSecondary,
  },
});