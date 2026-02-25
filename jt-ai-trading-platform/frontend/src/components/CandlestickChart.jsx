import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

const CandlestickChart = ({ ticker, data }) => {
  const chartContainerRef = useRef();

  useEffect(() => {
    if (!data || data.length === 0) return;

    const chart = createChart(chartContainerRef.current, {
      layout: { backgroundColor: 'transparent', textColor: '#64748b' },
      grid: { vertLines: { color: '#1e293b' }, horzLines: { color: '#1e293b' } },
      crosshair: { mode: 0 },
      width: chartContainerRef.current.clientWidth,
      height: 300,
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#22c55e', downColor: '#ef4444', borderVisible: false,
      wickUpColor: '#22c55e', wickDownColor: '#ef4444',
    });

    // Format data for lightweight-charts
    const formattedData = data.map(item => ({
      time: item.date.split(' ')[0], // Get YYYY-MM-DD
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
    })).sort((a, b) => new Date(a.time) - new Date(b.time));

    candlestickSeries.setData(formattedData);
    chart.timeScale().fitContent();

    const handleResize = () => {
      chart.applyOptions({ width: chartContainerRef.current.clientWidth });
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data]);

  return (
    <div className="w-full bg-slate-900/50 rounded-2xl border border-white/5 p-4">
      <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4">Live Price Action: {ticker}</div>
      <div ref={chartContainerRef} className="w-full" />
    </div>
  );
};

export default CandlestickChart;
