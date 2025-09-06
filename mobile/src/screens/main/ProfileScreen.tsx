/**
 * Profile and settings screen with privacy controls
 */

import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  Switch, 
  Alert,
  TouchableOpacity 
} from 'react-native';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Input } from '@/components/Input';
import { useAppContext } from '@/context/AppContext';
import { colors, typography, spacing } from '@/styles';
import Icon from 'react-native-vector-icons/MaterialIcons';

interface UserPreferences {
  historyEnabled: boolean;
  weeklyInsights: boolean;
  pushNotifications: boolean;
  dataSharing: boolean;
  autoSync: boolean;
}

export const ProfileScreen: React.FC = () => {
  const { state, logout } = useAppContext();
  const { user } = state;

  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState(user?.name || '');
  const [preferences, setPreferences] = useState<UserPreferences>({
    historyEnabled: user?.historyEnabled || false,
    weeklyInsights: true,
    pushNotifications: false,
    dataSharing: false,
    autoSync: true,
  });

  const handleSaveProfile = () => {
    // TODO: Implement API call to update profile
    Alert.alert('Success', 'Profile updated successfully');
    setIsEditing(false);
  };

  const handleLogout = async () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: async () => {
            try {
              await logout();
            } catch (error) {
              console.error('Logout error:', error);
              Alert.alert('Error', 'Failed to sign out. Please try again.');
            }
          },
        },
      ]
    );
  };

  const handleDeleteAccount = () => {
    Alert.alert(
      'Delete Account',
      'This will permanently delete your account and all associated data. This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            // TODO: Implement account deletion
            Alert.alert('Account Deleted', 'Your account has been deleted.');
          },
        },
      ]
    );
  };

  const handleDeleteHistory = () => {
    Alert.alert(
      'Delete Meal History',
      'This will permanently delete all your meal history and insights. This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            // TODO: Implement history deletion
            Alert.alert('History Deleted', 'Your meal history has been deleted.');
          },
        },
      ]
    );
  };

  const handleExportData = () => {
    Alert.alert(
      'Export Data',
      'Your data will be prepared for download. You will receive a notification when ready.',
      [{ text: 'OK' }]
    );
    // TODO: Implement data export
  };

  const updatePreference = (key: keyof UserPreferences, value: boolean) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
    // TODO: Implement API call to update preferences
  };

  const renderSettingItem = (
    title: string,
    description: string,
    value: boolean,
    onValueChange: (value: boolean) => void,
    icon: string
  ) => (
    <View style={styles.settingItem}>
      <View style={styles.settingInfo}>
        <Icon name={icon} size={24} color={colors.primary} style={styles.settingIcon} />
        <View style={styles.settingText}>
          <Text style={styles.settingTitle}>{title}</Text>
          <Text style={styles.settingDescription}>{description}</Text>
        </View>
      </View>
      <Switch
        value={value}
        onValueChange={onValueChange}
        trackColor={{ false: colors.gray, true: colors.primaryLight }}
        thumbColor={value ? colors.primary : colors.white}
      />
    </View>
  );

  const renderActionItem = (
    title: string,
    description: string,
    onPress: () => void,
    icon: string,
    destructive?: boolean
  ) => (
    <TouchableOpacity style={styles.actionItem} onPress={onPress}>
      <Icon 
        name={icon} 
        size={24} 
        color={destructive ? colors.error : colors.primary} 
        style={styles.settingIcon} 
      />
      <View style={styles.settingText}>
        <Text style={[styles.settingTitle, destructive && styles.destructiveText]}>
          {title}
        </Text>
        <Text style={styles.settingDescription}>{description}</Text>
      </View>
      <Icon name="chevron-right" size={24} color={colors.gray} />
    </TouchableOpacity>
  );

  if (!user) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>User not found</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Profile Section */}
      <Card style={styles.profileCard}>
        <View style={styles.profileHeader}>
          <View style={styles.avatarContainer}>
            <Icon name="person" size={40} color={colors.primary} />
          </View>
          <View style={styles.profileInfo}>
            {isEditing ? (
              <Input
                value={editedName}
                onChangeText={setEditedName}
                placeholder="Enter your name"
                style={styles.nameInput}
              />
            ) : (
              <Text style={styles.userName}>{user.name}</Text>
            )}
            <Text style={styles.userEmail}>{user.email}</Text>
            <Text style={styles.memberSince}>
              Member since {new Date(user.registrationDate).toLocaleDateString()}
            </Text>
          </View>
        </View>
        
        <View style={styles.profileActions}>
          {isEditing ? (
            <View style={styles.editActions}>
              <Button
                title="Cancel"
                onPress={() => {
                  setIsEditing(false);
                  setEditedName(user.name);
                }}
                variant="outline"
                style={styles.editButton}
              />
              <Button
                title="Save"
                onPress={handleSaveProfile}
                style={styles.editButton}
              />
            </View>
          ) : (
            <Button
              title="Edit Profile"
              onPress={() => setIsEditing(true)}
              variant="outline"
              leftIcon="edit"
            />
          )}
        </View>
      </Card>

      {/* Privacy & Data Settings */}
      <Card style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Privacy & Data</Text>
        
        {renderSettingItem(
          'Meal History',
          'Store your meal photos and analysis results',
          preferences.historyEnabled,
          (value) => updatePreference('historyEnabled', value),
          'history'
        )}
        
        {renderSettingItem(
          'Weekly Insights',
          'Generate weekly nutrition reports',
          preferences.weeklyInsights,
          (value) => updatePreference('weeklyInsights', value),
          'insights'
        )}
        
        {renderSettingItem(
          'Data Sharing',
          'Help improve our AI with anonymous data',
          preferences.dataSharing,
          (value) => updatePreference('dataSharing', value),
          'share'
        )}
      </Card>

      {/* App Settings */}
      <Card style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>App Settings</Text>
        
        {renderSettingItem(
          'Push Notifications',
          'Receive reminders and insights',
          preferences.pushNotifications,
          (value) => updatePreference('pushNotifications', value),
          'notifications'
        )}
        
        {renderSettingItem(
          'Auto Sync',
          'Automatically sync data when online',
          preferences.autoSync,
          (value) => updatePreference('autoSync', value),
          'sync'
        )}
      </Card>

      {/* Data Management */}
      <Card style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Data Management</Text>
        
        {renderActionItem(
          'Manage Consent',
          'Update your data sharing preferences',
          () => {
            // TODO: Navigate to consent screen
            Alert.alert('Consent Management', 'This would open the consent management screen.');
          },
          'privacy-tip'
        )}

        {renderActionItem(
          'Export My Data',
          'Download a copy of your data',
          handleExportData,
          'download'
        )}
        
        {renderActionItem(
          'Delete Meal History',
          'Remove all stored meal data',
          handleDeleteHistory,
          'delete-sweep',
          true
        )}
      </Card>

      {/* Account Actions */}
      <Card style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Account</Text>
        
        {renderActionItem(
          'Sign Out',
          'Sign out of your account',
          handleLogout,
          'logout'
        )}
        
        {renderActionItem(
          'Delete Account',
          'Permanently delete your account',
          handleDeleteAccount,
          'delete-forever',
          true
        )}
      </Card>

      {/* App Info */}
      <View style={styles.appInfo}>
        <Text style={styles.appVersion}>Nutrition Feedback v1.0.0</Text>
        <Text style={styles.appDescription}>
          AI-powered nutrition analysis for Nigerian students
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
  profileCard: {
    marginBottom: spacing.lg,
  },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  avatarContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  profileInfo: {
    flex: 1,
  },
  userName: {
    ...typography.h4,
    marginBottom: spacing.xs,
  },
  userEmail: {
    ...typography.body2,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  memberSince: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  nameInput: {
    marginBottom: spacing.xs,
  },
  profileActions: {
    alignItems: 'center',
  },
  editActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
  },
  editButton: {
    flex: 1,
    marginHorizontal: spacing.xs,
  },
  sectionCard: {
    marginBottom: spacing.lg,
  },
  sectionTitle: {
    ...typography.h5,
    marginBottom: spacing.md,
    color: colors.primary,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  settingInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingIcon: {
    marginRight: spacing.md,
  },
  settingText: {
    flex: 1,
  },
  settingTitle: {
    ...typography.body1,
    marginBottom: spacing.xs,
  },
  settingDescription: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  actionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  destructiveText: {
    color: colors.error,
  },
  appInfo: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
  },
  appVersion: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  appDescription: {
    ...typography.caption,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  errorText: {
    ...typography.body1,
    color: colors.error,
    textAlign: 'center',
  },
});