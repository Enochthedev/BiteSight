import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface SettingsContextType {
  saveToHistory: boolean;
  setSaveToHistory: (value: boolean) => void;
  autoTagMealTime: boolean;
  setAutoTagMealTime: (value: boolean) => void;
  isLoading: boolean;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

const STORAGE_KEYS = {
  SAVE_TO_HISTORY: '@settings_save_to_history',
  AUTO_TAG_MEAL_TIME: '@settings_auto_tag_meal_time',
};

export const SettingsProvider = ({ children }: { children: ReactNode }) => {
  const [saveToHistory, setSaveToHistoryState] = useState(true);
  const [autoTagMealTime, setAutoTagMealTimeState] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Load settings from AsyncStorage on mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const [savedSaveToHistory, savedAutoTagMealTime] = await Promise.all([
        AsyncStorage.getItem(STORAGE_KEYS.SAVE_TO_HISTORY),
        AsyncStorage.getItem(STORAGE_KEYS.AUTO_TAG_MEAL_TIME),
      ]);

      if (savedSaveToHistory !== null) {
        setSaveToHistoryState(JSON.parse(savedSaveToHistory));
      }
      if (savedAutoTagMealTime !== null) {
        setAutoTagMealTimeState(JSON.parse(savedAutoTagMealTime));
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const setSaveToHistory = async (value: boolean) => {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.SAVE_TO_HISTORY, JSON.stringify(value));
      setSaveToHistoryState(value);
    } catch (error) {
      console.error('Error saving saveToHistory setting:', error);
    }
  };

  const setAutoTagMealTime = async (value: boolean) => {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.AUTO_TAG_MEAL_TIME, JSON.stringify(value));
      setAutoTagMealTimeState(value);
    } catch (error) {
      console.error('Error saving autoTagMealTime setting:', error);
    }
  };

  return (
    <SettingsContext.Provider
      value={{
        saveToHistory,
        setSaveToHistory,
        autoTagMealTime,
        setAutoTagMealTime,
        isLoading,
      }}
    >
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};