export type DonationTier = "one_line" | "feature" | "major" | "chaos";
export type PromptState = "idle" | "filtering" | "queued" | "running" | "building" | "done" | "failed" | "rejected" | "timeout" | "reverting" | "reverted";

export interface QueueItem {
  id: string;
  donorName: string;
  donorId: string;
  prompt: string;
  tier: DonationTier;
  state: PromptState;
  createdAt: string;
  elapsedSeconds: number;
}

export interface BanEvent {
  userId: string;
  donorName: string;
  reason: string;
}

export interface QueueState {
  current: QueueItem | null;
  pending: QueueItem[];
  recentCompleted: QueueItem | null;
  recentBan: BanEvent | null;
}
