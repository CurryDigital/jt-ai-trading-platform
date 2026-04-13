import AsyncStorage from '@react-native-async-storage/async-storage';

const KEY = '@blockmath_progress';

const DEFAULT_PROGRESS = {
  totalStars: 0,
  lvl1_right: 0,
  lvl1_total: 0,
  lvl2_right: 0,
  lvl2_total: 0,
  lvl3_right: 0,
  lvl3_total: 0,
  lvl4_right: 0,
  lvl4_total: 0,
};

export async function getProgress() {
  try {
    const json = await AsyncStorage.getItem(KEY);
    return json ? { ...DEFAULT_PROGRESS, ...JSON.parse(json) } : { ...DEFAULT_PROGRESS };
  } catch {
    return { ...DEFAULT_PROGRESS };
  }
}

export async function updateProgress(updates) {
  try {
    const current = await getProgress();
    const updated = { ...current, ...updates };
    await AsyncStorage.setItem(KEY, JSON.stringify(updated));
    return updated;
  } catch (e) {
    console.warn('Failed to save progress:', e);
    return null;
  }
}

export async function resetProgress() {
  try {
    await AsyncStorage.setItem(KEY, JSON.stringify(DEFAULT_PROGRESS));
    return { ...DEFAULT_PROGRESS };
  } catch (e) {
    console.warn('Failed to reset progress:', e);
    return null;
  }
}
