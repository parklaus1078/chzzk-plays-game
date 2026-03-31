import { describe, it, expect } from 'vitest';
import {
  formatElapsedTime,
  formatCurrency,
  truncateText,
  getTierName,
} from '@/utils/formatters';

describe('formatters', () => {
  describe('formatElapsedTime', () => {
    it('formats 0 seconds correctly', () => {
      expect(formatElapsedTime(0)).toBe('0:00');
    });

    it('formats seconds without minutes', () => {
      expect(formatElapsedTime(45)).toBe('0:45');
    });

    it('formats seconds with leading zero', () => {
      expect(formatElapsedTime(5)).toBe('0:05');
    });

    it('formats exactly 1 minute', () => {
      expect(formatElapsedTime(60)).toBe('1:00');
    });

    it('formats minutes and seconds', () => {
      expect(formatElapsedTime(125)).toBe('2:05');
    });

    it('formats double-digit minutes', () => {
      expect(formatElapsedTime(645)).toBe('10:45');
    });

    it('formats large time values', () => {
      expect(formatElapsedTime(3661)).toBe('61:01');
    });

    it('handles fractional seconds by flooring', () => {
      expect(formatElapsedTime(45.7)).toBe('0:45');
      expect(formatElapsedTime(125.9)).toBe('2:05');
    });
  });

  describe('formatCurrency', () => {
    it('formats small amounts', () => {
      expect(formatCurrency(1000)).toBe('1,000원');
    });

    it('formats feature tier amount', () => {
      expect(formatCurrency(5000)).toBe('5,000원');
    });

    it('formats major tier amount', () => {
      expect(formatCurrency(10000)).toBe('10,000원');
    });

    it('formats chaos tier amount', () => {
      expect(formatCurrency(30000)).toBe('30,000원');
    });

    it('formats large amounts with multiple commas', () => {
      expect(formatCurrency(1000000)).toBe('1,000,000원');
    });

    it('formats amounts without thousands separator', () => {
      expect(formatCurrency(500)).toBe('500원');
    });
  });

  describe('truncateText', () => {
    it('returns short text unchanged', () => {
      const text = 'Short text';
      expect(truncateText(text, 50)).toBe('Short text');
    });

    it('returns text at exact max length unchanged', () => {
      const text = 'Exactly ten';
      expect(truncateText(text, 11)).toBe('Exactly ten');
    });

    it('truncates long text with ellipsis', () => {
      const text = 'This is a very long text that needs truncation';
      const result = truncateText(text, 20);
      expect(result).toBe('This is a very long ...');
      expect(result.length).toBe(23); // 20 + 3 for '...'
    });

    it('truncates to very short length', () => {
      const text = 'Hello world';
      expect(truncateText(text, 5)).toBe('Hello...');
    });

    it('handles empty string', () => {
      expect(truncateText('', 10)).toBe('');
    });

    it('handles single character with length 1', () => {
      expect(truncateText('A', 1)).toBe('A');
    });

    it('truncates Korean text correctly', () => {
      const text = '한글로 작성된 매우 긴 텍스트입니다';
      const result = truncateText(text, 10);
      expect(result).toBe('한글로 작성된 매우...');
      expect(result.length).toBe(13);
    });
  });

  describe('getTierName', () => {
    it('returns Korean name for one_line tier', () => {
      expect(getTierName('one_line')).toBe('한 줄');
    });

    it('returns Korean name for feature tier', () => {
      expect(getTierName('feature')).toBe('기능');
    });

    it('returns Korean name for major tier', () => {
      expect(getTierName('major')).toBe('대규모');
    });

    it('returns Korean name for chaos tier', () => {
      expect(getTierName('chaos')).toBe('카오스');
    });

    it('returns input unchanged for unknown tier', () => {
      expect(getTierName('unknown_tier')).toBe('unknown_tier');
    });

    it('handles empty string', () => {
      expect(getTierName('')).toBe('');
    });
  });
});
