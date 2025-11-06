import { useRef, useEffect } from 'react';
import type { Landmark } from '../types';

interface VideoCaptureProps {
  isActive: boolean;
  onFrame: (frameData: string) => void;
  landmarks?: Landmark[];
  feedback?: string;
}

export const VideoCapture = ({
  isActive,
  onFrame,
  landmarks,
  feedback,
}: VideoCaptureProps) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Start/stop camera based on isActive
  useEffect(() => {
    let mounted = true;

    const startCamera = async () => {
      try {
        if (!isActive) return;

        const stream = await navigator.mediaDevices.getUserMedia({
          video: { 
            width: 1280, 
            height: 720,
            frameRate: { ideal: 30 }
          },
        });
        
        // Check if component is still mounted
        if (!mounted) {
          stream.getTracks().forEach(track => track.stop());
          return;
        }
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          streamRef.current = stream;
        }
      } catch (err) {
        console.error('Error accessing camera:', err);
        alert('Không thể truy cập camera. Vui lòng cho phép quyền truy cập camera.');
      }
    };

    startCamera();

    return () => {
      mounted = false;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    };
  }, [isActive]);

  // Capture and send frames
  useEffect(() => {
    if (!isActive || !videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let frameId: number | null = null;
    let lastFrameTime = 0;
    const frameInterval = 1000 / 30; // 30 FPS

    const captureFrame = (timestamp: number) => {
      if (!isActive) return;

      if (timestamp - lastFrameTime >= frameInterval) {
        lastFrameTime = timestamp;

        if (video.readyState === video.HAVE_ENOUGH_DATA) {
          // Only resize canvas if dimensions have changed
          if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
          }
          
          // Draw video frame
          ctx.drawImage(video, 0, 0);

          // Only send frame if active
          if (isActive) {
            const frameData = canvas.toDataURL('image/jpeg', 0.8);
            onFrame(frameData);
          }
        }
      }

      frameId = requestAnimationFrame(captureFrame);
    };

    // Wait for video to be ready before starting capture
    const handleVideoReady = () => {
      frameId = requestAnimationFrame(captureFrame);
    };

    video.addEventListener('loadeddata', handleVideoReady);

    return () => {
      if (frameId !== null) {
        cancelAnimationFrame(frameId);
      }
      video.removeEventListener('loadeddata', handleVideoReady);
    };
  }, [isActive, onFrame]);

  // Draw skeleton
  useEffect(() => {
    if (!landmarks || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { width, height } = canvas;

    // Clear previous drawings
    ctx.clearRect(0, 0, width, height);

    // Draw connections
    const connections = [
      [11, 12], [11, 13], [13, 15], [12, 14], [14, 16], // Arms
      [11, 23], [12, 24], [23, 24], // Torso
      [23, 25], [25, 27], [27, 29], [29, 31], // Left leg
      [24, 26], [26, 28], [28, 30], [30, 32], // Right leg
    ];

    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 3;

    connections.forEach(([start, end]) => {
      const startLm = landmarks[start];
      const endLm = landmarks[end];
      
      if (startLm.visibility > 0.5 && endLm.visibility > 0.5) {
        ctx.beginPath();
        ctx.moveTo(startLm.x * width, startLm.y * height);
        ctx.lineTo(endLm.x * width, endLm.y * height);
        ctx.stroke();
      }
    });

    // Draw landmarks
    landmarks.forEach((lm) => {
      if (lm.visibility > 0.5) {
        ctx.fillStyle = '#ff0000';
        ctx.beginPath();
        ctx.arc(lm.x * width, lm.y * height, 5, 0, 2 * Math.PI);
        ctx.fill();
      }
    });
  }, [landmarks]);

  return (
    <div className="relative w-full max-w-4xl mx-auto">
      {/* Video element (hidden but needed for capture) */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="opacity-0 absolute"
      />
      
      {/* Canvas for skeleton overlay */}
      <canvas
        ref={canvasRef}
        className="w-full rounded-lg shadow-2xl border-4 border-blue-600"
      />

      {/* Feedback overlay */}
      <div className="absolute top-4 left-4 right-4">
        <div className="bg-black bg-opacity-70 text-white px-6 py-4 rounded-lg">
          <p className="text-2xl font-bold">{feedback || 'Sẵn sàng...'}</p>
        </div>
      </div>


    </div>
  );
};
