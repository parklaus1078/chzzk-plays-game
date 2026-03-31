import { AnimatePresence } from "framer-motion";
import type { QueueState } from "@/types/queue";
import { CurrentPrompt } from "./CurrentPrompt";
import { QueueItem } from "./QueueItem";

interface QueueDisplayProps {
  state: QueueState;
}

export function QueueDisplay({ state }: QueueDisplayProps) {
  const pendingItems = state.pending.slice(0, 8);

  return (
    <div className="w-full max-w-2xl mx-auto p-4 space-y-4">
      {/* Current Prompt */}
      {state.current && (
        <div>
          <h2 className="text-text-secondary text-sm font-semibold mb-2 uppercase tracking-wide">
            현재 실행 중
          </h2>
          <CurrentPrompt item={state.current} />
        </div>
      )}

      {/* Pending Queue */}
      {pendingItems.length > 0 && (
        <div>
          <h2 className="text-text-secondary text-sm font-semibold mb-2 uppercase tracking-wide">
            대기열 ({pendingItems.length})
          </h2>
          <div className="space-y-2">
            <AnimatePresence mode="popLayout">
              {pendingItems.map((item) => (
                <QueueItem key={item.id} item={item} />
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!state.current && pendingItems.length === 0 && (
        <div className="bg-surface/50 backdrop-blur-sm p-8 rounded-lg border border-border text-center">
          <p className="text-text-secondary text-lg">대기 중인 프롬프트가 없습니다</p>
          <p className="text-text-secondary text-sm mt-2">후원으로 프롬프트를 보내주세요!</p>
        </div>
      )}
    </div>
  );
}
