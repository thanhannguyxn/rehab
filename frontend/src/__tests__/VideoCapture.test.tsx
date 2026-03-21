import { render, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

import { VideoCapture } from '../components/VideoCapture';

describe('VideoCapture', () => {
  const getUserMediaMock = vi.fn();
  const onFrame = vi.fn();
  const stopTrack = vi.fn();
  let rafCallback: FrameRequestCallback | undefined;

  beforeEach(() => {
    onFrame.mockReset();
    stopTrack.mockReset();
    getUserMediaMock.mockReset();
    rafCallback = undefined;

    Object.defineProperty(window, 'alert', {
      value: vi.fn(),
      writable: true,
    });

    Object.defineProperty(global.navigator, 'mediaDevices', {
      value: {
        getUserMedia: getUserMediaMock.mockResolvedValue({
          getTracks: () => [{ stop: stopTrack }],
        }),
      },
      configurable: true,
    });

    Object.defineProperty(window, 'requestAnimationFrame', {
      value: vi.fn((cb: FrameRequestCallback) => {
        rafCallback = cb;
        return 1;
      }),
      writable: true,
    });

    Object.defineProperty(window, 'cancelAnimationFrame', {
      value: vi.fn(),
      writable: true,
    });

    HTMLCanvasElement.prototype.getContext = vi.fn(
      () =>
        ({
          drawImage: vi.fn(),
          clearRect: vi.fn(),
          beginPath: vi.fn(),
          moveTo: vi.fn(),
          lineTo: vi.fn(),
          stroke: vi.fn(),
          arc: vi.fn(),
          fill: vi.fn(),
          shadowBlur: 0,
        }) as unknown as CanvasRenderingContext2D
    );
    HTMLCanvasElement.prototype.toDataURL = vi.fn(() => 'data:image/jpeg;base64,test-frame');
  });

  it('starts camera and emits frame while active', async () => {
    const { container } = render(
      <VideoCapture isActive onFrame={onFrame} feedback="Đang tập" landmarks={[]} />
    );

    await waitFor(() => {
      expect(getUserMediaMock).toHaveBeenCalled();
    });

    const video = container.querySelector('video') as HTMLVideoElement;
    Object.defineProperty(video, 'readyState', { value: 4, configurable: true });
    Object.defineProperty(video, 'videoWidth', { value: 640, configurable: true });
    Object.defineProperty(video, 'videoHeight', { value: 480, configurable: true });

    rafCallback?.(100);

    expect(onFrame).toHaveBeenCalledWith('data:image/jpeg;base64,test-frame');
  });

  it('renders provided feedback text', () => {
    const { getByText } = render(
      <VideoCapture isActive={false} onFrame={onFrame} feedback="Giữ thăng bằng" landmarks={[]} />
    );

    expect(getByText('Giữ thăng bằng')).toBeInTheDocument();
  });
});

