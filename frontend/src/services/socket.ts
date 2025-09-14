import { SocketEvents } from '../types/api';

type WebSocketMessage = {
  type: string;
  data: any;
};

class SocketService {
  private socket: WebSocket | null = null;
  private sessionId: string | null = null;
  private messageHandlers: Map<string, ((data: any) => void)[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(sessionId?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      // Generate a temporary connection ID if not provided
      const connectionId = sessionId || this.generateTempSessionId();
      this.sessionId = connectionId;

      const wsUrl = import.meta.env.VITE_SOCKET_URL || 'ws://localhost:8000';
      const url = `${wsUrl}/ws/${connectionId}`;
      
      console.log('🔌 Frontend: Connecting to WebSocket:', url);
      
      this.socket = new WebSocket(url);

      this.socket.onopen = () => {
        console.log('✅ Frontend: WebSocket connected');
        this.reconnectAttempts = 0;
        resolve();
      };

      this.socket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('📨 Frontend: Received message:', message);
          this.handleMessage(message);
        } catch (error) {
          console.error('❌ Frontend: Failed to parse WebSocket message:', error);
        }
      };

      this.socket.onclose = (event) => {
        console.log('🔌 Frontend: WebSocket closed:', event.code, event.reason);
        this.socket = null;
        
        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.attemptReconnect();
        }
      };

      this.socket.onerror = (error) => {
        console.error('❌ Frontend: WebSocket error:', error);
        reject(error);
      };
    });
  }

  private generateTempSessionId(): string {
    return 'temp_' + Math.random().toString(36).substr(2, 9);
  }

  private attemptReconnect(): void {
    this.reconnectAttempts++;
    console.log(`🔄 Frontend: Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      if (this.sessionId) {
        this.connect(this.sessionId).catch(() => {
          console.error('❌ Frontend: Reconnection failed');
        });
      }
    }, this.reconnectDelay * this.reconnectAttempts);
  }

  disconnect(): void {
    if (this.socket) {
      console.log('🔌 Frontend: Disconnecting WebSocket');
      this.socket.close(1000, 'Client disconnect');
      this.socket = null;
    }
    this.messageHandlers.clear();
  }

  private sendMessage(message: WebSocketMessage): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      console.log('📡 Frontend: Sending message:', message);
      this.socket.send(JSON.stringify(message));
    } else {
      console.error('❌ Frontend: WebSocket not connected, cannot send message:', message);
    }
  }

  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => handler(message.data));
    }
  }

  on<K extends keyof SocketEvents>(
    event: K,
    callback: (data: SocketEvents[K]) => void
  ): void {
    if (!this.messageHandlers.has(event)) {
      this.messageHandlers.set(event, []);
    }
    this.messageHandlers.get(event)!.push(callback);
  }

  off(event: string, callback?: (data: any) => void): void {
    if (callback) {
      const handlers = this.messageHandlers.get(event);
      if (handlers) {
        const index = handlers.indexOf(callback);
        if (index > -1) {
          handlers.splice(index, 1);
        }
      }
    } else {
      this.messageHandlers.delete(event);
    }
  }

  startSession(candidateName: string): void {
    console.log('🚀 Frontend: Starting session with name:', candidateName);
    this.sendMessage({
      type: 'start_session',
      data: { candidate_name: candidateName }
    });
  }

  sendUserMessage(sessionId: string, message: string): void {
    console.log('📤 Frontend: Sending message:', { sessionId, message });
    this.sendMessage({
      type: 'user_message',
      data: { session_id: sessionId, message }
    });
  }

  ping(): void {
    this.sendMessage({
      type: 'ping',
      data: {}
    });
  }

  getSessionId(): string | null {
    return this.sessionId;
  }

  isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }
}

export const socketService = new SocketService();
