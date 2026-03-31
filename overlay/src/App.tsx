import { useQueueWebSocket } from "./hooks/useWebSocket";
import { QueueDisplay } from "./components/QueueDisplay";
import { BanAlert } from "./components/BanAlert";
import { CompletionAlert } from "./components/CompletionAlert";

function App() {
  const state = useQueueWebSocket("ws://localhost:8000/ws/queue");

  return (
    <>
      <QueueDisplay state={state} />
      <BanAlert banEvent={state.recentBan} />
      <CompletionAlert completedItem={state.recentCompleted} />
    </>
  );
}

export default App;
