import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { MaterialIcons } from '@expo/vector-icons';
import { getLevelInfo } from '../helpers/mathHelpers';
import { getProgress, resetProgress } from '../helpers/storage';

export default function ProgressScreen({ navigation }) {
  const insets = useSafeAreaInsets();
  const [progress, setProgress] = useState({});

  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      getProgress().then(p => setProgress(p));
    });
    return unsubscribe;
  }, [navigation]);

  const handleReset = () => {
    resetProgress().then(p => setProgress(p));
  };

  return (
    <ScrollView
      style={styles.scrollView}
      contentContainerStyle={{ paddingTop: insets.top + 10, paddingBottom: 40 }}
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>My Stars</Text>
        <View style={styles.totalStarsBadge}>
          <MaterialIcons name="star" size={32} color="#F59E0B" />
          <Text style={styles.totalStarsNum}>{progress.totalStars || 0}</Text>
        </View>
        <Text style={styles.totalStarsLabel}>Total Stars Earned</Text>
      </View>

      {/* Level progress cards */}
      {[1, 2, 3, 4].map(lvl => {
        const info = getLevelInfo(lvl);
        const right = progress[`lvl${lvl}_right`] || 0;
        const total = progress[`lvl${lvl}_total`] || 0;
        const accuracy = total > 0 ? Math.round((right / total) * 100) : 0;

        return (
          <View key={lvl} style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardEmoji}>{info.emoji}</Text>
              <Text style={styles.cardTitle}>Level {lvl}: {info.title}</Text>
            </View>
            <View style={styles.statsRow}>
              <Text style={styles.statLabel}>Solved: {right}</Text>
              <Text style={[styles.statValue, { color: info.color }]}>
                {accuracy}% Accuracy
              </Text>
            </View>
            <View style={styles.progressBg}>
              <View
                style={[
                  styles.progressFill,
                  { width: `${accuracy}%`, backgroundColor: info.color },
                ]}
              />
            </View>
            {total === 0 && (
              <Text style={styles.notStarted}>Not started yet - go play!</Text>
            )}
          </View>
        );
      })}

      {/* Reset button */}
      <TouchableOpacity style={styles.resetBtn} onPress={handleReset} activeOpacity={0.7}>
        <MaterialIcons name="refresh" size={18} color="#A0AEC0" />
        <Text style={styles.resetText}>Reset Progress</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scrollView: {
    flex: 1,
    backgroundColor: '#FFF3E0',
  },
  header: {
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FF6B6B',
  },
  totalStarsBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF',
    borderRadius: 24,
    paddingHorizontal: 24,
    paddingVertical: 14,
    marginTop: 12,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  totalStarsNum: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#F59E0B',
    marginLeft: 10,
  },
  totalStarsLabel: {
    fontSize: 14,
    color: '#718096',
    fontWeight: '600',
    marginTop: 6,
  },
  card: {
    backgroundColor: '#FFF',
    marginHorizontal: 20,
    marginTop: 14,
    padding: 16,
    borderRadius: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  cardEmoji: {
    fontSize: 22,
    marginRight: 8,
  },
  cardTitle: {
    fontSize: 17,
    fontWeight: 'bold',
    color: '#2D3748',
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  statLabel: {
    fontSize: 13,
    color: '#718096',
    fontWeight: '600',
  },
  statValue: {
    fontSize: 13,
    fontWeight: 'bold',
  },
  progressBg: {
    height: 10,
    backgroundColor: '#E5E7EB',
    borderRadius: 5,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 5,
  },
  notStarted: {
    fontSize: 12,
    color: '#A0AEC0',
    fontStyle: 'italic',
    marginTop: 6,
  },
  resetBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 24,
    padding: 12,
  },
  resetText: {
    fontSize: 14,
    color: '#A0AEC0',
    marginLeft: 6,
  },
});
