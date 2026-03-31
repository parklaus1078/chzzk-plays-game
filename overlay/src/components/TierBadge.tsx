import type { DonationTier } from "@/types/queue";
import { getTierName } from "@/utils/formatters";

interface TierBadgeProps {
  tier: DonationTier;
}

export function TierBadge({ tier }: TierBadgeProps) {
  const tierStyles: Record<DonationTier, string> = {
    one_line: "bg-tier-oneline text-text-primary",
    feature: "bg-tier-feature text-text-primary",
    major: "bg-tier-major text-text-primary",
    chaos: "bg-tier-chaos text-black",
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-bold ${tierStyles[tier]}`}>
      {getTierName(tier)}
    </span>
  );
}
