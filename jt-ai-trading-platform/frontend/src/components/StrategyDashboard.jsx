import React from 'react';
import { GoldenStrategies } from './GoldenStrategies';

/**
 * Strategy Dashboard - Simplified to show only 5 Golden Strategies
 */
export const StrategyDashboard = ({ onCreateStrategy }) => {
  return (
    <div className="strategy-dashboard min-h-screen">
      <GoldenStrategies onDeployStrategy={onCreateStrategy} />
    </div>
  );
};

export default StrategyDashboard;
