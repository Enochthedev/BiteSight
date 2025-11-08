import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Switch,
  Alert,
  Linking,
  Platform,
  Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Notifications from 'expo-notifications';
import { RadialGradientMask } from '../../components/GradientIcon';
import COLORS from '../../styles/colors';
import { useRouter } from 'expo-router';
import { useSettings } from '../../context/SettingsContext';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// Responsive scaling functions
const scale = (size: number) => (SCREEN_WIDTH / 375) * size;
const verticalScale = (size: number) => (SCREEN_HEIGHT / 812) * size;
const moderateScale = (size: number, factor = 0.5) => size + (scale(size) - size) * factor;
const normalize = (size: number) => {
  const newSize = size * (SCREEN_WIDTH / 375);
  if (Platform.OS === 'ios') {
    return Math.round(newSize);
  } else {
    return Math.round(newSize) - 2;
  }
};

// Configure notifications
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

interface UserData {
  fullName: string;
  email: string;
}

const Settings: React.FC = () => {
  // Get settings from context
  const { 
    saveToHistory, 
    setSaveToHistory, 
    autoTagMealTime, 
    setAutoTagMealTime 
  } = useSettings();

  // State management
  const [userData, setUserData] = useState<UserData>({
    fullName: 'Ola Oluwaseun',
    email: 'olaoluwaseun@gmail.com',
  });
  const [mealReminders, setMealReminders] = useState(false);
  const [soundVibrations, setSoundVibrations] = useState(false);
  const [hasHistory, setHasHistory] = useState(false);
  const [hasCache, setHasCache] = useState(false);

  // Load saved settings on mount
  useEffect(() => {
  loadSettings();
  checkHistoryStatus();
  loadUserData();
}, []);


  const loadSettings = async () => {
    try {
      const savedSettings = await AsyncStorage.getItem('userSettings');
      if (savedSettings) {
        const settings = JSON.parse(savedSettings);
        setMealReminders(settings.mealReminders ?? false);
        setSoundVibrations(settings.soundVibrations ?? false);
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const saveSettings = async (key: string, value: boolean) => {
    try {
      const currentSettings = await AsyncStorage.getItem('userSettings');
      const settings = currentSettings ? JSON.parse(currentSettings) : {};
      settings[key] = value;
      await AsyncStorage.setItem('userSettings', JSON.stringify(settings));
    } catch (error) {
      console.error('Error saving settings:', error);
    }
  };

  const checkHistoryStatus = async () => {
    try {
      const history = await AsyncStorage.getItem('mealHistory');
      setHasHistory(history !== null && JSON.parse(history).length > 0);
      
      const cache = await AsyncStorage.getItem('appCache');
      setHasCache(cache !== null);
    } catch (error) {
      console.error('Error checking history:', error);
    }
  };

  // Handle toggle changes - Updated to use context
  const handleSaveToHistory = async (value: boolean) => {
    setSaveToHistory(value);
  };

  const handleAutoTagMealTime = async (value: boolean) => {
    setAutoTagMealTime(value);
  };

  const handleMealReminders = async (value: boolean) => {
    setMealReminders(value);
    await saveSettings('mealReminders', value);
    
    if (value) {
      await scheduleMealReminders();
    } else {
      await cancelMealReminders();
    }
  };

  const handleSoundVibrations = async (value: boolean) => {
    setSoundVibrations(value);
    await saveSettings('soundVibrations', value);
  };

  // Schedule meal reminder notifications
  const scheduleMealReminders = async () => {
    const { status } = await Notifications.requestPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Please enable notifications to receive meal reminders.');
      return;
    }

    await Notifications.cancelAllScheduledNotificationsAsync();

    await Notifications.scheduleNotificationAsync({
      content: {
        title: '🍳 Good Morning!',
        body: "It's breakfast time! Have you analyzed your meal today?",
        sound: soundVibrations,
        vibrate: soundVibrations ? [0, 250, 250, 250] : undefined,
      },
      trigger: {
        type: Notifications.SchedulableTriggerInputTypes.CALENDAR,
        hour: 8,
        minute: 0,
        repeats: true,
      },
    });

    await Notifications.scheduleNotificationAsync({
      content: {
        title: '🥗 Lunch Time!',
        body: "Ready for lunch? Let's see what's on your plate!",
        sound: soundVibrations,
        vibrate: soundVibrations ? [0, 250, 250, 250] : undefined,
      },
      trigger: {
        type: Notifications.SchedulableTriggerInputTypes.CALENDAR,
        hour: 13,
        minute: 0,
        repeats: true,
      },
    });

    await Notifications.scheduleNotificationAsync({
      content: {
        title: '🍽️ Dinner Time!',
        body: "Time for dinner! Don't forget to analyze your meal.",
        sound: soundVibrations,
        vibrate: soundVibrations ? [0, 250, 250, 250] : undefined,
      },
      trigger: {
        type: Notifications.SchedulableTriggerInputTypes.CALENDAR,
        hour: 20,
        minute: 0,
        repeats: true,
      },
    });

    Alert.alert('Success', 'Meal reminders have been scheduled!');
  };

  const cancelMealReminders = async () => {
    await Notifications.cancelAllScheduledNotificationsAsync();
  };

  // Handle browser actions
  const handleChangePassword = () => {
    const resetUrl = `https://yourapp.com/reset-password?email=${userData.email}`;
    Linking.openURL(resetUrl).catch(() => {
      Alert.alert('Error', 'Could not open password reset page');
    });
  };

  const handleEditProfile = () => {
    const editUrl = `https://yourapp.com/edit-profile?email=${userData.email}`;
    Linking.openURL(editUrl).catch(() => {
      Alert.alert('Error', 'Could not open profile edit page');
    });
  };

  const handleAboutApp = () => {
    const aboutUrl = 'https://yourapp.com/about?version=1.0.0';
    Linking.openURL(aboutUrl).catch(() => {
      Alert.alert('Error', 'Could not open app information page');
    });
  };

  const handleHelpFAQ = () => {
    const faqUrl = 'https://yourapp.com/faq';
    Linking.openURL(faqUrl).catch(() => {
      Alert.alert('Error', 'Could not open FAQ page');
    });
  };

  const handleDeleteAccount = async () => {
    Alert.alert(
      'Delete Account',
      'Are you sure you want to delete your account? This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Continue',
          style: 'destructive',
          onPress: async () => {
            try {
              await fetch('https://yourapi.com/request-account-deletion', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: userData.email }),
              });
              
              Alert.alert(
                'Check Your Email',
                `We've sent an account deletion link to ${userData.email}. Please check your email and click the link to complete the account deletion process.`,
                [{ text: 'OK' }]
              );
            } catch (error) {
              Alert.alert('Error', 'Failed to send deletion email. Please try again later.');
            }
          },
        },
      ]
    );
  };

  // Handle clear actions
  const handleClearHistory = async () => {
    if (!hasHistory) return;

    Alert.alert(
      'Clear History',
      'Are you sure you want to clear all your meal analysis history?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              await AsyncStorage.removeItem('mealHistory');
              setHasHistory(false);
              Alert.alert('Success', 'Meal history has been cleared');
            } catch (error) {
              Alert.alert('Error', 'Failed to clear history');
            }
          },
        },
      ]
    );
  };

  const handleClearCache = async () => {
    if (!hasCache) return;

    try {
      await AsyncStorage.removeItem('appCache');
      setHasCache(false);
      Alert.alert('Success', 'Cache has been cleared');
    } catch (error) {
      Alert.alert('Error', 'Failed to clear cache');
    }
  };

  const router = useRouter();

  const loadUserData = async () => {
    try {
      const storedName = await AsyncStorage.getItem("userName");
      const storedEmail = await AsyncStorage.getItem("userEmail");

      setUserData(prev => ({
        ...prev,
        fullName: storedName || prev.fullName,
        email: storedEmail || prev.email,
      }));
    } catch (error) {
      console.log("Error loading user data:", error);
    }
  };


  return (
    <View style={styles.screen}>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Ionicons name="chevron-back" size={moderateScale(24)} color={COLORS.textColor} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Settings</Text>
          <View style={styles.backButton} />
        </View>

        <ScrollView 
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Profile Section */}
          <View style={styles.profileSection}>
            <View style={styles.avatarContainer}>
              <RadialGradientMask 
                colors={['#A4A75F', '#764C8D']} 
                width={moderateScale(36)} 
                height={moderateScale(36)}
              >
                <Ionicons name="person" size={moderateScale(36)} color="black" />
              </RadialGradientMask>
            </View>
            <View style={styles.nameRow}>
              <Text style={styles.userName}>{userData.fullName}</Text>
              <TouchableOpacity onPress={handleEditProfile} activeOpacity={0.7}>
                <RadialGradientMask colors={['#A4A75F', '#764C8D']} width={moderateScale(20)} height={moderateScale(20)}>
                  <Ionicons name="create-outline" size={moderateScale(20)} color="black" />
                </RadialGradientMask>
              </TouchableOpacity>
            </View>
            <Text style={styles.userEmail}>{userData.email}</Text>
            <TouchableOpacity 
              style={styles.changePasswordButton}
              onPress={handleChangePassword}
              activeOpacity={0.7}
            >
              <Ionicons name="lock-closed" size={moderateScale(14)} color="#E63946" />
              <Text style={styles.changePasswordText}>Change password</Text>
            </TouchableOpacity>
          </View>

          {/* Preferences Section */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Preferences</Text>
            <View style={styles.card}>
              <View style={styles.settingItem_1}>
                <Ionicons name="save-outline" size={moderateScale(20)} color={COLORS.textColor} />
                <Text style={styles.settingText}>Save analyzed meals to history</Text>
                <Switch 
                  value={saveToHistory}
                  onValueChange={handleSaveToHistory}
                  trackColor={{ false: '#999999', true: COLORS.buttonColor }}
                  thumbColor="#FFFFFF"
                  style={styles.switch}
                />
              </View>
              <View style={styles.divider} />
              <View style={styles.settingItem_1}>
                <Ionicons name="time-outline" size={moderateScale(20)} color={COLORS.textColor} />
                <Text style={styles.settingText}>Auto-tag meal time</Text>
                <Switch
                  value={autoTagMealTime}
                  onValueChange={handleAutoTagMealTime}
                  trackColor={{ false: '#999999', true: COLORS.buttonColor }}
                  thumbColor="#FFFFFF"
                  style={styles.switch}
                />
              </View>
            </View>
          </View>

          {/* Notifications Section */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Notifications</Text>
            <View style={styles.card}>
              <View style={styles.settingItem_1}>
                <Ionicons name="notifications-outline" size={moderateScale(20)} color={COLORS.textColor} />
                <Text style={styles.settingText}>Meal analysis reminders</Text>
                <Switch
                  value={mealReminders}
                  onValueChange={handleMealReminders}
                  trackColor={{ false: '#999999', true: COLORS.buttonColor }}
                  thumbColor="#FFFFFF"
                  style={styles.switch}
                />
              </View>
              <View style={styles.divider} />
              <View style={styles.settingItem_1}>
                <Ionicons name="volume-high-outline" size={moderateScale(20)} color={COLORS.textColor} />
                <Text style={styles.settingText}>Sound & Vibrations</Text>
                <Switch
                  value={soundVibrations}
                  onValueChange={handleSoundVibrations}
                  trackColor={{ false: '#999999', true: COLORS.buttonColor }}
                  thumbColor="#FFFFFF"
                  style={styles.switch}
                />
              </View>
            </View>
          </View>

          {/* Storage & Data Section */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Storage & Data</Text>
            <View style={styles.card}>
              <View style={styles.settingItem_2}>
                <Ionicons name="trash-outline" size={moderateScale(20)} color={COLORS.textColor} />
                <Text style={styles.settingText}>Clear analysis history</Text>
                <TouchableOpacity
                  onPress={handleClearHistory}
                  disabled={!hasHistory}
                  activeOpacity={0.7}
                >
                  <View style={styles.clearButton}>
                    <Text style={[
                      styles.clearButtonText,
                      !hasHistory && styles.clearButtonTextDisabled
                    ]}>
                      Clear
                    </Text>
                  </View>
                </TouchableOpacity>
              </View>
              <View style={styles.divider} />
              <View style={styles.settingItem_2}>
                <Ionicons name="folder-outline" size={moderateScale(20)} color={COLORS.textColor} />
                <Text style={styles.settingText}>Clear cache / Temporary files</Text>
                <TouchableOpacity
                  onPress={handleClearCache}
                  disabled={!hasCache}
                  activeOpacity={0.7}
                >
                  <View style={styles.clearButton}>
                    <Text style={[
                      styles.clearButtonText,
                      !hasCache && styles.clearButtonTextDisabled
                    ]}>
                      Clear
                    </Text>
                  </View>
                </TouchableOpacity>
              </View>
            </View>
          </View>

          {/* System Info Section */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>System Info</Text>
            <View style={styles.card}>
              <TouchableOpacity
                style={styles.settingItem_2}
                onPress={handleAboutApp}
                activeOpacity={0.7}
              >
                <Ionicons name="information-circle-outline" size={moderateScale(20)} color={COLORS.textColor} />
                <Text style={styles.settingText}>About Application</Text>
                <Ionicons name="chevron-forward" size={moderateScale(24)} color={COLORS.textColor} />
              </TouchableOpacity>
              <View style={styles.divider} />
              <TouchableOpacity
                style={styles.settingItem_2}
                onPress={handleHelpFAQ}
                activeOpacity={0.7}
              >
                <Ionicons name="help-circle-outline" size={moderateScale(20)} color={COLORS.textColor} />
                <Text style={styles.settingText}>Help / FAQ</Text>
                <Ionicons name="chevron-forward" size={moderateScale(24)} color={COLORS.textColor} />
              </TouchableOpacity>
              <View style={styles.divider} />
              <TouchableOpacity
                style={styles.settingItem_2}
                onPress={handleDeleteAccount}
                activeOpacity={0.7}
              >
                <Ionicons name="trash-outline" size={moderateScale(20)} color="#E63946" />
                <Text style={[styles.settingText, styles.deleteText]}>Delete my account</Text>
                <Ionicons name="chevron-forward" size={moderateScale(24)} color="#E63946" />
              </TouchableOpacity>
            </View>
          </View>
        </ScrollView>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: COLORS.screenBackground,
  },

  container: {
      flex: 1,
      paddingTop: verticalScale(35),
    },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: scale(16),
    paddingTop: Platform.OS === 'ios' ? verticalScale(50) : verticalScale(20),
    paddingBottom: verticalScale(16),
  },

  backButton: {
    width: moderateScale(32),
    height: moderateScale(32),
    justifyContent: 'center',
    alignItems: 'center',
  },

  headerTitle: {
    fontSize: moderateScale(20),
    fontFamily: 'Nunito-Bold',
    color: COLORS.textColor,
    position: 'absolute',
    left: 0,
    right: 0,
    textAlign: 'center',
  },

  scrollView: {
    flex: 1,
  },

  scrollContent: {
    paddingHorizontal: scale(16),
    paddingBottom: verticalScale(100),
  },

  profileSection: {
    alignItems: 'center',
    marginTop: verticalScale(20),
    marginBottom: verticalScale(32),
  },

  avatarContainer: {
    width: moderateScale(80),
    height: moderateScale(80),
    borderRadius: moderateScale(40),
    backgroundColor: COLORS.white,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: verticalScale(7),
  },

  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: scale(4),
    marginBottom: verticalScale(2),
  },

  userName: {
    fontSize: moderateScale(18),
    fontFamily: 'Nunito-Medium',
    color: COLORS.textColor,
    letterSpacing: 0.1,
  },

  userEmail: {
    fontSize: moderateScale(14),
    fontFamily: 'Nunito-Light',
    color: COLORS.textColor,
    marginBottom: verticalScale(2),
  },

  changePasswordButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: scale(4),
  },

  changePasswordText: {
    fontSize: moderateScale(12),
    fontFamily: 'Nunito-Medium',
    color: COLORS.redColor,
  },

  section: {
    marginBottom: verticalScale(24),
  },

  sectionTitle: {
    fontSize: moderateScale(14),
    fontFamily: 'Nunito-SemiBold',
    color: COLORS.textColor,
    marginBottom: verticalScale(8),
    letterSpacing: 0.16,
    paddingHorizontal: scale(4),
  },

  card: {
    backgroundColor: COLORS.white,
    borderRadius: moderateScale(10),
    borderWidth: 0.3,
    borderColor: COLORS.borderColor,
  },


  settingItem_1: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: scale(16),
    gap: scale(6),
    minHeight: verticalScale(48),
    justifyContent: 'space-between',
  },

  settingItem_2: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: verticalScale(12),
    paddingHorizontal: scale(16),
    gap: scale(6),
    minHeight: verticalScale(48),
    justifyContent: 'space-between',
  },

  settingText: {
    flex: 1,
    fontSize: moderateScale(14),
    fontFamily: 'Nunito-Light',
    color: COLORS.textColor,
  },

  deleteText: {
    color: COLORS.redColor,
  },

  divider: {
    height: 0.8,
    backgroundColor: COLORS.borderColor,

  },

  clearButton: {
    backgroundColor: COLORS.settingsClearBg,
    paddingHorizontal: scale(16),
    paddingVertical: verticalScale(4),
    borderRadius: moderateScale(4),
    minWidth: scale(60),
    alignItems: 'center',
  },

  clearButtonText: {
    fontSize: moderateScale(14),
    fontFamily: 'Nunito-Light',
    color: COLORS.textColor,
  },

  clearButtonTextDisabled: {
    color: COLORS.borderColor,
    fontFamily: 'Nunito-ExtraLight',
  },

  switch: {
    transform: Platform.OS === 'ios' 
      ? [{ scaleX: moderateScale(0.8, 0.3) }, { scaleY: moderateScale(0.8, 0.3) }] 
      : [{ scaleX: 1 }, { scaleY: 1 }],
      paddingVertical: 2,
  },
});

export default Settings;