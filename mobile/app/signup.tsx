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

export default function SignUpScreen() {  
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleSignUp = async () => {
    // Basic validation still active
    if (!fullName || !email || !password || !confirmPassword) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }
    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }

    // AUTHENTICATION LOGIC TO BE IMPLEMENTED
    try {
      await AsyncStorage.setItem('hasAccount', 'true');
      await AsyncStorage.setItem('userEmail', email);
      await AsyncStorage.setItem('userName', fullName);
      
      // Navigate to auth splash screen
      router.replace('/auth-splash');
    } catch (error) {
      console.error('Error saving user data:', error);
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
        <View style={{ alignItems: 'center', marginTop: normalizeVertical(10) }}>
          <DiamondGradient size={38}>PlateLensAI</DiamondGradient>
        </View>
        <Text style={{ 
          fontSize: moderateScale(16), 
          fontFamily: 'Nunito-Light', 
          color: COLORS.textColor, 
          textAlign: 'center', 
          marginBottom: normalizeVertical(40), 
          marginTop: normalizeVertical(-15) 
        }}>
          Let's get you started!
        </Text>
        <View style={{ width: '100%' }}>
          <View style={{ marginBottom: normalizeVertical(15) }}>
            <Text style={{ 
              fontSize: moderateScale(14), 
              fontFamily: 'Nunito-Regular', 
              color: COLORS.textColor, 
              marginBottom: normalizeVertical(5) 
            }}>
              Full Name
            </Text>
            <CustomTextInput 
              value={fullName} 
              onChangeText={setFullName} 
              placeholder="Your name here..." 
              autoCapitalize="words" 
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
              Create Password
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
          <View style={{ marginBottom: normalizeVertical(15) }}>
            <Text style={{ 
              fontSize: moderateScale(14), 
              fontFamily: 'Nunito-Regular', 
              color: COLORS.textColor, 
              marginBottom: normalizeVertical(5) 
            }}>
              Confirm Password
            </Text>
            <CustomTextInput 
              value={confirmPassword} 
              onChangeText={setConfirmPassword} 
              placeholder="Re-enter your password..." 
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
            onPress={handleSignUp} 
            style={{ 
              backgroundColor: COLORS.buttonColor, 
              paddingVertical: normalizeVertical(10), 
              borderRadius: normalize(10), 
              alignItems: 'center', 
              justifyContent: 'center', 
              marginTop: normalizeVertical(20), 
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
            title="Sign up" 
          />
          <TouchableOpacity onPress={() => router.push('/login')}>
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
                Already have an account?
              </Text>
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}