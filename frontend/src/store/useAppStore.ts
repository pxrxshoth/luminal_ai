import { create } from 'zustand';

interface GraphNode {
  id: string;
  name: string;
  labels: string[];
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  isStreaming: boolean;
}

interface AppState {
  messages: Message[];
  graphData: GraphData;
  activeTopic: string;
  addMessage: (message: Message) => void;
  updateLastMessage: (contentChunk: string, isStreaming: boolean) => void;
  setGraphData: (data: GraphData) => void;
  setActiveTopic: (topic: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  messages: [],
  graphData: { nodes: [], edges: [] },
  activeTopic: '',
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  updateLastMessage: (contentChunk, isStreaming) => set((state) => {
    const newMessages = [...state.messages];
    if (newMessages.length > 0) {
      const lastMsg = newMessages[newMessages.length - 1];
      if (lastMsg.role === 'assistant') {
        lastMsg.content += contentChunk;
        lastMsg.isStreaming = isStreaming;
      }
    }
    return { messages: newMessages };
  }),
  setGraphData: (data) => set({ graphData: data }),
  setActiveTopic: (topic) => set({ activeTopic: topic }),
}));
