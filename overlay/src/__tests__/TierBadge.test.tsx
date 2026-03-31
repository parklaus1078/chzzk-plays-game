import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TierBadge } from '@/components/TierBadge';
import type { DonationTier } from '@/types/queue';

describe('TierBadge', () => {
  it('renders correct text for one_line tier', () => {
    render(<TierBadge tier="one_line" />);
    expect(screen.getByText('한 줄')).toBeInTheDocument();
  });

  it('renders correct text for feature tier', () => {
    render(<TierBadge tier="feature" />);
    expect(screen.getByText('기능')).toBeInTheDocument();
  });

  it('renders correct text for major tier', () => {
    render(<TierBadge tier="major" />);
    expect(screen.getByText('대규모')).toBeInTheDocument();
  });

  it('renders correct text for chaos tier', () => {
    render(<TierBadge tier="chaos" />);
    expect(screen.getByText('카오스')).toBeInTheDocument();
  });

  it('renders correct color for one_line tier', () => {
    const { container } = render(<TierBadge tier="one_line" />);
    const badge = container.querySelector('span');
    expect(badge?.className).toContain('bg-tier-oneline');
  });

  it('renders correct color for feature tier', () => {
    const { container } = render(<TierBadge tier="feature" />);
    const badge = container.querySelector('span');
    expect(badge?.className).toContain('bg-tier-feature');
  });

  it('renders correct color for major tier', () => {
    const { container } = render(<TierBadge tier="major" />);
    const badge = container.querySelector('span');
    expect(badge?.className).toContain('bg-tier-major');
  });

  it('renders correct color for chaos tier', () => {
    const { container } = render(<TierBadge tier="chaos" />);
    const badge = container.querySelector('span');
    expect(badge?.className).toContain('bg-tier-chaos');
  });

  it('applies black text for chaos tier', () => {
    const { container } = render(<TierBadge tier="chaos" />);
    const badge = container.querySelector('span');
    expect(badge?.className).toContain('text-black');
  });

  it('applies primary text color for non-chaos tiers', () => {
    const tiers: DonationTier[] = ['one_line', 'feature', 'major'];

    tiers.forEach(tier => {
      const { container } = render(<TierBadge tier={tier} />);
      const badge = container.querySelector('span');
      expect(badge?.className).toContain('text-text-primary');
    });
  });

  it('renders with correct badge styling', () => {
    const { container } = render(<TierBadge tier="feature" />);
    const badge = container.querySelector('span');

    // Check for badge styling classes
    expect(badge?.className).toContain('px-2');
    expect(badge?.className).toContain('py-1');
    expect(badge?.className).toContain('rounded-full');
    expect(badge?.className).toContain('text-xs');
    expect(badge?.className).toContain('font-bold');
  });
});
