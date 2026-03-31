import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";
import type { BanEvent } from "@/types/queue";

interface BanAlertProps {
  banEvent: BanEvent | null;
}

export function BanAlert({ banEvent }: BanAlertProps) {
  const [currentBan, setCurrentBan] = useState<BanEvent | null>(null);

  useEffect(() => {
    if (banEvent) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setCurrentBan(banEvent);
      const timer = setTimeout(() => setCurrentBan(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [banEvent]);

  return (
    <AnimatePresence>
      {currentBan && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          className="fixed top-4 right-4 bg-error/90 backdrop-blur-md p-4 rounded-lg border-2 border-error max-w-sm"
        >
          <div className="text-text-primary font-bold text-lg mb-1">⛔ 사용자 차단</div>
          <div className="text-text-primary text-sm">
            <p><strong>{currentBan.donorName}</strong></p>
            <p className="text-text-secondary">사유: {currentBan.reason}</p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
