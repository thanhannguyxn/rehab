import { useState, useEffect, useCallback, useRef } from 'react';
import type { AnalysisResult } from '../types';
import { WS_BASE_URL } from '../utils/config';

interface CustomThresholds {
  down_angle?: number;
  up_angle?: number;
  max_reps?: number;
}

export const useWebSocket = (
  exerciseType: string,
  isActive: boolean,
  customThresholds?: CustomThresholds,
  sessionId?: number | null
) => {
  const [isConnected, setIsConnected] = useState(false);
  const [analysisData, setAnalysisData] = useState<AnalysisResult | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Store customThresholds in ref to avoid reconnection
  const customThresholdsRef = useRef(customThresholds);
  
  useEffect(() => {
    customThresholdsRef.current = customThresholds;
  }, [customThresholds]);

  const connect = useCallback(() => {
    if (!isActive || !sessionId || wsRef.current) return;

    const wsUrl = `${WS_BASE_URL}/ws/exercise/${exerciseType}?session_id=${sessionId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      
      // Send custom thresholds if available
      if (customThresholdsRef.current) {
        ws.send(JSON.stringify({
          type: 'set_thresholds',
          thresholds: customThresholdsRef.current
        }));
        console.log('Sent custom thresholds:', customThresholdsRef.current);
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'analysis') {
          setAnalysisData(data);
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      wsRef.current = null;
    };

    wsRef.current = ws;
  }, [exerciseType, isActive, sessionId]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
      setIsConnected(false);
    }
  }, []);

  const sendFrame = useCallback((frameData: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'frame',
          data: frameData,
        })
      );
    }
  }, []);

  const resetCounter = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'reset',
        })
      );
    }
  }, []);

  useEffect(() => {
    if (isActive) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [isActive, connect, disconnect]); // Removed customThresholds from dependencies

  return {
    isConnected,
    analysisData,
    sendFrame,
    resetCounter,
  };
};
