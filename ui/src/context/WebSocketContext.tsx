import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuth } from '../providers/AuthProvider';
import toast from 'react-hot-toast';

interface WebSocketContextType {
  isConnected: boolean;
  sendMessage: (message: any) => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    // Skip WebSocket connection if not enabled or not authenticated
    if (!import.meta.env.VITE_ENABLE_WEBSOCKET || !isAuthenticated) {
      return;
    }

    if (socket) {
      socket.close();
      setSocket(null);
    }

    const wsUrl = import.meta.env.VITE_WS_URL;
    const token = localStorage.getItem('token');

    if (!token || !wsUrl) {
      console.warn('WebSocket connection skipped: Missing token or WS URL');
      return;
    }

    try {
      // Use the system WebSocket endpoint for general updates
      const ws = new WebSocket(`${wsUrl.replace('http', 'ws')}/api/v1/ws/system?token=${token}`);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        // Attempt to reconnect after 5 seconds
        setTimeout(() => {
          if (isAuthenticated) {
            setSocket(null);
          }
        }, 5000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
        toast.error('Failed to connect to real-time updates');
      };

      setSocket(ws);

      return () => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      toast.error('Failed to initialize real-time updates');
    }
  }, [isAuthenticated]);

  const sendMessage = (message: any) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
      toast.error('Real-time updates are currently unavailable');
    }
  };

  return (
    <WebSocketContext.Provider value={{ isConnected, sendMessage }}>
      {children}
    </WebSocketContext.Provider>
  );
};
