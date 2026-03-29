import { act, renderHook } from '@testing-library/react';
import { vi } from 'vitest';

import { useWebSocket } from '../hooks/useWebSocket';

class MockWebSocket {
  static OPEN = 1;
  readyState = MockWebSocket.OPEN;
  send = vi.fn();
  close = vi.fn();
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: ((error: Event) => void) | null = null;
  onclose: (() => void) | null = null;

  constructor(public url: string) {}
}

describe('useWebSocket', () => {
  it('connects, sends thresholds, parses analysis, and can send frame/reset', async () => {
    const instances: MockWebSocket[] = [];
    const wsCtor = vi.fn((url: string) => {
      const ws = new MockWebSocket(url);
      instances.push(ws);
      return ws;
    });
    Object.assign(wsCtor, { OPEN: 1 });
    vi.stubGlobal('WebSocket', wsCtor as unknown as typeof WebSocket);

    const { result } = renderHook(() =>
      useWebSocket('squat', true, { down_angle: 90, up_angle: 160 }, 123)
    );

    expect(instances).toHaveLength(1);
    expect(instances[0].url).toContain('/ws/exercise/squat?session_id=123');

    act(() => {
      instances[0].onopen?.();
    });

    expect(result.current.isConnected).toBe(true);
    expect(instances[0].send).toHaveBeenCalledWith(
      JSON.stringify({
        type: 'set_thresholds',
        thresholds: { down_angle: 90, up_angle: 160 },
      })
    );

    act(() => {
      instances[0].onmessage?.({
        data: JSON.stringify({ type: 'analysis', pose_detected: true, rep_count: 3 }),
      });
    });
    expect(result.current.analysisData?.rep_count).toBe(3);

    act(() => {
      result.current.sendFrame('base64-frame');
      result.current.resetCounter();
    });

    expect(instances[0].send).toHaveBeenCalledWith(
      JSON.stringify({ type: 'frame', data: 'base64-frame' })
    );
    expect(instances[0].send).toHaveBeenCalledWith(JSON.stringify({ type: 'reset' }));
  });

  it('disconnects when inactive', () => {
    const ws = new MockWebSocket('ws://example');
    const wsCtor = vi.fn(() => ws);
    Object.assign(wsCtor, { OPEN: 1 });
    vi.stubGlobal('WebSocket', wsCtor as unknown as typeof WebSocket);

    const { rerender } = renderHook(
      ({ active }) => useWebSocket('squat', active, undefined, 1),
      { initialProps: { active: true } }
    );

    act(() => {
      ws.onopen?.();
    });

    rerender({ active: false });
    expect(ws.close).toHaveBeenCalled();
  });
});

