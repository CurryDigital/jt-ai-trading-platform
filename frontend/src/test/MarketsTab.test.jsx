import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MarketsTab } from '../components/MarketsTab';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('MarketsTab HK/CN data serialization', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  const mockOkResponse = (data) =>
    Promise.resolve({ ok: true, json: () => Promise.resolve(data) });

  it('renders HK F&G Index and Adv/Dec from API response', async () => {
    // Setup mock responses for all endpoints
    mockFetch.mockImplementation((url) => {
      if (url.includes('/api/market/indices')) return mockOkResponse({ data: [] });
      if (url.includes('/api/market/movers')) return mockOkResponse({ gainers: [], losers: [] });
      if (url.includes('/api/market/sectors')) return mockOkResponse({ data: [] });
      if (url.includes('/api/market/volume-leaders')) return mockOkResponse({ data: [] });
      if (url.includes('/api/market/global')) return mockOkResponse({ data: [] });
      if (url.includes('/api/market/breadth?country=US'))
        return mockOkResponse({ advancing: 1200, declining: 800, unchanged: 100, newHighs: 50, newLows: 20 });
      if (url.includes('/api/market/breadth?country=HK'))
        return mockOkResponse({ advancing: 450, declining: 320, unchanged: 30, newHighs: 12, newLows: 8 });
      if (url.includes('/api/market/breadth?country=CN'))
        return mockOkResponse({ advancing: 2100, declining: 1800, unchanged: 200, newHighs: 80, newLows: 45 });
      if (url.includes('/api/market/sentiment?country=US'))
        return mockOkResponse({ fearGreed: 55, vix: 18.5, putCall: 1.0 });
      if (url.includes('/api/market/sentiment?country=HK'))
        return mockOkResponse({ fearGreed: 62, vix: null, putCall: 1.0 });
      if (url.includes('/api/market/sentiment?country=CN'))
        return mockOkResponse({ fearGreed: 48, vix: null, putCall: 1.0 });
      return Promise.resolve({ ok: false });
    });

    render(<MarketsTab />);

    // Wait for HK F&G Index to appear
    await waitFor(() => {
      const hkCards = screen.getAllByText('HK');
      expect(hkCards.length).toBeGreaterThan(0);
    });

    // Verify HK F&G Index value (62) is rendered, not "--"
    expect(screen.getAllByText('62').length).toBeGreaterThan(0);

    // Verify CN F&G Index value (48) is rendered, not "--"
    expect(screen.getAllByText('48').length).toBeGreaterThan(0);

    // Verify HK Adv/Dec ratio is rendered
    expect(screen.getAllByText('450/320').length).toBeGreaterThan(0);

    // Verify CN Adv/Dec ratio is rendered
    expect(screen.getAllByText('2100/1800').length).toBeGreaterThan(0);

    // Ensure "--" does NOT appear in the component
    expect(screen.queryByText('--')).not.toBeInTheDocument();
  });

  it('falls back to default values when HK/CN APIs return empty', async () => {
    mockFetch.mockImplementation((url) => {
      if (url.includes('/api/market/indices')) return mockOkResponse({ data: [] });
      if (url.includes('/api/market/movers')) return mockOkResponse({ gainers: [], losers: [] });
      if (url.includes('/api/market/sectors')) return mockOkResponse({ data: [] });
      if (url.includes('/api/market/volume-leaders')) return mockOkResponse({ data: [] });
      if (url.includes('/api/market/global')) return mockOkResponse({ data: [] });
      if (url.includes('/api/market/breadth'))
        return mockOkResponse({ advancing: 0, declining: 0, unchanged: 0, newHighs: 0, newLows: 0 });
      if (url.includes('/api/market/sentiment'))
        return mockOkResponse({ fearGreed: 50, vix: null, putCall: 1.0 });
      return Promise.resolve({ ok: false });
    });

    render(<MarketsTab />);

    await waitFor(() => {
      expect(screen.getAllByText('HK').length).toBeGreaterThan(0);
    });

    // With empty API responses, default fearGreed=50 and 0/0 should render
    expect(screen.getAllByText('50').length).toBeGreaterThan(0);
    expect(screen.getAllByText('0/0').length).toBeGreaterThan(0);
  });

  it('sends correct country query params for HK and CN', async () => {
    mockFetch.mockImplementation((url) => {
      if (url.includes('/api/market/indices')) return mockOkResponse({ data: [] });
      if (url.includes('/api/market/movers')) return mockOkResponse({ gainers: [], losers: [] });
      if (url.includes('/api/market/sectors')) return mockOkResponse({ data: [] });
      if (url.includes('/api/market/volume-leaders')) return mockOkResponse({ data: [] });
      if (url.includes('/api/market/global')) return mockOkResponse({ data: [] });
      if (url.includes('/api/market/breadth')) return mockOkResponse({ advancing: 0, declining: 0, unchanged: 0, newHighs: 0, newLows: 0 });
      if (url.includes('/api/market/sentiment')) return mockOkResponse({ fearGreed: 50, vix: null, putCall: 1.0 });
      return Promise.resolve({ ok: false });
    });

    render(<MarketsTab />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/market/breadth?country=HK');
      expect(mockFetch).toHaveBeenCalledWith('/api/market/breadth?country=CN');
      expect(mockFetch).toHaveBeenCalledWith('/api/market/sentiment?country=HK');
      expect(mockFetch).toHaveBeenCalledWith('/api/market/sentiment?country=CN');
    });
  });
});
