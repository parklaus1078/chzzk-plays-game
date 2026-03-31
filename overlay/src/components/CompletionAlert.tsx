import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";
import type { QueueItem } from "@/types/queue";

interface CompletionAlertProps {
  completedItem: QueueItem | null;
}

export function CompletionAlert({ completedItem }: CompletionAlertProps) {
  const [currentItem, setCurrentItem] = useState<QueueItem | null>(null);

  useEffect(() => {
    if (completedItem) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setCurrentItem(completedItem);
      const timer = setTimeout(() => setCurrentItem(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [completedItem]);

  if (!currentItem) return null;

  const isSuccess = currentItem.state === "done";
  const bgColor = isSuccess ? "bg-success/90" : "bg-error/90";
  const borderColor = isSuccess ? "border-success" : "border-error";
  const icon = isSuccess ? "✅" : "❌";
  const title = isSuccess ? "완료" : "실패";

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className={`fixed top-4 left-1/2 -translate-x-1/2 ${bgColor} backdrop-blur-md p-4 rounded-lg border-2 ${borderColor} max-w-md`}
      >
        <div className="text-text-primary font-bold text-lg mb-1">
          {icon} {title}
        </div>
        <div className="text-text-primary text-sm">
          <p><strong>{currentItem.donorName}</strong></p>
          <p className="text-text-secondary truncate">{currentItem.prompt}</p>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
