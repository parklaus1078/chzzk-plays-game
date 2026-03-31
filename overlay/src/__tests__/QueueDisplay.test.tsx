import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueueDisplay } from '@/components/QueueDisplay';
import type { QueueState, QueueItem } from '@/types/queue';

const createMockItem = (id: string, overrides?: Partial<QueueItem>): QueueItem => ({
  id,
  donorName: `Donor ${id}`,
  donorId: `user_${id}`,
  prompt: `Test prompt ${id}`,
  tier: 'one_line',
  state: 'queued',
  createdAt: new Date().toISOString(),
  elapsedSeconds: 0,
  ...overrides,
});

describe('QueueDisplay', () => {
  it('test_renders_current_prompt', () => {
    const state: QueueState = {
      current: createMockItem('1', { donorName: 'Alice', prompt: 'Add jump feature' }),
      pending: [],
      recentCompleted: null,
      recentBan: null,
    };

    render(<QueueDisplay state={state} />);

    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Add jump feature')).toBeInTheDocument();
    expect(screen.getByText('현재 실행 중')).toBeInTheDocument();
  });

  it('test_renders_pending_items', () => {
    const state: QueueState = {
      current: null,
      pending: [
        createMockItem('1', { donorName: 'Bob' }),
        createMockItem('2', { donorName: 'Charlie' }),
        createMockItem('3', { donorName: 'David' }),
      ],
      recentCompleted: null,
      recentBan: null,
    };

    render(<QueueDisplay state={state} />);

    expect(screen.getByText('Bob')).toBeInTheDocument();
    expect(screen.getByText('Charlie')).toBeInTheDocument();
    expect(screen.getByText('David')).toBeInTheDocument();
    expect(screen.getByText('대기열 (3)')).toBeInTheDocument();
  });

  it('test_limits_pending_to_8', () => {
    const pendingItems = Array.from({ length: 12 }, (_, i) =>
      createMockItem(`${i}`, { donorName: `User${i}` })
    );

    const state: QueueState = {
      current: null,
      pending: pendingItems,
      recentCompleted: null,
      recentBan: null,
    };

    render(<QueueDisplay state={state} />);

    // Should only render first 8 items
    expect(screen.getByText('대기열 (8)')).toBeInTheDocument();
    expect(screen.getByText('User0')).toBeInTheDocument();
    expect(screen.getByText('User7')).toBeInTheDocument();
    expect(screen.queryByText('User8')).not.toBeInTheDocument();
    expect(screen.queryByText('User11')).not.toBeInTheDocument();
  });

  it('test_tier_badge_colors', () => {
    const state: QueueState = {
      current: null,
      pending: [
        createMockItem('1', { tier: 'one_line', donorName: 'OneLine' }),
        createMockItem('2', { tier: 'feature', donorName: 'Feature' }),
        createMockItem('3', { tier: 'major', donorName: 'Major' }),
        createMockItem('4', { tier: 'chaos', donorName: 'Chaos' }),
      ],
      recentCompleted: null,
      recentBan: null,
    };

    const { container } = render(<QueueDisplay state={state} />);

    // Check that tier badges are rendered with tier names
    expect(screen.getByText('한 줄')).toBeInTheDocument();
    expect(screen.getByText('기능')).toBeInTheDocument();
    expect(screen.getByText('대규모')).toBeInTheDocument();
    expect(screen.getByText('카오스')).toBeInTheDocument();

    // Check that badges have the correct CSS classes
    const badges = container.querySelectorAll('span');
    const tierBadges = Array.from(badges).filter(badge =>
      badge.textContent && ['한 줄', '기능', '대규모', '카오스'].includes(badge.textContent)
    );

    expect(tierBadges.length).toBe(4);
    expect(tierBadges[0].className).toContain('bg-tier-oneline');
    expect(tierBadges[1].className).toContain('bg-tier-feature');
    expect(tierBadges[2].className).toContain('bg-tier-major');
    expect(tierBadges[3].className).toContain('bg-tier-chaos');
  });

  it('test_empty_state', () => {
    const state: QueueState = {
      current: null,
      pending: [],
      recentCompleted: null,
      recentBan: null,
    };

    render(<QueueDisplay state={state} />);

    expect(screen.getByText('대기 중인 프롬프트가 없습니다')).toBeInTheDocument();
    expect(screen.getByText('후원으로 프롬프트를 보내주세요!')).toBeInTheDocument();
  });

  it('test_prompt_text_truncated', () => {
    const longPrompt = 'This is a very long prompt that should be truncated because it exceeds the maximum allowed length for display in the UI and we want to make sure it does not overflow the container';

    const state: QueueState = {
      current: null,
      pending: [createMockItem('1', { prompt: longPrompt })],
      recentCompleted: null,
      recentBan: null,
    };

    const { container } = render(<QueueDisplay state={state} />);

    // The prompt text should have the 'truncate' class which handles overflow
    const promptElements = container.querySelectorAll('.truncate');
    const hasLongPrompt = Array.from(promptElements).some(
      el => el.textContent === longPrompt
    );

    expect(hasLongPrompt).toBe(true);

    // Verify that at least one element with truncate class exists
    expect(promptElements.length).toBeGreaterThan(0);
  });
});
