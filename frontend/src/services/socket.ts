import { io, Socket } from 'socket.io-client';
import { SocketEvents } from '../types/api';

class SocketService {
  private socket: Socket | null = null;

  connect(): Socket {
    if (!this.socket) {
      this.socket = io(import.meta.env.VITE_SOCKET_URL || 'http://localhost:8000', {
        transports: ['polling', 'websocket'],
        upgrade: true,
        rememberUpgrade: true,
        timeout: 20000,
        forceNew: true
      });
    }
    return this.socket;
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  emit(event: string, data: any): void {
    console.log('📡 Frontend: Emitting event:', event, 'with data:', data);
    if (this.socket) {
      this.socket.emit(event, data);
    } else {
      console.error('❌ Frontend: Socket not connected, cannot emit event:', event);
    }
  }

  on<K extends keyof SocketEvents>(
    event: K,
    callback: (data: SocketEvents[K]) => void
  ): void {
    if (this.socket) {
      this.socket.on(event as string, callback as (...args: any[]) => void);
    }
  }

  off(event: string, callback?: (...args: any[]) => void): void {
    if (this.socket) {
      this.socket.off(event, callback);
    }
  }

  startSession(candidateName: string): void {
    console.log('🚀 Frontend: Starting session with name:', candidateName);
    this.emit('start_session', { candidate_name: candidateName });
  }

  sendMessage(sessionId: string, message: string): void {
    console.log('📤 Frontend: Sending message:', { sessionId, message });
    this.emit('user_message', { session_id: sessionId, message });
  }
}

export const socketService = new SocketService();
