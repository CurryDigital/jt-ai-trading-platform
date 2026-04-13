import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  Animated,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { MaterialIcons } from '@expo/vector-icons';
import BlockCharacter from '../components/BlockCharacter';
import { generateMathQuestion, getLevelInfo } from '../helpers/mathHelpers';
import { getProgress, updateProgress } from '../helpers/storage';

export default function GameScreen({ route, navigation }) {
  const { selectedLevel = 1 } = route.params || {};
  const insets = useSafeAreaInsets();
  const levelInfo = getLevelInfo(selectedLevel);

  const [question, setQuestion] = useState(null);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [isCorrect, setIsCorrect] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);
  const [wrongAttempts, setWrongAttempts] = useState(0);
  const [disabledAnswers, setDisabledAnswers] = useState([]);
  const [streak, setStreak] = useState(0);
  const [stars, setStars] = useState(0);
  const [showCorrectHint, setShowCorrectHint] = useState(false);

  const scaleAnim = useRef(new Animated.Value(1)).current;
  const shakeAnim = useRef(new Animated.Value(0)).current;

  const newQuestion = useCallback(() => {
    setQuestion(generateMathQuestion(selectedLevel));
    setSelectedAnswer(null);
    setIsCorrect(false);
    setShowCelebration(false);
    setWrongAttempts(0);
    setDisabledAnswers([]);
    setShowCorrectHint(false);

    // Bounce-in animation for new question
    scaleAnim.setValue(0.8);
    Animated.spring(scaleAnim, {
      toValue: 1,
      friction: 4,
      tension: 100,
      useNativeDriver: Platform.OS !== 'web',
    }).start();
  }, [selectedLevel, scaleAnim]);

  useEffect(() => {
    newQuestion();
    getProgress().then(p => setStars(p.totalStars || 0));
  }, [newQuestion]);

  const handleAnswer = (index) => {
    if (isCorrect || disabledAnswers.includes(index)) return;

    const correct = index === question.correctIndex;
    setSelectedAnswer(index);

    if (correct) {
      setIsCorrect(true);
      setStreak(s => s + 1);

      // Save progress — only award star on first-try correct
      getProgress().then(p => {
        const earnedStar = wrongAttempts === 0;
        const newStars = (p.totalStars || 0) + (earnedStar ? 1 : 0);
        updateProgress({
          totalStars: newStars,
          [`lvl${selectedLevel}_right`]: (p[`lvl${selectedLevel}_right`] || 0) + 1,
          [`lvl${selectedLevel}_total`]: (p[`lvl${selectedLevel}_total`] || 0) + wrongAttempts + 1,
        });
        setStars(newStars);
      });

      setTimeout(() => setShowCelebration(true), 600);
    } else {
      const newWrongAttempts = wrongAttempts + 1;
      setWrongAttempts(newWrongAttempts);
      setDisabledAnswers(prev => [...prev, index]);
      setStreak(0);

      // Shake animation
      Animated.sequence([
        Animated.timing(shakeAnim, { toValue: 10, duration: 50, useNativeDriver: Platform.OS !== 'web' }),
        Animated.timing(shakeAnim, { toValue: -10, duration: 50, useNativeDriver: Platform.OS !== 'web' }),
        Animated.timing(shakeAnim, { toValue: 10, duration: 50, useNativeDriver: Platform.OS !== 'web' }),
        Animated.timing(shakeAnim, { toValue: 0, duration: 50, useNativeDriver: Platform.OS !== 'web' }),
      ]).start();

      // After 2 wrong attempts, reveal the correct answer then auto-advance
      if (newWrongAttempts >= 2) {
        setTimeout(() => {
          setShowCorrectHint(true);
          setSelectedAnswer(question.correctIndex);
          setIsCorrect(true);

          // Record attempts in progress
          getProgress().then(p => {
            updateProgress({
              [`lvl${selectedLevel}_total`]: (p[`lvl${selectedLevel}_total`] || 0) + newWrongAttempts,
            });
          });

          // Auto-advance after showing the answer
          setTimeout(() => newQuestion(), 1800);
        }, 600);
      } else {
        // Clear wrong selection so they can try again
        setTimeout(() => setSelectedAnswer(null), 400);
      }
    }
  };

  if (!question) return null;

  const getButtonStyle = (index) => {
    if (disabledAnswers.includes(index)) {
      return { backgroundColor: '#FED7D7', borderColor: '#FEB2B2' };
    }
    if (showCorrectHint && index === question.correctIndex) {
      return { backgroundColor: '#10B981', borderColor: '#059669' };
    }
    if (selectedAnswer === index) {
      if (isCorrect && index === question.correctIndex) {
        return { backgroundColor: '#10B981', borderColor: '#059669' };
      }
      return { backgroundColor: '#EF4444', borderColor: '#DC2626' };
    }
    return { backgroundColor: '#FFF', borderColor: '#E2E8F0' };
  };

  const getTextColor = (index) => {
    if (disabledAnswers.includes(index)) return '#FCA5A5';
    if (showCorrectHint && index === question.correctIndex) return '#FFF';
    if (selectedAnswer === index) return '#FFF';
    return '#2D3748';
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <MaterialIcons name="arrow-back" size={28} color={levelInfo.color} />
        </TouchableOpacity>
        <Text style={[styles.levelTitle, { color: levelInfo.color }]} numberOfLines={1}>
          Lv{selectedLevel}: {levelInfo.title}
        </Text>
        <View style={styles.starCounter}>
          <MaterialIcons name="star" size={16} color="#F59E0B" />
          <Text style={styles.starCountText}>{stars}</Text>
        </View>
      </View>

      {/* Streak banner */}
      {streak >= 2 && (
        <View style={styles.streakBanner}>
          <Text style={styles.streakText}>{streak} in a row!</Text>
        </View>
      )}

      {/* Question area with block characters */}
      <Animated.View style={[styles.questionArea, { transform: [{ scale: scaleAnim }] }]}>
        <View style={styles.equation}>
          <BlockCharacter number={question.num1} size="medium" />
          <Text style={styles.operator}>{question.operation}</Text>
          <BlockCharacter number={question.num2} size="medium" />
          <Text style={styles.operator}>=</Text>
          <Text style={styles.questionMark}>?</Text>
        </View>
      </Animated.View>

      {/* Answer buttons */}
      <Animated.View style={[styles.answersArea, { transform: [{ translateX: shakeAnim }] }]}>
        {question.answers.map((ans, i) => (
          <TouchableOpacity
            key={`${question.num1}-${question.operation}-${question.num2}-${i}`}
            style={[styles.answerBtn, getButtonStyle(i)]}
            onPress={() => handleAnswer(i)}
            activeOpacity={0.7}
            disabled={disabledAnswers.includes(i) || isCorrect}
          >
            <Text style={[styles.answerText, { color: getTextColor(i) }]}>{ans}</Text>
          </TouchableOpacity>
        ))}
      </Animated.View>

      {/* Hint after first wrong */}
      {wrongAttempts === 1 && !isCorrect && (
        <Text style={styles.hintText}>Try again! You can do it!</Text>
      )}

      {/* Celebration modal */}
      <Modal visible={showCelebration} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.celebrationEmoji}>
              {wrongAttempts === 0 ? '\u{1F31F}' : '\u{1F44D}'}
            </Text>
            <Text style={styles.celebrationTitle}>
              {wrongAttempts === 0 ? 'Perfect!' : 'Well Done!'}
            </Text>
            <Text style={styles.celebrationSub}>
              {question.num1} {question.operation} {question.num2} = {question.correctAnswer}
            </Text>
            {wrongAttempts === 0 && (
              <Text style={styles.starEarned}>+1 Star!</Text>
            )}
            <TouchableOpacity
              style={[styles.nextBtn, { backgroundColor: levelInfo.color }]}
              onPress={newQuestion}
              activeOpacity={0.8}
            >
              <Text style={styles.nextBtnText}>Next Question</Text>
              <MaterialIcons name="arrow-forward" size={22} color="#FFF" />
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFF3E0',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  backBtn: {
    padding: 4,
  },
  levelTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginLeft: 8,
    flex: 1,
  },
  starCounter: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF',
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 4,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  starCountText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#F59E0B',
    marginLeft: 4,
  },
  streakBanner: {
    alignItems: 'center',
    paddingVertical: 6,
  },
  streakText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FF6B6B',
  },
  questionArea: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: 180,
  },
  equation: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    flexWrap: 'wrap',
    paddingHorizontal: 10,
  },
  operator: {
    fontSize: 38,
    fontWeight: 'bold',
    color: '#2D3748',
    marginHorizontal: 6,
  },
  questionMark: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#FF6B6B',
  },
  answersArea: {
    paddingHorizontal: 20,
    paddingBottom: 24,
  },
  answerBtn: {
    padding: 16,
    borderRadius: 16,
    marginBottom: 10,
    alignItems: 'center',
    borderWidth: 2,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
  },
  answerText: {
    fontSize: 28,
    fontWeight: 'bold',
  },
  hintText: {
    textAlign: 'center',
    fontSize: 16,
    color: '#FF6B6B',
    fontWeight: '600',
    paddingBottom: 12,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    width: '80%',
    backgroundColor: '#FFF',
    borderRadius: 24,
    padding: 30,
    alignItems: 'center',
    elevation: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 10,
  },
  celebrationEmoji: {
    fontSize: 60,
  },
  celebrationTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#2D3748',
    marginTop: 10,
  },
  celebrationSub: {
    fontSize: 20,
    color: '#718096',
    marginTop: 8,
  },
  starEarned: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#F59E0B',
    marginTop: 8,
  },
  nextBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 24,
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 16,
    width: '100%',
  },
  nextBtnText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFF',
    marginRight: 8,
  },
});
