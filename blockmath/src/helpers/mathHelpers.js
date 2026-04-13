/**
 * Math question generator for BlockMath.
 * Fixed: no infinite loops, distinct level logic, answers always >= 1.
 */

export function generateMathQuestion(level) {
  let num1, num2, operation;

  switch (level) {
    case 1: // Addition only, sum <= 5
      operation = '+';
      num1 = Math.floor(Math.random() * 4) + 1; // 1-4
      num2 = Math.floor(Math.random() * (5 - num1)) + 1; // ensures sum <= 5
      break;

    case 2: // Addition only, sum <= 10
      operation = '+';
      num1 = Math.floor(Math.random() * 8) + 1; // 1-8
      num2 = Math.floor(Math.random() * (10 - num1)) + 1; // ensures sum <= 10
      break;

    case 3: // Subtraction only, result >= 1
      operation = '-';
      num1 = Math.floor(Math.random() * 8) + 2; // 2-9
      num2 = Math.floor(Math.random() * (num1 - 1)) + 1; // 1 to (num1-1), ensures result >= 1
      break;

    case 4: // Mixed addition and subtraction
      operation = Math.random() > 0.5 ? '+' : '-';
      if (operation === '+') {
        num1 = Math.floor(Math.random() * 7) + 1; // 1-7
        num2 = Math.floor(Math.random() * (10 - num1)) + 1; // ensures sum <= 10
      } else {
        num1 = Math.floor(Math.random() * 8) + 2; // 2-9
        num2 = Math.floor(Math.random() * (num1 - 1)) + 1; // ensures result >= 1
      }
      break;

    default:
      operation = '+';
      num1 = 1;
      num2 = 1;
  }

  const correctAnswer = operation === '+' ? num1 + num2 : num1 - num2;

  // Generate wrong answers from a safe candidate pool (NO infinite loop)
  const candidates = [];
  for (let offset = -3; offset <= 3; offset++) {
    if (offset === 0) continue;
    const val = correctAnswer + offset;
    if (val >= 1 && val <= 15) {
      candidates.push(val);
    }
  }

  // Fisher-Yates shuffle for candidates
  for (let i = candidates.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
  }

  // Pick 2 wrong answers
  const wrongAnswers = candidates.slice(0, 2);

  // Fallback (shouldn't be needed, but prevents any edge case)
  let fallback = correctAnswer + 1;
  while (wrongAnswers.length < 2) {
    if (fallback !== correctAnswer && !wrongAnswers.includes(fallback)) {
      wrongAnswers.push(fallback);
    }
    fallback++;
  }

  // Combine and shuffle all answers
  const allAnswers = [correctAnswer, ...wrongAnswers];
  for (let i = allAnswers.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [allAnswers[i], allAnswers[j]] = [allAnswers[j], allAnswers[i]];
  }

  return {
    num1,
    num2,
    operation,
    correctAnswer,
    answers: allAnswers,
    correctIndex: allAnswers.indexOf(correctAnswer),
  };
}

export function getLevelInfo(level) {
  const configs = {
    1: { title: 'Tiny Blocks', subtitle: 'Add up to 5', color: '#FF6B6B', emoji: '\u{1F534}' },
    2: { title: 'Big Blocks', subtitle: 'Add up to 10', color: '#FFB020', emoji: '\u{1F7E0}' },
    3: { title: 'Take Away', subtitle: 'Simple subtraction', color: '#4ECDC4', emoji: '\u{1F7E2}' },
    4: { title: 'Block Party', subtitle: 'Mix it up!', color: '#7C4DFF', emoji: '\u{1F7E3}' },
  };
  return configs[level] || configs[1];
}
