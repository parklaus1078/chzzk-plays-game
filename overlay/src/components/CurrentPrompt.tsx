import { motion } from "framer-motion";
import type { QueueItem } from "@/types/queue";
import { TierBadge } from "./TierBadge";
import { formatElapsedTime } from "@/utils/formatters";

interface CurrentPromptProps {
  item: QueueItem;
}

export function CurrentPrompt({ item }: CurrentPromptProps) {
  const isRunning = item.state === "running";

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-surface-highlight p-4 rounded-lg backdrop-blur-md border-2 ${
        isRunning ? "border-tier-feature animate-pulse" : "border-border"
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-text-primary font-bold text-lg">{item.donorName}</span>
          <TierBadge tier={item.tier} />
        </div>
        <span className="text-text-primary font-mono text-lg">
          {formatElapsedTime(item.elapsedSeconds)}
        </span>
      </div>
      <p className="text-text-primary text-base truncate">{item.prompt}</p>
      <div className="mt-2 text-text-secondary text-sm">
        상태: {item.state}
      </div>
    </motion.div>
  );
}
