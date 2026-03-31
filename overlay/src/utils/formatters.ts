/**
 * Format elapsed time in seconds to MM:SS format
 */
export function formatElapsedTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Format Korean won currency
 */
export function formatCurrency(amount: number): string {
  return `${amount.toLocaleString('ko-KR')}원`;
}

/**
 * Truncate text to max length with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

/**
 * Get tier display name in Korean
 */
export function getTierName(tier: string): string {
  const tierNames: Record<string, string> = {
    one_line: '한 줄',
    feature: '기능',
    major: '대규모',
    chaos: '카오스',
  };
  return tierNames[tier] || tier;
}
