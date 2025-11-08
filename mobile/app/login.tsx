import React, { useState } from 'react';
import { 
  View, 
  Text, 
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
  TextInput,
  TouchableOpacity,
  Dimensions,
  PixelRatio,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import AnimatedButton from '../src/components/AnimatedButton';
import COLORS from '../src/styles/colors';
import DiamondGradient from "../src/components/DiamondGradient";
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

const scale = SCREEN_WIDTH / 375;
const verticalScale = SCREEN_HEIGHT / 812;

const normalize = (size: number) => {
  const newSize = size * scale;
  return Math.round(PixelRatio.roundToNearestPixel(newSize));
};

const normalizeVertical = (size: number) => {
  const newSize = size * verticalScale;
  return Math.round(PixelRatio.roundToNearestPixel(newSize));
};

const moderateScale = (size: number, factor = 0.5) => {
  return size + (normalize(size) - size) * factor;
};

interface CustomTextInputProps {
  value: string;
  onChangeText: (text: string) => void;
  placeholder: string;
  secureTextEntry?: boolean;
  keyboardType?: any;
  autoCapitalize?: 'none' | 'sentences' | 'words' | 'characters';
  style?: any;
}

function CustomTextInput({
  value,
  onChangeText,
  placeholder,
  secureTextEntry = false,
  keyboardType = 'default',
  autoCapitalize = 'none',
  style,
}: CustomTextInputProps) {
  return (
    <TextInput
      value={value}
      onChangeText={onChangeText}
      placeholder={placeholder}
      placeholderTextColor="#999999"
      secureTextEntry={secureTextEntry}
      keyboardType={keyboardType}
      autoCapitalize={autoCapitalize}
      style={[style, { fontFamily: 'Nunito-Regular' }]}
    />
  );
}

export default function LoginScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');


  // Email validation function
  const validateEmail = (email: string): boolean => {
  // Strong email format validation
  const trimmedEmail = email.trim();
  
  // Check basic email pattern with strict ending
  const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
  if (!emailRegex.test(trimmedEmail)) {
    return false;
  }
  
  // Split by @ to validate parts
  const parts = trimmedEmail.split('@');
  if (parts.length !== 2) return false;
  
  const localPart = parts[0];
  const domainPart = parts[1];
  
  // Local part (before @) must be at least 1 character and only valid characters
  if (localPart.length < 1 || !/^[a-zA-Z0-9._-]+$/.test(localPart)) {
    return false;
  }
  
  // Split domain by . to check extension
  const domainParts = domainPart.split('.');
  if (domainParts.length < 2) return false;
  
  // Check each domain part is valid
  for (const part of domainParts) {
    if (part.length < 1 || !/^[a-zA-Z0-9-]+$/.test(part)) {
      return false;
    }
  }
  
  // Check that the last part (extension) only contains letters and is 2-6 chars
  const extension = domainParts[domainParts.length - 1];
  if (!/^[a-zA-Z]{2,6}$/.test(extension)) {
    return false;
  }
  
  // Final check: make sure the email ends exactly with the extension (no extra chars)
  if (!trimmedEmail.endsWith('.' + extension)) {
    return false;
  }
  
  return true;
};

  //Password validation function
  const validatePassword = (password: string): boolean => {
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
    return passwordRegex.test(password);
};

const handleLogin = async () => {
if (!email || !password) {
  Alert.alert('Error', 'Please fill in all fields');
  return;
}

// ADDED: Email validation
if (!validateEmail(email)) {
  Alert.alert('Invalid Email', 'Please enter a valid email address');
  return;
}

// ADDED: Password format validation
if (!validatePassword(password)) {
  Alert.alert(
    'Invalid Password Format', 
    'Password must be at least 8 characters long and include:\n• At least one uppercase letter\n• At least one lowercase letter\n• At least one number\n• At least one special character (@$!%*?&)'
  );
  return;
}

  try {
    const storedEmail = await AsyncStorage.getItem('userEmail');
    const storedPassword = await AsyncStorage.getItem('userPassword'); // ADDED
    
    // UPDATED: Check both email AND password
    if (storedEmail === email && storedPassword === password) {
      router.replace('/auth-splash');
    } else {
      Alert.alert('Error', 'Invalid credentials');
    }
  } catch (error) {
    console.error('Error during login:', error);
    Alert.alert('Error', 'Something went wrong. Please try again.');
  }
};


  return (
    <KeyboardAvoidingView 
      style={{ flex: 1, backgroundColor: COLORS.screenBackground }} 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView 
        contentContainerStyle={{ 
          flexGrow: 1, 
          paddingTop: insets.top + normalizeVertical(60), 
          paddingHorizontal: normalize(30), 
          paddingBottom: insets.bottom + normalizeVertical(30) 
        }} 
        showsVerticalScrollIndicator={false} 
        keyboardShouldPersistTaps="handled"
      >
        <View style={{ alignItems: 'center', marginTop: normalizeVertical(20) }}>
          <DiamondGradient size={36}>PlateLensAI</DiamondGradient>
        </View>
        <Text style={{ 
          fontSize: moderateScale(16), 
          fontFamily: 'Nunito-Light', 
          color: COLORS.textColor, 
          textAlign: 'center', 
          marginBottom: normalizeVertical(40), 
          marginTop: normalizeVertical(-15) 
        }}>
          Let's pick up where you left off!
        </Text>
        <View style={{ width: '100%' }}>
          <View style={{ marginBottom: normalizeVertical(15) }}>
            <Text style={{ 
              fontSize: moderateScale(14), 
              fontFamily: 'Nunito-Regular', 
              color: COLORS.textColor, 
              marginBottom: normalizeVertical(5) 
            }}>
              Email
            </Text>
            <CustomTextInput 
              value={email} 
              onChangeText={setEmail} 
              placeholder="you@example.com" 
              keyboardType="email-address" 
              autoCapitalize="none" 
              style={{ 
                backgroundColor: COLORS.white, 
                borderWidth: 1, 
                borderColor: '#B7C6D1', 
                borderRadius: normalize(10), 
                paddingVertical: normalizeVertical(12), 
                paddingHorizontal: normalize(15), 
                fontSize: moderateScale(14), 
                color: COLORS.textColor, 
                lineHeight: moderateScale(14) * 1.7 
              }} 
            />
          </View>
          <View style={{ marginBottom: normalizeVertical(15) }}>
            <Text style={{ 
              fontSize: moderateScale(14), 
              fontFamily: 'Nunito-Regular', 
              color: COLORS.textColor, 
              marginBottom: normalizeVertical(5) 
            }}>
              Password
            </Text>
            <CustomTextInput 
              value={password} 
              onChangeText={setPassword} 
              placeholder="Enter your password..." 
              secureTextEntry 
              style={{ 
                backgroundColor: COLORS.white, 
                borderWidth: 1, 
                borderColor: '#B7C6D1', 
                borderRadius: normalize(10), 
                paddingVertical: normalizeVertical(12), 
                paddingHorizontal: normalize(15), 
                fontSize: moderateScale(14), 
                color: COLORS.textColor, 
                lineHeight: moderateScale(14) * 1.7 
              }} 
            />
          </View>

          <AnimatedButton 
            onPress={handleLogin} 
            style={{ 
              backgroundColor: COLORS.buttonColor, 
              paddingVertical: normalizeVertical(10), 
              borderRadius: normalize(10), 
              alignItems: 'center', 
              justifyContent: 'center', 
              marginTop: normalizeVertical(30), 
              shadowColor: COLORS.secondaryColor, 
              shadowOffset: { width: 0, height: 2 }, 
              shadowOpacity: 0.2, 
              shadowRadius: 6, 
              elevation: 3 
            }} 
            textStyle={{ 
              fontSize: moderateScale(18), 
              fontFamily: 'Nunito-Medium', 
              color: COLORS.white 
            }} 
            title="Login" 
          />

          <TouchableOpacity onPress={() => router.push('/signup')}>
            <Text style={{ 
              fontSize: moderateScale(14), 
              color: COLORS.textColor, 
              textAlign: 'center', 
              marginTop: normalizeVertical(5) 
            }}>
              <Text style={{ 
                fontFamily: 'Nunito-Light', 
                textDecorationLine: 'underline' 
              }}>
                Don't have an account?
              </Text>
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}