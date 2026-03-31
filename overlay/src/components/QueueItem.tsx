import { motion } from "framer-motion";
import type { QueueItem as QueueItemType } from "@/types/queue";
import { TierBadge } from "./TierBadge";

interface QueueItemProps {
  item: QueueItemType;
}

export function QueueItem({ item }: QueueItemProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 100 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -100 }}
      className="bg-surface p-3 rounded-lg backdrop-blur-sm border border-border"
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-text-primary font-medium truncate">{item.donorName}</span>
        <TierBadge tier={item.tier} />
      </div>
      <p className="text-text-secondary text-sm truncate">{item.prompt}</p>
    </motion.div>
  );
}
