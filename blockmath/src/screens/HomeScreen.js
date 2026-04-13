import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { MaterialIcons } from '@expo/vector-icons';
import { getLevelInfo } from '../helpers/mathHelpers';
import { getProgress } from '../helpers/storage';

export default function HomeScreen({ navigation }) {
  const insets = useSafeAreaInsets();
  const [totalStars, setTotalStars] = useState(0);

  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      getProgress().then(p => setTotalStars(p.totalStars || 0));
    });
    return unsubscribe;
  }, [navigation]);

  return (
    <ScrollView
      style={styles.scrollView}
      contentContainerStyle={{ paddingTop: insets.top + 10, paddingBottom: 40 }}
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>BlockMath</Text>
        <Text style={styles.subtitle}>Learn maths with Numberblocks!</Text>
        <View style={styles.starBadge}>
          <MaterialIcons name="star" size={22} color="#F59E0B" />
          <Text style={styles.starText}>{totalStars}</Text>
        </View>
      </View>

      {/* Level buttons */}
      <View style={styles.levelContainer}>
        <Text style={styles.sectionTitle}>Choose a Level</Text>
        {[1, 2, 3, 4].map(lvl => {
          const info = getLevelInfo(lvl);
          return (
            <TouchableOpacity
              key={lvl}
              style={[styles.levelBtn, { backgroundColor: info.color }]}
              onPress={() => navigation.navigate('Game', { selectedLevel: lvl })}
              activeOpacity={0.8}
            >
              <View style={styles.levelBtnContent}>
                <Text style={styles.levelEmoji}>{info.emoji}</Text>
                <View style={styles.levelTextWrap}>
                  <Text style={styles.levelTitle}>Level {lvl}: {info.title}</Text>
                  <Text style={styles.levelSub}>{info.subtitle}</Text>
                </View>
                <MaterialIcons name="play-circle-filled" size={36} color="rgba(255,255,255,0.9)" />
              </View>
            </TouchableOpacity>
          );
        })}
      </View>
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
    paddingVertical: 20,
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 42,
    fontWeight: 'bold',
    color: '#FF6B6B',
  },
  subtitle: {
    fontSize: 16,
    color: '#718096',
    fontWeight: '600',
    marginTop: 4,
  },
  starBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginTop: 12,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  starText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#F59E0B',
    marginLeft: 6,
  },
  levelContainer: {
    paddingHorizontal: 20,
    marginTop: 10,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2D3748',
    marginBottom: 12,
  },
  levelBtn: {
    borderRadius: 20,
    marginBottom: 14,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
  },
  levelBtnContent: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 18,
  },
  levelEmoji: {
    fontSize: 32,
    marginRight: 14,
  },
  levelTextWrap: {
    flex: 1,
  },
  levelTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFF',
  },
  levelSub: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.85)',
    marginTop: 2,
  },
});
