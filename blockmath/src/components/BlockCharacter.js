import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

/**
 * Numberblocks-style character: colored blocks stacked with eyes on the top block.
 * Arrangement matches the show:
 * - 1-3: single column
 * - 4: 2x2 square
 * - 5: 3 bottom + 2 top
 * - 6: 3x2
 * - 7: 4 bottom + 3 top
 * - 8: 4x2
 * - 9: 3x3
 * - 10: 5x2
 */

const BLOCK_COLORS = {
  1: '#FF4444',
  2: '#FF8C00',
  3: '#FFD700',
  4: '#32CD32',
  5: '#4488FF',
  6: '#9B59B6',
  7: '#FF69B4',
  8: '#A0522D',
  9: '#00CED1',
  10: '#FF6B6B',
};

function getArrangement(number) {
  // Returns array of rows (top to bottom), each row is number of blocks
  switch (number) {
    case 1: return [1];
    case 2: return [1, 1];
    case 3: return [1, 1, 1];
    case 4: return [2, 2];
    case 5: return [2, 3];
    case 6: return [2, 2, 2];
    case 7: return [3, 4];
    case 8: return [2, 2, 2, 2];
    case 9: return [3, 3, 3];
    case 10: return [2, 2, 2, 2, 2];
    default: return [1];
  }
}

export default function BlockCharacter({ number, size = 'medium' }) {
  const n = Math.min(Math.max(number, 1), 10);
  const color = BLOCK_COLORS[n] || BLOCK_COLORS[1];
  const arrangement = getArrangement(n);

  // Determine block size based on character size prop
  const blockSize = size === 'large' ? 22 : size === 'small' ? 12 : 16;
  const gap = 2;

  return (
    <View style={styles.container}>
      <View style={styles.blocksWrapper}>
        {arrangement.map((blocksInRow, rowIndex) => (
          <View key={rowIndex} style={styles.row}>
            {Array.from({ length: blocksInRow }).map((_, colIndex) => (
              <View
                key={colIndex}
                style={[
                  styles.block,
                  {
                    width: blockSize,
                    height: blockSize,
                    backgroundColor: color,
                    margin: gap / 2,
                    borderRadius: blockSize * 0.2,
                  },
                ]}
              >
                {/* Eyes on the top row blocks */}
                {rowIndex === 0 && (
                  <View style={styles.faceContainer}>
                    <View style={[styles.eye, { width: blockSize * 0.26, height: blockSize * 0.26 }]}>
                      <View style={[styles.pupil, { width: blockSize * 0.13, height: blockSize * 0.13 }]} />
                    </View>
                    <View style={{ width: blockSize * 0.1 }} />
                    <View style={[styles.eye, { width: blockSize * 0.26, height: blockSize * 0.26 }]}>
                      <View style={[styles.pupil, { width: blockSize * 0.13, height: blockSize * 0.13 }]} />
                    </View>
                  </View>
                )}
              </View>
            ))}
          </View>
        ))}
      </View>
      <Text style={[styles.numberLabel, { fontSize: blockSize * 1.1, color }]}>
        {number}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    marginHorizontal: 8,
  },
  blocksWrapper: {
    alignItems: 'center',
  },
  row: {
    flexDirection: 'row',
  },
  block: {
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: 'rgba(0,0,0,0.12)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.15,
    shadowRadius: 1,
    elevation: 2,
  },
  faceContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  eye: {
    backgroundColor: '#FFF',
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
  },
  pupil: {
    backgroundColor: '#333',
    borderRadius: 50,
  },
  numberLabel: {
    fontWeight: 'bold',
    marginTop: 3,
  },
});
