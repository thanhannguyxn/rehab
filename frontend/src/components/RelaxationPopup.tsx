import { useEffect, useState, useRef } from 'react';
import { voiceService, VoiceMessages } from '../utils/voiceService';

interface RelaxationPopupProps {
  isOpen: boolean;
  onClose: () => void;
  duration?: number; // seconds
}

export const RelaxationPopup = ({ isOpen, onClose, duration = 180 }: RelaxationPopupProps) => {
  const [timeRemaining, setTimeRemaining] = useState(duration);
  const [isPlaying, setIsPlaying] = useState(true);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeRemaining(duration);
      setIsPlaying(true);

      // Voice: Start relaxation
      setTimeout(() => {
        voiceService.speak(VoiceMessages.relaxation.start, true);
      }, 500);

      // Play relaxation music
      if (audioRef.current) {
        audioRef.current.play().catch(err => console.log('Audio play failed:', err));
      }
    } else {
      // Stop music when closed
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
    }
  }, [isOpen, duration]);

  useEffect(() => {
    if (!isOpen || timeRemaining <= 0) return;

    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          // Voice: Relaxation complete
          voiceService.speak(VoiceMessages.relaxation.complete, true);
          // Auto close when time's up
          setTimeout(() => onClose(), 2000);
          return 0;
        }
        
        // Voice warnings at specific times
        if (prev === 90) {
          voiceService.addToQueue(VoiceMessages.relaxation.halfway);
        } else if (prev === 30) {
          voiceService.addToQueue(VoiceMessages.relaxation.almostDone);
        }
        
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isOpen, timeRemaining, onClose]);

  const toggleMusic = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const skipRelaxation = () => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    onClose();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = ((duration - timeRemaining) / duration) * 100;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-white/95 dark:bg-black/95 backdrop-blur-md flex items-center justify-center z-50 overflow-hidden animate-fadeIn">
      <div className="relative bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-2xl max-w-4xl w-full mx-4 p-6 animate-scaleIn">
        {/* Header */}
        <div className="text-center mb-6">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Nghỉ Thư Giãn
          </h2>
          <p className="text-base text-gray-600 dark:text-gray-400">
            Hãy thả lỏng cơ thể và hít thở sâu
          </p>
        </div>

        {/* Main Content - Horizontal Layout */}
        <div className="flex items-center gap-8 mb-6">
          {/* Left: Timer Display */}
          <div className="flex-shrink-0">
            <div className="relative w-48 h-48 flex items-center justify-center">
              {/* Circular progress - Smaller size */}
              <svg className="absolute w-48 h-48 transform -rotate-90">
                <circle
                  cx="96"
                  cy="96"
                  r="88"
                  stroke="currentColor"
                  className="text-gray-200 dark:text-gray-800"
                  strokeWidth="8"
                  fill="none"
                />
                <circle
                  cx="96"
                  cy="96"
                  r="88"
                  stroke="currentColor"
                  className="text-teal-500 dark:text-cyan-500 transition-all duration-1000"
                  strokeWidth="8"
                  fill="none"
                  strokeDasharray={`${2 * Math.PI * 88}`}
                  strokeDashoffset={`${2 * Math.PI * 88 * (1 - progress / 100)}`}
                  strokeLinecap="round"
                />
              </svg>
              
              {/* Time in center */}
              <div className="flex flex-col items-center justify-center z-10">
                <div className="text-5xl font-bold text-gray-900 dark:text-white">
                  {formatTime(timeRemaining)}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400 mt-1 font-medium">còn lại</div>
              </div>
            </div>
          </div>

          {/* Right: Breathing Animation and Tips */}
          <div className="flex-1 space-y-6">
            {/* Breathing Animation */}
            <div className="flex items-center gap-6">
              {/* Breathing bubble - smaller */}
              <div className="relative w-24 h-24 flex-shrink-0">
                <div className="absolute inset-0 bg-teal-500/50 dark:bg-cyan-500/50 rounded-full animate-breatheBubble shadow-xl blur-sm"></div>
                <div className="absolute inset-2 bg-teal-400/70 dark:bg-cyan-400/70 rounded-full animate-breatheBubble shadow-lg" style={{ animationDelay: '0.15s' }}></div>
                <div className="absolute inset-4 bg-teal-300/80 dark:bg-cyan-300/80 rounded-full animate-breatheBubble" style={{ animationDelay: '0.3s' }}></div>
                <div className="absolute inset-6 bg-white/90 dark:bg-gray-800/90 rounded-full animate-breatheBubble" style={{ animationDelay: '0.45s' }}></div>
              </div>
              
              {/* Breathing instruction */}
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-teal-500 dark:bg-cyan-500 rounded-full animate-breatheText"></div>
                  <span className="text-gray-900 dark:text-white text-lg font-light tracking-wide animate-breatheText">
                    Hít vào
                  </span>
                  <span className="text-gray-400">•</span>
                  <span className="text-gray-900 dark:text-white text-lg font-light tracking-wide animate-breatheText">
                    Thở ra
                  </span>
                  <div className="w-1.5 h-1.5 bg-teal-500 dark:bg-cyan-500 rounded-full animate-breatheText"></div>
                </div>
                <div className="text-gray-600 dark:text-gray-400 text-xs font-light tracking-widest uppercase">
                  Đều đặn và chậm rãi
                </div>
              </div>
            </div>

            {/* Relaxation Tips */}
            <div className="bg-gray-100 dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
              <h3 className="text-gray-900 dark:text-white font-semibold text-base mb-2">
                Hướng dẫn thư giãn:
              </h3>
              <ul className="space-y-1.5 text-sm text-gray-700 dark:text-gray-300">
                <li className="flex items-start gap-2">
                  <span className="text-teal-500 dark:text-cyan-500">•</span>
                  <span>Ngồi hoặc nằm ở tư thế thoải mái</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-teal-500 dark:text-cyan-500">•</span>
                  <span>Hít thở sâu và đều đặn</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-teal-500 dark:text-cyan-500">•</span>
                  <span>Thả lỏng tất cả các cơ trong cơ thể</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-teal-500 dark:text-cyan-500">•</span>
                  <span>Đóng mắt và tập trung vào hơi thở</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex gap-3">
          <button
            onClick={toggleMusic}
            className="flex-1 bg-gray-200 dark:bg-gray-800 hover:bg-gray-300 dark:hover:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white font-semibold py-3 px-4 rounded-xl transition flex items-center justify-center gap-2"
          >
            {isPlaying ? 'Tắt Nhạc' : 'Bật Nhạc'}
          </button>
          
          <button
            onClick={skipRelaxation}
            className="flex-1 bg-teal-500 dark:bg-cyan-500 hover:bg-teal-600 dark:hover:bg-cyan-600 text-white font-bold py-3 px-4 rounded-xl transition shadow-lg flex items-center justify-center gap-2"
          >
            Bỏ Qua
          </button>
        </div>

        {/* Audio Element */}
        <audio
          ref={audioRef}
          loop
          preload="auto"
        >
          {/* Using local relaxation music from backend */}
          <source src="http://localhost:8000/static/music_relax.mp3" type="audio/mpeg" />
        </audio>
      </div>

      {/* Custom animations */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        @keyframes scaleIn {
          from { 
            opacity: 0;
            transform: scale(0.9);
          }
          to { 
            opacity: 1;
            transform: scale(1);
          }
        }
        
        @keyframes breatheBubble {
          0%, 100% { 
            transform: scale(0.8);
            opacity: 0.6;
          }
          50% { 
            transform: scale(1.2);
            opacity: 1;
          }
        }
        
        @keyframes breatheText {
          0%, 100% { 
            opacity: 0.7;
          }
          50% { 
            opacity: 1;
          }
        }
        
        .animate-fadeIn {
          animation: fadeIn 0.5s ease-out;
        }
        
        .animate-scaleIn {
          animation: scaleIn 0.5s ease-out;
        }
        
        .animate-breatheBubble {
          animation: breatheBubble 4s ease-in-out infinite;
        }
        
        .animate-breatheText {
          animation: breatheText 4s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
};
